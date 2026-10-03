import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from database import SessionLocal
import os

db = SessionLocal()
# Fetch testing data
df = pd.read_sql("SELECT * FROM dpc_feature_store WHERE arrival_mt IS NOT NULL", db.bind)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(by=['dpc_id', 'date'])

# Generate some additional baselines
df['arrival_3d_mean'] = df.groupby('dpc_id')['arrival_mt'].transform(lambda x: x.shift(1).rolling(3, min_periods=1).mean())
df['seasonal_naive_7d'] = df.groupby('dpc_id')['arrival_mt'].transform(lambda x: x.shift(7))
df['ewma_alpha_0_3'] = df.groupby('dpc_id')['arrival_mt'].transform(lambda x: x.shift(1).ewm(alpha=0.3, min_periods=1).mean())

df = df.dropna(subset=['arrival_mt', 'arrival_7d_mean', 'seasonal_naive_7d', 'ewma_alpha_0_3'])
df = df.sort_values(by=['date', 'dpc_id'])

split1 = int(len(df) * 0.7)
split2 = int(len(df) * 0.85)
test = df.iloc[split2:]

y_test = test['arrival_mt']

models = {
    '7-Day Mean (Current Baseline)': test['arrival_7d_mean'],
    '3-Day Mean': test['arrival_3d_mean'],
    'Seasonal Naive (T-7)': test['seasonal_naive_7d'],
    'EWMA (alpha=0.3)': test['ewma_alpha_0_3']
}

print("Baseline Evaluation on Test Set:")
for name, preds in models.items():
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)
    print(f"\n{name}:")
    print(f"  MAE:  {mae:.3f}")
    print(f"  RMSE: {rmse:.3f}")
    print(f"  R2:   {r2:.3f}")

# Also evaluate RF predictions to confirm
from sklearn.ensemble import RandomForestRegressor
train = df.iloc[:split1]
features = ['arrival_7d_mean', 'arrival_7d_max', 'arrival_14d_mean', 'arrival_volatility', 'rainfall_7d', 'rainfall_14d', 'elevation', 'nearest_road_dist']
X_train = train[features].fillna(0)
y_train = train['arrival_mt']
X_test = test[features].fillna(0)

rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
rf.fit(X_train, y_train)
rf_preds = rf.predict(X_test)
print("\nRandom Forest (Current Model):")
print(f"  MAE:  {mean_absolute_error(y_test, rf_preds):.3f}")
print(f"  RMSE: {np.sqrt(mean_squared_error(y_test, rf_preds)):.3f}")
print(f"  R2:   {r2_score(y_test, rf_preds):.3f}")

db.close()
