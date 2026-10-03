"""
Risk Engine Execution Script.
Executes multi-horizon forecasting, stock balance flow, and operational risk classification.
Writes enriched operational metrics to dpc_risk_scores.
"""
import os
import sys
import json
import pandas as pd
from sqlalchemy import create_engine

# Database and sibling imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import engine

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from storage import calculate_storage_and_risk

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../forecasting')))
from arrival_model import ArrivalForecaster
from arrival_lstm import LSTMForecaster

def run_risk_engine():
    print("Loading feature store from database...")
    df = pd.read_sql("SELECT * FROM dpc_feature_store", engine)
    print(f"Loaded {len(df)} rows from feature store.")
    
    # 1. Generate multi-horizon arrival forecasts, trends, and surge anomalies
    print("Generating arrival forecasts, trends, and surge anomaly flags...")
    forecaster = ArrivalForecaster()
    # Check if pre-trained models exist, else train and predict
    models_dir = os.path.join(os.path.dirname(__file__), '../models')
    model_file = os.path.join(models_dir, 'arrival_3d_rf.pkl')
    
    if os.path.exists(model_file):
        try:
            import joblib
            forecaster.model_1d = joblib.load(os.path.join(models_dir, 'arrival_1d_rf.pkl'))
            forecaster.model_3d = joblib.load(os.path.join(models_dir, 'arrival_3d_rf.pkl'))
            forecaster.model_7d = joblib.load(os.path.join(models_dir, 'arrival_7d_rf.pkl'))
            print("Loaded pre-trained multi-horizon arrival models.")
        except Exception as e:
            print(f"Loading pre-trained models failed ({e}), training fresh...")
            forecaster.train_and_evaluate(df)
    else:
        print("Training multi-horizon arrival forecaster...")
        forecaster.train_and_evaluate(df)
        
    df = forecaster.predict_panel(df)
    
    print("Generating LSTM arrival forecasts...")
    lstm_forecaster = LSTMForecaster(lookback=14)
    # Check if LSTM models exist
    lstm_model_file = os.path.join(models_dir, 'arrival_3d_lstm.pth')
    if not os.path.exists(lstm_model_file):
        print("Training LSTM forecaster...")
        lstm_forecaster.train_and_evaluate(df)
        
    df = lstm_forecaster.predict_panel(df)
    
    # 2. Run Storage Flow & Operational Risk Engine for RF (default)
    print("Computing storage saturation and operational risk tiers for RF...")
    df_rf = calculate_storage_and_risk(df)
    df_rf['risk_reasons_json'] = df_rf['risk_explanation'].apply(json.dumps)
    df_rf['suggested_alternatives_json'] = df_rf['suggested_alternatives'].apply(json.dumps)
    
    # 2b. Run for LSTM
    print("Computing for LSTM...")
    df_lstm = df.copy()
    if 'lstm_arrival_1d_mt' in df_lstm.columns:
        df_lstm['expected_arrival_1d_mt'] = df_lstm['lstm_arrival_1d_mt']
        df_lstm['expected_arrival_3d_mt'] = df_lstm['lstm_arrival_3d_mt']
        df_lstm['expected_arrival_7d_mt'] = df_lstm['lstm_arrival_7d_mt']
    df_lstm = calculate_storage_and_risk(df_lstm)
    df_lstm['risk_reasons_json'] = df_lstm['risk_explanation'].apply(json.dumps)
    df_lstm['suggested_alternatives_json'] = df_lstm['suggested_alternatives'].apply(json.dumps)
    
    # 2c. Run for Baseline
    print("Computing for Baseline...")
    df_base = df.copy()
    df_base['expected_arrival_1d_mt'] = df_base['arrival_3d_mean'].fillna(0)
    df_base['expected_arrival_3d_mt'] = (df_base['arrival_3d_mean'].fillna(0) * 3).round(1)
    df_base['expected_arrival_7d_mt'] = (df_base['arrival_7d_mean'].fillna(0) * 7).round(1)
    df_base = calculate_storage_and_risk(df_base)
    df_base['risk_reasons_json'] = df_base['risk_explanation'].apply(json.dumps)
    df_base['suggested_alternatives_json'] = df_base['suggested_alternatives'].apply(json.dumps)
    
    # Merge LSTM and Baseline columns into df_rf
    merge_cols = [
        'expected_arrival_1d_mt', 'expected_arrival_3d_mt', 'expected_arrival_7d_mt',
        'projected_stock_mt', 'utilization_pct', 'overflow_mt', 'risk_tier', 'risk_reasons_json', 'suggested_alternatives_json'
    ]
    for c in merge_cols:
        df_rf[f'lstm_{c}'] = df_lstm[c]
        df_rf[f'baseline_{c}'] = df_base[c]
    
    # 3. Select final schema columns for dpc_risk_scores
    risk_cols = [
        'dpc_id', 'date', 'name', 'block', 'village', 'latitude', 'longitude',
        'capacity_mt', 'current_stock_mt',
        'expected_arrival_1d_mt', 'expected_arrival_3d_mt', 'expected_arrival_7d_mt',
        'estimated_outflow_3d_mt', 'estimated_outflow_7d_mt',
        'projected_stock_mt', 'projected_stock_3d_mt', 'projected_stock_7d_mt',
        'utilization_pct', 'overflow_mt',
        'arrival_trend', 'arrival_surge_flag',
        'flood_exposure_pct', 'rainfall_7d_mm', 'access_disrupted',
        'is_active_season', 'risk_tier', 'risk_reasons_json', 'outflow_assumption_note',
        'suggested_alternatives_json'
    ]
    
    # Add LSTM and Baseline columns to risk_cols
    for c in merge_cols:
        risk_cols.extend([f'lstm_{c}', f'baseline_{c}'])
        
    # Keep only available columns
    save_cols = [c for c in risk_cols if c in df_rf.columns]
    df_risk = df_rf[save_cols].copy()
    df_risk['date'] = pd.to_datetime(df_risk['date']).dt.strftime('%Y-%m-%d')
    
    print(f"Saving {len(df_risk)} records to dpc_risk_scores table...")
    df_risk.to_sql('dpc_risk_scores', engine, if_exists='replace', index=False)
    
    # Print summary of snapshot date (e.g. 2025-11-29)
    snapshot = df_risk[df_risk['date'] == '2025-11-29']
    if not snapshot.empty:
        active = snapshot[snapshot['is_active_season']]
        print(f"\n--- Snapshot 2025-11-29 Operational Summary ---")
        print(f"Active DPCs: {len(active)} / {len(snapshot)}")
        print(f"Risk Tiers: {active['risk_tier'].value_counts().to_dict()}")
        print(f"Average Utilization: {active['utilization_pct'].mean():.1f}%")
        print(f"Total Projected Overflow: {active['overflow_mt'].sum():.1f} MT across {(active['overflow_mt'] > 0).sum()} centres")
        print(f"Arrival Surges Detected: {active['arrival_surge_flag'].sum()} centres")
        
    print("Risk engine completed successfully.")

if __name__ == '__main__':
    run_risk_engine()
