import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

class ArrivalForecaster:
    """
    Forward-Looking Multi-Horizon Arrival Forecasting Model.
    Predicts future arrival volume (1-day, 3-day, 7-day cumulative MT)
    using strictly lagged features to prevent temporal data leakage.
    Preserves strict chronological train/val/test separation.
    """
    def __init__(self):
        self.features = [
            'arrival_lag1', 'arrival_3d_mean', 'arrival_7d_mean', 'arrival_14d_mean',
            'arrival_volatility', 'rainfall_3d', 'rainfall_7d', 'rainfall_14d',
            'capacity', 'nearest_road_dist', 'flood_exposure'
        ]
        self.model_1d = RandomForestRegressor(n_estimators=100, max_depth=8, min_samples_leaf=4, random_state=42)
        self.model_3d = RandomForestRegressor(n_estimators=100, max_depth=8, min_samples_leaf=4, random_state=42)
        self.model_7d = RandomForestRegressor(n_estimators=100, max_depth=8, min_samples_leaf=4, random_state=42)
        
    def prepare_data(self, df):
        # Filter to active dates where arrivals exist
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by=['date', 'dpc_id']).reset_index(drop=True)
        # Ensure capacity and features exist
        for col in self.features:
            if col not in df.columns:
                df[col] = 0.0
            else:
                df[col] = df[col].fillna(0.0)
        return df

    def train_and_evaluate(self, df):
        df = self.prepare_data(df)
        
        # Only train on rows where target is defined
        train_mask = (df['future_arrival_1d'].notna()) & (df['date'] <= '2026-03-31')
        valid_df = df[train_mask]
        
        if len(valid_df) < 100:
            print("Insufficient data rows for arrival forecasting.")
            return None
            
        # Chronological Split (70% train, 15% val, 15% test)
        dates = sorted(valid_df['date'].unique())
        n_dates = len(dates)
        split1_date = dates[int(n_dates * 0.70)]
        split2_date = dates[int(n_dates * 0.85)]
        
        train = valid_df[valid_df['date'] <= split1_date]
        val = valid_df[(valid_df['date'] > split1_date) & (valid_df['date'] <= split2_date)]
        test = valid_df[valid_df['date'] > split2_date]
        
        print(f"Chronological split: Train ({train['date'].min().date()} to {train['date'].max().date()}, {len(train)} rows)")
        print(f"Val ({val['date'].min().date()} to {val['date'].max().date()}, {len(val)} rows)")
        print(f"Test ({test['date'].min().date()} to {test['date'].max().date()}, {len(test)} rows)")
        
        X_train, X_test = train[self.features], test[self.features]
        
        results = {}
        models_dir = os.path.join(os.path.dirname(__file__), '../models')
        os.makedirs(models_dir, exist_ok=True)
        
        horizons = [
            ('1d', 'future_arrival_1d', self.model_1d, 'arrival_3d_mean', 1.0),
            ('3d', 'future_arrival_3d', self.model_3d, 'arrival_3d_mean', 3.0),
            ('7d', 'future_arrival_7d', self.model_7d, 'arrival_7d_mean', 7.0),
        ]
        
        for name, target_col, model, baseline_col, baseline_mult in horizons:
            y_train = train[target_col].fillna(0.0)
            y_test = test[target_col].fillna(0.0)
            
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            
            # Baseline is scaled trailing mean
            baseline_preds = test[baseline_col].fillna(0.0) * baseline_mult
            
            b_mae = mean_absolute_error(y_test, baseline_preds)
            b_rmse = np.sqrt(mean_squared_error(y_test, baseline_preds))
            b_r2 = r2_score(y_test, baseline_preds)
            
            m_mae = mean_absolute_error(y_test, preds)
            m_rmse = np.sqrt(mean_squared_error(y_test, preds))
            m_r2 = r2_score(y_test, preds)
            
            print(f"Horizon {name.upper()}: Baseline MAE={b_mae:.2f}, RMSE={b_rmse:.2f} | Model MAE={m_mae:.2f}, RMSE={m_rmse:.2f}, R2={m_r2:.2f}")
            
            joblib.dump(model, os.path.join(models_dir, f'arrival_{name}_rf.pkl'))
            results[name] = {
                "target": target_col,
                "model": f"RandomForestRegressor ({name})",
                "baseline_mae": float(b_mae),
                "baseline_rmse": float(b_rmse),
                "model_mae": float(m_mae),
                "model_rmse": float(m_rmse),
                "model_r2": float(m_r2)
            }
            
        return {
            "model_name": "Multi-Horizon Arrival Forecaster",
            "features": self.features,
            "training_period": f"{train['date'].min().date()} to {train['date'].max().date()}",
            "test_period": f"{test['date'].min().date()} to {test['date'].max().date()}",
            "training_rows": len(train),
            "test_rows": len(test),
            "horizons": results
        }

    def predict_panel(self, df):
        """Generate 1d, 3d, 7d expected arrivals, trends, and surge anomaly flags."""
        df = self.prepare_data(df)
        X = df[self.features]
        
        preds_1d = np.maximum(0.0, self.model_1d.predict(X))
        preds_3d = np.maximum(0.0, self.model_3d.predict(X))
        preds_7d = np.maximum(0.0, self.model_7d.predict(X))
        
        df['expected_arrival_1d_mt'] = np.round(preds_1d, 1)
        df['expected_arrival_3d_mt'] = np.round(preds_3d, 1)
        df['expected_arrival_7d_mt'] = np.round(preds_7d, 1)
        
        # Arrival Trend Classification:
        # Expected daily rate over next 3 days vs trailing 7d mean
        daily_future_rate = df['expected_arrival_3d_mt'] / 3.0
        trailing_rate = df['arrival_7d_mean']
        
        diff_ratio = np.where(trailing_rate > 1.0, (daily_future_rate - trailing_rate) / trailing_rate, 0.0)
        
        df['arrival_trend'] = np.select(
            [diff_ratio > 0.15, diff_ratio < -0.15],
            ['Increasing', 'Declining'],
            default='Stable'
        )
        
        # Surge Anomaly Flag:
        # Flag if 1-day or 3-day expected arrivals exceed DPC's 2-sigma surge threshold
        df['arrival_surge_flag'] = (df['expected_arrival_1d_mt'] > df['surge_threshold_mt']) | \
                                   (df['expected_arrival_3d_mt'] > 3.0 * df['surge_threshold_mt'])
        
        return df
