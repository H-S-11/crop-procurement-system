# Model Evaluation

This document contains the evaluation results of the Module 3 Forecasting models.

## Arrival RandomForestRegressor
* **Target**: `arrival_mt`
* **Training period**: 2025-09-01 00:00:00 to 2026-02-28 00:00:00
* **Validation period**: 2026-02-28 00:00:00 to 2026-03-19 00:00:00
* **Test period**: 2026-03-19 00:00:00 to 2026-04-20 00:00:00
* **Training rows**: 42998
* **Features**: arrival_7d_mean, arrival_7d_max, arrival_14d_mean, arrival_volatility, rainfall_7d, rainfall_14d, elevation, nearest_road_dist
* **Baseline metrics**:
  * MAE: 1.8998
  * RMSE: 3.3547
  * R2: 0.6370
* **Model metrics**:
  * MAE: 2.1252
  * RMSE: 3.5815
  * R2: 0.5862

## Arrival LSTMForecaster (Experimental)
* **Target**: `arrival_mt`
* **Architecture**: PyTorch LSTM (2 layers, hidden size 64) with chronological sequencing
* **Training period**: 2025-09-01 00:00:00 to 2026-02-28 00:00:00
* **Validation period**: 2026-02-28 00:00:00 to 2026-03-19 00:00:00
* **Test period**: 2026-03-19 00:00:00 to 2026-04-20 00:00:00
* **Features**: Scaled lagged features and standard dynamic environmental features (e.g., rainfall, baseline means).
* **Note**: LSTM performance metrics pending final CI/CD evaluation run on remote cluster. Not yet proven better than RF. No causal relationships claimed.

## Moisture Proxy Risk Index
* **Target**: `moisture_risk_proxy (Proxy)`
* **Training period**: N/A
* **Validation period**: N/A
* **Test period**: N/A
* **Training rows**: 176778
* **Features**: rainfall_7d, rainfall_14d, flood_exposure
* **Note**: Transparent risk proxy, not a trained prediction.

## Access Disruption Model
* **Target**: `access_disruption`
* **Training period**: N/A
* **Validation period**: N/A
* **Test period**: N/A
* **Training rows**: 0
* **Features**: rainfall_7d, flood_exposure, nearest_road_dist, major_road_dist
* **Note**: Target cannot be constructed reliably. Document limitation instead of fabricating labels.

