import pandas as pd
import numpy as np
import os
import json

class MoistureModel:
    def __init__(self):
        self.features = ['rainfall_7d', 'rainfall_14d', 'flood_exposure']
        
    def prepare_data(self, df):
        return df

    def train_and_evaluate(self, df):
        print("Moisture / Rejection Risk: No defensible moisture target exists.")
        print("Creating proxy risk index using available predictors...")
        
        if 'flood_exposure' not in df.columns:
            df['flood_exposure'] = 0
        if 'rainfall_14d' not in df.columns:
            df['rainfall_14d'] = 0
            
        # Create risk proxy: combination of normalized rainfall and flood exposure
        max_rain = df['rainfall_14d'].max() if df['rainfall_14d'].max() > 0 else 1
        
        df['moisture_risk_proxy'] = (df['rainfall_14d'] / max_rain * 0.5) + (df['flood_exposure'].fillna(0) * 0.5)
        
        return {
            "model_name": "Moisture Proxy Risk Index",
            "target": "moisture_risk_proxy (Proxy)",
            "training_period": "N/A",
            "validation_period": "N/A",
            "test_period": "N/A",
            "training_rows": len(df),
            "features": self.features,
            "baseline_metrics": {"mae": None, "rmse": None, "r2": None},
            "model_metrics": {"mae": None, "rmse": None, "r2": None},
            "note": "Transparent risk proxy, not a trained prediction."
        }
