import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader

class TimeSeriesDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)
        
    def __len__(self):
        return len(self.X)
        
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

def build_sequences(df, feature_cols, target_col, lookback=14):
    """
    Builds sequences for LSTM while preventing temporal leakage.
    Each sequence uses `lookback` days of historical data to predict `target_col`.
    """
    df = df.sort_values(by=['dpc_id', 'date']).reset_index(drop=True)
    
    X_list, y_list = [], []
    
    for dpc, group in df.groupby('dpc_id'):
        group = group.reset_index(drop=True)
        if len(group) <= lookback:
            continue
            
        features = group[feature_cols].values
        # Ensure we're targeting the value that immediately follows the lookback window
        targets = group[target_col].values
        
        for i in range(len(group) - lookback):
            seq_x = features[i: i + lookback]
            seq_y = targets[i + lookback]
            
            if not np.isnan(seq_y):
                seq_x = np.nan_to_num(seq_x, nan=0.0)
                X_list.append(seq_x)
                y_list.append(seq_y)
                
    if not X_list:
        return np.array([]), np.array([])
        
    return np.array(X_list), np.array(y_list)
