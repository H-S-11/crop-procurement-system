import pandas as pd
import numpy as np
import json
import os

def load_weights():
    config_path = os.path.join(os.path.dirname(__file__), '../config/risk_weights.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def calculate_risk_scores(df):
    print("Calculating composite risk scores...")
    weights = load_weights()
    
    # 1. Storage Risk Score (0-100)
    # < 70% -> 0-30, 70-85% -> 30-70, 85-100% -> 70-100, >100% -> 100
    df['storage_risk_score'] = np.clip(df['capacity_utilization'] * 100, 0, 100)
    
    # 2. Flood Risk Score
    df['flood_risk_score'] = np.clip(df.get('flood_exposure', 0).fillna(0) * 100, 0, 100)
    
    # 3. Weather / Moisture Risk Score
    # Use real moisture data if available (e.g. mean_moisture_pct > 0), else proxy via rainfall
    max_rain = df['rainfall_14d'].max() if 'rainfall_14d' in df and df['rainfall_14d'].max() > 0 else 1
    proxy_moisture_risk = np.clip((df.get('rainfall_14d', 0).fillna(0) / max_rain) * 100, 0, 100)
    
    real_moisture_risk = np.where(df.get('mean_moisture_pct', 0) > 0, np.clip(df.get('share_lots_above_17pct', 0) * 100, 0, 100), proxy_moisture_risk)
    df['weather_risk_score'] = real_moisture_risk
    
    # 4. Damage Risk Score
    df['damage_risk_score'] = np.clip(df.get('damage_incidence_rate', 0).fillna(0) * 100, 0, 100)
    
    # 5. Access Risk Score
    df['access_risk_score'] = np.clip(df.get('access_disruption', 0).fillna(0) * 100, 0, 100)
    
    # Composite Risk
    df['composite_risk_score'] = (
        df['storage_risk_score'] * weights['storage_weight'] +
        df['flood_risk_score'] * weights['flood_weight'] +
        df['weather_risk_score'] * weights['weather_weight'] +
        df['damage_risk_score'] * weights['damage_weight'] +
        df['access_risk_score'] * weights['access_weight']
    )
    
    return df
