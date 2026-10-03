import os
import json
import pandas as pd
import sys

# Ensure database and sibling imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import engine

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from arrival_model import ArrivalForecaster
from arrival_lstm import LSTMForecaster
from moisture_model import MoistureModel
from access_model import AccessModel

def write_markdown_report(results, report_path):
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Model Evaluation & Validation Report\n\n")
        f.write("Evaluation results for the Crop Procurement Forecasting System models.\n\n")
        f.write("> **Methodological Standard**: Temporal chronological split (70% train, 15% validation, 15% test). ")
        f.write("No look-ahead bias; all features are strictly lagged prior to the forecast window.\n\n")
        
        for res in results:
            if not res: continue
            f.write(f"## {res['model_name']}\n")
            if 'horizons' in res:
                f.write(f"* **Training Period**: {res.get('training_period', 'N/A')}\n")
                f.write(f"* **Test Period**: {res.get('test_period', 'N/A')}\n")
                f.write(f"* **Training Samples**: {res.get('training_rows', 0)}\n")
                f.write(f"* **Test Samples**: {res.get('test_rows', 0)}\n")
                f.write(f"* **Features**: {', '.join(res['features'])}\n\n")
                f.write("| Horizon | Target | Baseline MAE | Baseline RMSE | Model MAE | Model RMSE | Model R² |\n")
                f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
                for h_name, h_metrics in res['horizons'].items():
                    f.write(f"| {h_name.upper()} | `{h_metrics['target']}` | {h_metrics['baseline_mae']:.2f} | {h_metrics['baseline_rmse']:.2f} | {h_metrics['model_mae']:.2f} | {h_metrics['model_rmse']:.2f} | {h_metrics['model_r2']:.3f} |\n")
                f.write("\n")
            else:
                f.write(f"* **Target**: `{res.get('target', 'N/A')}`\n")
                f.write(f"* **Status**: {res.get('note', 'Evaluated')}\n")
                if res.get('model_metrics', {}).get('mae') is not None:
                    f.write(f"* **Metrics**: MAE={res['model_metrics']['mae']:.2f}\n")
                else:
                    f.write("* **Metrics**: INSUFFICIENT GROUND TRUTH DATA FOR PREDICTIVE MODELING\n")
                f.write("\n")

def main():
    print("Loading validated feature data (dpc_feature_store)...")
    try:
        df = pd.read_sql("SELECT * FROM dpc_feature_store", engine)
    except Exception as e:
        print(f"Failed to load dpc_feature_store: {e}. Please run run_preprocessing.py first.")
        return
        
    if df.empty:
        print("Feature store is empty!")
        return
        
    df['date'] = pd.to_datetime(df['date'])
    results = []
    
    print("\n--- 1. Multi-Horizon Arrival Forecaster (RF & Baseline) ---")
    arr_forecaster = ArrivalForecaster()
    arr_results = arr_forecaster.train_and_evaluate(df)
    if arr_results:
        results.append(arr_results)
        
    print("\n--- 1b. Multi-Horizon Arrival Forecaster (LSTM) ---")
    try:
        lstm_forecaster = LSTMForecaster(lookback=14)
        lstm_results = lstm_forecaster.train_and_evaluate(df)
        if lstm_results:
            results.append(lstm_results)
    except Exception as e:
        print(f"Failed to train LSTM: {e}")
        
    print("\n--- 2. Moisture / Rejection Proxy Model ---")
    moist_model = MoistureModel()
    moist_results = moist_model.train_and_evaluate(df)
    results.append(moist_results)
    
    print("\n--- 3. Access Disruption Model ---")
    acc_model = AccessModel()
    acc_results = acc_model.train_and_evaluate(df)
    results.append(acc_results)
    
    # Save JSON metrics for API consumption
    models_dir = os.path.join(os.path.dirname(__file__), '../models')
    os.makedirs(models_dir, exist_ok=True)
    metrics_path = os.path.join(models_dir, 'metrics.json')
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved metrics to {metrics_path}")
    
    # Save Markdown report
    docs_report = os.path.join(os.path.dirname(__file__), '../../docs/model_evaluation.md')
    write_markdown_report(results, docs_report)
    print(f"Saved evaluation markdown report to {docs_report}")

if __name__ == '__main__':
    main()
