"""
Export verified operational snapshot for the static fallback and demo mode.
Source of truth is dpc_risk_scores and dpc_feature_store in SQLite.
"""
import os
import json
import sqlite3
import pandas as pd
import numpy as np

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/paddy_db.sqlite'))
out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend/public/demo-data.json'))

conn = sqlite3.connect(db_path)
target_date = '2025-11-29'

query = f"""
SELECT * FROM dpc_risk_scores
WHERE date = '{target_date}'
"""
df = pd.read_sql_query(query, conn)

if df.empty:
    max_date = pd.read_sql_query("SELECT MAX(date) FROM dpc_risk_scores", conn).iloc[0, 0]
    df = pd.read_sql_query(f"SELECT * FROM dpc_risk_scores WHERE date = '{max_date}'", conn)
    target_date = max_date

# Read timeseries series for active season up to end of harvest (filtered to meaningful dates)
series_query = f"""
SELECT 
    f.dpc_id,
    f.date,
    f.arrival_mt as actual_arrival,
    r.expected_arrival_1d_mt as forecast_arrival,
    r.projected_stock_mt
FROM dpc_feature_store f
LEFT JOIN dpc_risk_scores r ON f.dpc_id = r.dpc_id AND f.date = r.date
WHERE f.date >= '2025-09-01' AND f.date <= '2025-12-31'
ORDER BY f.dpc_id, f.date
"""
series_df = pd.read_sql_query(series_query, conn)
conn.close()

# Group series by DPC
series_dict = {}
for dpc_id, group in series_df.groupby('dpc_id'):
    pts = []
    # Sample every 3 days or keep significant dates to keep file fast and responsive
    for _, row in group.iterrows():
        pts.append({
            'date': str(row['date']),
            'actual_arrival': float(row['actual_arrival']) if pd.notna(row['actual_arrival']) else 0.0,
            'forecast_arrival': float(row['forecast_arrival']) if pd.notna(row['forecast_arrival']) else None,
            'projected_stock': float(row['projected_stock_mt']) if pd.notna(row['projected_stock_mt']) else None
        })
    series_dict[dpc_id] = pts

records = []
for _, row in df.iterrows():
    reasons = []
    if pd.notna(row.get('risk_reasons_json')):
        try:
            reasons = json.loads(row['risk_reasons_json'])
        except Exception:
            reasons = []
            
    alternatives = []
    if pd.notna(row.get('suggested_alternatives_json')):
        try:
            alternatives = json.loads(row['suggested_alternatives_json'])
        except Exception:
            alternatives = []
            
    records.append({
        'id': str(row['dpc_id']),
        'name': row.get('name') or str(row['dpc_id']),
        'block': str(row.get('block') or ''),
        'village': row.get('village'),
        'lat': float(row['latitude']) if pd.notna(row.get('latitude')) else 10.75,
        'lon': float(row['longitude']) if pd.notna(row.get('longitude')) else 79.18,
        'capacity_mt': float(row['capacity_mt']) if pd.notna(row.get('capacity_mt')) else 100.0,
        'current_stock_mt': float(row['current_stock_mt']) if pd.notna(row.get('current_stock_mt')) else 0.0,
        'expected_arrival_1d_mt': float(row['expected_arrival_1d_mt']) if pd.notna(row.get('expected_arrival_1d_mt')) else 0.0,
        'expected_arrival_3d_mt': float(row['expected_arrival_3d_mt']) if pd.notna(row.get('expected_arrival_3d_mt')) else 0.0,
        'expected_arrival_7d_mt': float(row['expected_arrival_7d_mt']) if pd.notna(row.get('expected_arrival_7d_mt')) else 0.0,
        'estimated_outflow_3d_mt': float(row['estimated_outflow_3d_mt']) if pd.notna(row.get('estimated_outflow_3d_mt')) else 0.0,
        'projected_stock_mt': float(row['projected_stock_mt']) if pd.notna(row.get('projected_stock_mt')) else 0.0,
        'utilization_pct': float(row['utilization_pct']) if pd.notna(row.get('utilization_pct')) else 0.0,
        'overflow_mt': float(row['overflow_mt']) if pd.notna(row.get('overflow_mt')) else 0.0,
        'risk_tier': str(row['risk_tier']),
        'risk_reasons': reasons,
        'arrival_trend': str(row.get('arrival_trend') or 'Stable'),
        'arrival_surge_flag': bool(row.get('arrival_surge_flag') or False),
        'flood_exposure_pct': float(row['flood_exposure_pct']) if pd.notna(row.get('flood_exposure_pct')) else 0.0,
        'rainfall_7d_mm': float(row['rainfall_7d_mm']) if pd.notna(row.get('rainfall_7d_mm')) else 0.0,
        'access_disrupted': bool(row.get('access_disrupted') or False),
        'is_active_season': bool(row.get('is_active_season', True)),
        'outflow_assumption_note': str(row.get('outflow_assumption_note') or 'Modeled at 10% capacity/day (TNCSC Godown B5 unlinked to DPCs)'),
        'suggested_alternatives': alternatives,
        'series': series_dict.get(row['dpc_id'], [])
    })

data = {
    'snapshot_date': target_date,
    'total_dpcs': len(records),
    'dpcs': records
}

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

active_records = [r for r in records if r['is_active_season']]
print(f"Exported {len(records)} centres ({len(active_records)} active) to {out_path}")
print(f"Total Projected Overflow: {sum(r['overflow_mt'] for r in active_records):.1f} MT")
print(f"Risk Tiers breakdown: {pd.Series([r['risk_tier'] for r in active_records]).value_counts().to_dict()}")
