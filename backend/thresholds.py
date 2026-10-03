import pandas as pd
from database import SessionLocal

db = SessionLocal()
# Fetch latest scores for threshold setting
date_val = '2025-11-29 00:00:00.000000'
df = pd.read_sql_query(f"SELECT * FROM dpc_risk_scores WHERE date = '{date_val}'", db.bind)

p50 = df['composite_risk_score'].quantile(0.50)
p80 = df['composite_risk_score'].quantile(0.80)
p95 = df['composite_risk_score'].quantile(0.95)

print(f'Cutoffs: Low <= {p50:.2f}, Moderate <= {p80:.2f}, High <= {p95:.2f}, Critical > {p95:.2f}')

low = len(df[df['composite_risk_score'] <= p50])
mod = len(df[(df['composite_risk_score'] > p50) & (df['composite_risk_score'] <= p80)])
high = len(df[(df['composite_risk_score'] > p80) & (df['composite_risk_score'] <= p95)])
crit = len(df[df['composite_risk_score'] > p95])

print(f'Counts: Low: {low}, Moderate: {mod}, High: {high}, Critical: {crit}')
db.close()
