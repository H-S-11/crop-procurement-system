import os
import sys
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine

# Ensure database and sibling pipeline modules are discoverable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import engine

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from spatial_features import generate_spatial_features
from road_features import generate_road_features
from flood_features import generate_flood_features
from rainfall_features import generate_rainfall_features
from arrival_features import generate_arrival_features
from damage_features import generate_damage_features
from access_features import generate_access_features

def run_preprocessing():
    print("Generating spatial features...")
    spatial_df = generate_spatial_features(engine)
    
    print("Generating road features...")
    road_df = generate_road_features(engine)
    
    print("Generating flood features (Sentinel-1 SAR observed exposure)...")
    flood_df = generate_flood_features(engine)
    
    print("Generating rainfall features...")
    rain_df = generate_rainfall_features(engine)
    
    print("Generating arrival and stock features...")
    arrival_df = generate_arrival_features(engine)
    
    print("Generating damage features...")
    damage_df = generate_damage_features(engine)
    
    print("Generating access features...")
    access_df = generate_access_features(engine)
    
    print("Merging feature store...")
    
    # Merge static features
    static_df = pd.merge(spatial_df, road_df, on='dpc_id', how='left')
    static_df = pd.merge(static_df, flood_df, on='dpc_id', how='left')
    static_df = pd.merge(static_df, damage_df, on='dpc_id', how='left')
    
    if arrival_df.empty and rain_df.empty:
        print("No temporal data available to build the time-series feature store.")
        return
    
    start_date = arrival_df['date'].min() if not arrival_df.empty else '2025-09-01'
    end_date = arrival_df['date'].max() if not arrival_df.empty else '2026-04-20'
    dates = pd.DataFrame({'date': pd.date_range(start=start_date, end=end_date)})
    
    dpcs = pd.DataFrame({'dpc_id': static_df['dpc_id'].unique()})
    panel = dpcs.merge(dates, how='cross')
    
    # Merge temporal features
    panel = pd.merge(panel, rain_df, on=['dpc_id', 'date'], how='left')
    panel = pd.merge(panel, arrival_df, on=['dpc_id', 'date'], how='left')
    panel = pd.merge(panel, access_df, on=['dpc_id', 'date'], how='left')
    
    # Fill temporal numeric features
    numeric_fills = {
        'rainfall_3d': 0.0, 'rainfall_7d': 0.0, 'rainfall_14d': 0.0, 'rainfall_30d': 0.0, 'rainy_days_7d': 0.0,
        'arrival_mt': 0.0, 'recorded_dispatched_mt': 0.0, 'recorded_closing_stock_mt': 0.0,
        'arrival_lag1': 0.0, 'arrival_3d_mean': 0.0, 'arrival_7d_mean': 0.0, 'arrival_7d_max': 0.0,
        'arrival_14d_mean': 0.0, 'arrival_volatility': 0.0,
        'future_arrival_1d': 0.0, 'future_arrival_3d': 0.0, 'future_arrival_7d': 0.0,
        'dpc_arrival_mean': 10.0, 'surge_threshold_mt': 20.0,
        'mean_moisture_pct': 0.0, 'share_lots_above_17pct': 0.0, 'access_disruption': 0.0
    }
    for col, val in numeric_fills.items():
        if col in panel.columns:
            panel[col] = panel[col].fillna(val)
            
    # Merge static features
    final_fs = pd.merge(panel, static_df, on='dpc_id', how='left')
    final_fs['historical_damage_events'] = final_fs['historical_damage_events'].fillna(0)
    final_fs['damage_incidence_rate'] = final_fs['damage_incidence_rate'].fillna(0.0)
    final_fs['feature_generated_at'] = datetime.now().isoformat()
    
    # Standardize date to string YYYY-MM-DD
    final_fs['date'] = pd.to_datetime(final_fs['date']).dt.strftime('%Y-%m-%d')
    
    print("Saving feature store to database...")
    final_fs.to_sql('dpc_feature_store', engine, if_exists='replace', index=False)
    print(f"Feature store generated with {len(final_fs)} rows.")

if __name__ == '__main__':
    run_preprocessing()
