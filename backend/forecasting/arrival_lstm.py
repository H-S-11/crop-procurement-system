import os
import joblib
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from .sequence_builder import build_sequences, TimeSeriesDataset

class PaddyLSTM(nn.Module):
    def __init__(self, input_size, hidden_size=64, num_layers=2, dropout=0.2):
        super(PaddyLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout if num_layers > 1 else 0)
        self.fc1 = nn.Linear(hidden_size, 32)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(32, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :] # Take the last hidden state
        out = self.fc1(out)
        out = self.relu(out)
        out = self.fc2(out)
        return out.squeeze(1)

class LSTMForecaster:
    def __init__(self, lookback=14):
        self.lookback = lookback
        self.features = [
            'arrival_lag1', 'arrival_3d_mean', 'arrival_7d_mean', 'arrival_14d_mean',
            'arrival_volatility', 'rainfall_3d', 'rainfall_7d', 'rainfall_14d',
            'capacity', 'nearest_road_dist', 'flood_exposure'
        ]
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.scaler = StandardScaler()
        
    def prepare_data(self, df):
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        for col in self.features:
            if col not in df.columns:
                df[col] = 0.0
            else:
                df[col] = df[col].fillna(0.0)
        return df

    def train_and_evaluate(self, df):
        df = self.prepare_data(df)
        
        train_mask = (df['future_arrival_1d'].notna()) & (df['date'] <= '2026-03-31')
        valid_df = df[train_mask].copy()
        
        if len(valid_df) < 100:
            print("Insufficient data rows for LSTM arrival forecasting.")
            return None
            
        dates = sorted(valid_df['date'].unique())
        n_dates = len(dates)
        split1_date = dates[int(n_dates * 0.70)]
        split2_date = dates[int(n_dates * 0.85)]
        
        train = valid_df[valid_df['date'] <= split1_date].copy()
        val = valid_df[(valid_df['date'] > split1_date) & (valid_df['date'] <= split2_date)].copy()
        test = valid_df[valid_df['date'] > split2_date].copy()
        
        print(f"LSTM Split: Train ({train['date'].min().date()} to {train['date'].max().date()})")
        print(f"LSTM Split: Val ({val['date'].min().date()} to {val['date'].max().date()})")
        print(f"LSTM Split: Test ({test['date'].min().date()} to {test['date'].max().date()})")
        
        # Fit scaler ONLY on train data to prevent leakage
        self.scaler.fit(train[self.features])
        
        train[self.features] = self.scaler.transform(train[self.features])
        val[self.features] = self.scaler.transform(val[self.features])
        test[self.features] = self.scaler.transform(test[self.features])
        
        results = {}
        models_dir = os.path.join(os.path.dirname(__file__), '../models')
        os.makedirs(models_dir, exist_ok=True)
        
        # Save the scaler
        joblib.dump(self.scaler, os.path.join(models_dir, 'lstm_scaler.pkl'))
        
        horizons = [
            ('1d', 'future_arrival_1d'),
            ('3d', 'future_arrival_3d'),
            ('7d', 'future_arrival_7d'),
        ]
        
        for name, target_col in horizons:
            print(f"Training LSTM for horizon: {name}...")
            
            X_train, y_train = build_sequences(train, self.features, target_col, self.lookback)
            X_val, y_val = build_sequences(val, self.features, target_col, self.lookback)
            X_test, y_test = build_sequences(test, self.features, target_col, self.lookback)
            
            if len(X_train) == 0 or len(X_test) == 0:
                print(f"Not enough sequences built for horizon {name}.")
                continue
                
            train_loader = DataLoader(TimeSeriesDataset(X_train, y_train), batch_size=64, shuffle=True)
            val_loader = DataLoader(TimeSeriesDataset(X_val, y_val), batch_size=64, shuffle=False)
            
            model = PaddyLSTM(input_size=len(self.features)).to(self.device)
            criterion = nn.MSELoss()
            optimizer = optim.Adam(model.parameters(), lr=0.001)
            
            epochs = 50
            best_val_loss = float('inf')
            patience = 5
            patience_counter = 0
            
            # Set fixed seed
            torch.manual_seed(42)
            np.random.seed(42)
            
            for epoch in range(epochs):
                model.train()
                train_loss = 0
                for batch_x, batch_y in train_loader:
                    batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                    optimizer.zero_grad()
                    outputs = model(batch_x)
                    loss = criterion(outputs, batch_y)
                    loss.backward()
                    optimizer.step()
                    train_loss += loss.item() * batch_x.size(0)
                
                train_loss /= len(train_loader.dataset)
                
                model.eval()
                val_loss = 0
                with torch.no_grad():
                    for batch_x, batch_y in val_loader:
                        batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                        outputs = model(batch_x)
                        loss = criterion(outputs, batch_y)
                        val_loss += loss.item() * batch_x.size(0)
                val_loss /= len(val_loader.dataset)
                
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    torch.save(model.state_dict(), os.path.join(models_dir, f'arrival_{name}_lstm.pth'))
                else:
                    patience_counter += 1
                    
                if patience_counter >= patience:
                    print(f"Early stopping at epoch {epoch+1}")
                    break
                    
            # Load best model for evaluation
            model.load_state_dict(torch.load(os.path.join(models_dir, f'arrival_{name}_lstm.pth')))
            model.eval()
            
            test_dataset = TimeSeriesDataset(X_test, y_test)
            test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)
            
            preds = []
            with torch.no_grad():
                for batch_x, _ in test_loader:
                    batch_x = batch_x.to(self.device)
                    out = model(batch_x)
                    preds.extend(out.cpu().numpy())
            
            preds = np.maximum(0.0, np.array(preds))
            
            m_mae = mean_absolute_error(y_test, preds)
            m_rmse = np.sqrt(mean_squared_error(y_test, preds))
            m_r2 = r2_score(y_test, preds)
            
            print(f"LSTM Horizon {name.upper()}: MAE={m_mae:.2f}, RMSE={m_rmse:.2f}, R2={m_r2:.2f}")
            
            results[name] = {
                "target": target_col,
                "model": f"LSTM ({name})",
                "model_mae": float(m_mae),
                "model_rmse": float(m_rmse),
                "model_r2": float(m_r2)
            }
            
        # Save training configuration
        config = {
            "lookback": self.lookback,
            "features": self.features,
            "hidden_size": 64,
            "num_layers": 2,
            "dropout": 0.2,
            "learning_rate": 0.001
        }
        with open(os.path.join(models_dir, 'lstm_config.json'), 'w') as f:
            json.dump(config, f)
            
        return {
            "model_name": "LSTM Arrival Forecaster",
            "features": self.features,
            "training_period": f"{train['date'].min().date()} to {train['date'].max().date()}",
            "test_period": f"{test['date'].min().date()} to {test['date'].max().date()}",
            "training_rows": len(train),
            "test_rows": len(test),
            "horizons": results
        }

    def predict_panel(self, df):
        df = self.prepare_data(df)
        df = df.sort_values(by=['dpc_id', 'date']).reset_index(drop=True)
        
        models_dir = os.path.join(os.path.dirname(__file__), '../models')
        try:
            self.scaler = joblib.load(os.path.join(models_dir, 'lstm_scaler.pkl'))
        except FileNotFoundError:
            print("LSTM scaler not found, returning zero predictions.")
            df['lstm_arrival_1d_mt'] = 0.0
            df['lstm_arrival_3d_mt'] = 0.0
            df['lstm_arrival_7d_mt'] = 0.0
            return df
            
        df_scaled = df.copy()
        df_scaled[self.features] = self.scaler.transform(df_scaled[self.features])
        
        preds_dict = { '1d': np.zeros(len(df)), '3d': np.zeros(len(df)), '7d': np.zeros(len(df)) }
        
        for name in ['1d', '3d', '7d']:
            model_path = os.path.join(models_dir, f'arrival_{name}_lstm.pth')
            if not os.path.exists(model_path):
                continue
            
            model = PaddyLSTM(input_size=len(self.features)).to(self.device)
            model.load_state_dict(torch.load(model_path, map_location=self.device))
            model.eval()
            
            for dpc, group in df_scaled.groupby('dpc_id'):
                idx = group.index
                if len(group) < self.lookback:
                    continue
                
                features = group[self.features].values
                # To predict for each day `t`, we need data from `t-lookback+1` to `t`.
                # If we don't have enough history, we can't predict.
                # Actually, the prompt says "predict_panel" should generate predictions for all rows where possible.
                X_batch = []
                valid_indices = []
                for i in range(self.lookback - 1, len(group)):
                    seq = features[i - self.lookback + 1 : i + 1]
                    X_batch.append(seq)
                    valid_indices.append(idx[i])
                    
                if X_batch:
                    X_tensor = torch.tensor(np.array(X_batch), dtype=torch.float32).to(self.device)
                    with torch.no_grad():
                        out = model(X_tensor)
                    out = np.maximum(0.0, out.cpu().numpy())
                    preds_dict[name][valid_indices] = out

        df['lstm_arrival_1d_mt'] = np.round(preds_dict['1d'], 1)
        df['lstm_arrival_3d_mt'] = np.round(preds_dict['3d'], 1)
        df['lstm_arrival_7d_mt'] = np.round(preds_dict['7d'], 1)
        
        return df
