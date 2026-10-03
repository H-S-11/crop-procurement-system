import os
import pandas as pd
import numpy as np

def generate_arrival_features(engine=None):
    csv_path = os.path.join(os.path.dirname(__file__), '../../data/B2_daily_arrivals_Thanjavur.csv')
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # Sort strictly chronologically by DPC and date
    df = df.sort_values(['dpc_id', 'date']).reset_index(drop=True)
    
    # Primary observed arrival
    df['arrival_mt'] = df['accepted_procured_mt'].fillna(0.0)
    df['recorded_dispatched_mt'] = df['dispatched_mt'].fillna(0.0)
    df['recorded_closing_stock_mt'] = df['closing_stock_mt'].fillna(0.0)
    
    # LAGGED features (using shift(1) to strictly prevent look-ahead bias / data leakage)
    g = df.groupby('dpc_id')['arrival_mt']
    df['arrival_lag1'] = g.shift(1).fillna(0.0)
    df['arrival_3d_mean'] = g.transform(lambda x: x.shift(1).rolling(3, min_periods=1).mean()).fillna(0.0)
    df['arrival_7d_mean'] = g.transform(lambda x: x.shift(1).rolling(7, min_periods=1).mean()).fillna(0.0)
    df['arrival_7d_max'] = g.transform(lambda x: x.shift(1).rolling(7, min_periods=1).max()).fillna(0.0)
    df['arrival_14d_mean'] = g.transform(lambda x: x.shift(1).rolling(14, min_periods=1).mean()).fillna(0.0)
    df['arrival_volatility'] = g.transform(lambda x: x.shift(1).rolling(7, min_periods=2).std()).fillna(0.0)
    
    # FORWARD TARGETS (for future arrival forecasting models)
    # Target 1: Next day arrival (t+1)
    df['future_arrival_1d'] = g.shift(-1)
    # Target 2: Next 3 days cumulative arrivals (t+1, t+2, t+3)
    df['future_arrival_3d'] = (g.shift(-1).fillna(0.0) + g.shift(-2).fillna(0.0) + g.shift(-3).fillna(0.0))
    # Target 3: Next 7 days cumulative arrivals
    future_7d = pd.Series(0.0, index=df.index)
    for shift_i in range(1, 8):
        future_7d += g.shift(-shift_i).fillna(0.0)
    df['future_arrival_7d'] = future_7d
    
    # Per-DPC historical baseline (mean and std during active harvesting)
    active_mask = df['arrival_mt'] > 0
    dpc_stats = df[active_mask].groupby('dpc_id')['arrival_mt'].agg(['mean', 'std']).reset_index()
    dpc_stats = dpc_stats.rename(columns={'mean': 'dpc_arrival_mean', 'std': 'dpc_arrival_std'})
    dpc_stats['dpc_arrival_std'] = dpc_stats['dpc_arrival_std'].fillna(5.0)
    
    df = df.merge(dpc_stats, on='dpc_id', how='left')
    df['dpc_arrival_mean'] = df['dpc_arrival_mean'].fillna(10.0)
    df['dpc_arrival_std'] = df['dpc_arrival_std'].fillna(5.0)
    
    # Surge threshold: mean + 2*sigma
    df['surge_threshold_mt'] = df['dpc_arrival_mean'] + 2.0 * df['dpc_arrival_std']
    
    # Moisture features
    df['mean_moisture_pct'] = df['mean_moisture_pct'].fillna(0.0)
    df['share_lots_above_17pct'] = df['share_lots_above_17pct'].fillna(0.0)
    
    cols = [
        'dpc_id', 'date', 'arrival_mt', 'recorded_dispatched_mt', 'recorded_closing_stock_mt',
        'arrival_lag1', 'arrival_3d_mean', 'arrival_7d_mean', 'arrival_7d_max', 'arrival_14d_mean',
        'arrival_volatility', 'future_arrival_1d', 'future_arrival_3d', 'future_arrival_7d',
        'dpc_arrival_mean', 'surge_threshold_mt', 'mean_moisture_pct', 'share_lots_above_17pct'
    ]
    
    return df[cols]
