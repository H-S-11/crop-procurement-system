import json
import sqlite3
import pandas as pd
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db, DEFAULT_DB_PATH
from schemas.dpc import DPCBase

router = APIRouter(prefix="/dpcs", tags=["DPCs"])

@router.get("", response_model=List[DPCBase])
def get_dpcs(
    block: Optional[str] = None,
    risk_tier: Optional[str] = None,
    target_date: Optional[str] = Query('2025-11-29'),
    active_only: Optional[bool] = False,
    db: Session = Depends(get_db)
):
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    query = f"SELECT * FROM dpc_risk_scores WHERE date = '{target_date}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        conn = sqlite3.connect(DEFAULT_DB_PATH)
        max_date = pd.read_sql_query("SELECT MAX(date) FROM dpc_risk_scores", conn).iloc[0, 0]
        df = pd.read_sql_query(f"SELECT * FROM dpc_risk_scores WHERE date = '{max_date}'", conn)
        conn.close()
        
    if active_only:
        df = df[df['is_active_season'] == 1]
    if block:
        df = df[df['block'] == block]
    if risk_tier and risk_tier.upper() != 'ALL':
        df = df[df['risk_tier'] == risk_tier.upper()]
        
    tier_order = {'DARK_RED': 0, 'RED': 1, 'YELLOW': 2, 'GREEN': 3, 'OFF_SEASON': 4}
    df['sort_order'] = df['risk_tier'].map(tier_order).fillna(5)
    df = df.sort_values(by=['sort_order', 'overflow_mt', 'utilization_pct'], ascending=[True, False, False])
    
    results = []
    for _, row in df.iterrows():
        reasons = []
        if pd.notna(row.get('risk_reasons_json')):
            try:
                reasons = json.loads(row['risk_reasons_json'])
            except Exception:
                reasons = []
        results.append(DPCBase(
            dpc_id=str(row['dpc_id']),
            dpc_name=row.get('name') or str(row['dpc_id']),
            latitude=float(row['latitude']) if pd.notna(row.get('latitude')) else None,
            longitude=float(row['longitude']) if pd.notna(row.get('longitude')) else None,
            block_panchayat_union=row.get('block'),
            village=row.get('village'),
            capacity_mt=float(row['capacity_mt']) if pd.notna(row.get('capacity_mt')) else 100.0,
            current_stock_mt=float(row['current_stock_mt']) if pd.notna(row.get('current_stock_mt')) else 0.0,
            expected_arrival_1d_mt=float(row['expected_arrival_1d_mt']) if pd.notna(row.get('expected_arrival_1d_mt')) else 0.0,
            expected_arrival_3d_mt=float(row['expected_arrival_3d_mt']) if pd.notna(row.get('expected_arrival_3d_mt')) else 0.0,
            expected_arrival_7d_mt=float(row['expected_arrival_7d_mt']) if pd.notna(row.get('expected_arrival_7d_mt')) else 0.0,
            estimated_outflow_3d_mt=float(row['estimated_outflow_3d_mt']) if pd.notna(row.get('estimated_outflow_3d_mt')) else 0.0,
            projected_stock_mt=float(row['projected_stock_mt']) if pd.notna(row.get('projected_stock_mt')) else 0.0,
            utilization_pct=float(row['utilization_pct']) if pd.notna(row.get('utilization_pct')) else 0.0,
            overflow_mt=float(row['overflow_mt']) if pd.notna(row.get('overflow_mt')) else 0.0,
            risk_tier=str(row['risk_tier']),
            risk_reasons=reasons,
            arrival_trend=str(row.get('arrival_trend', 'Stable')),
            arrival_surge_flag=bool(row.get('arrival_surge_flag', False)),
            flood_exposure_pct=float(row['flood_exposure_pct']) if pd.notna(row.get('flood_exposure_pct')) else 0.0,
            rainfall_7d_mm=float(row['rainfall_7d_mm']) if pd.notna(row.get('rainfall_7d_mm')) else 0.0,
            access_disrupted=bool(row.get('access_disrupted', False)),
            is_active_season=bool(row.get('is_active_season', True)),
            outflow_assumption_note=str(row.get('outflow_assumption_note', '')),
            lstm_expected_arrival_1d_mt=float(row.get('lstm_expected_arrival_1d_mt', 0.0)) if pd.notna(row.get('lstm_expected_arrival_1d_mt')) else 0.0,
            lstm_expected_arrival_3d_mt=float(row.get('lstm_expected_arrival_3d_mt', 0.0)) if pd.notna(row.get('lstm_expected_arrival_3d_mt')) else 0.0,
            lstm_expected_arrival_7d_mt=float(row.get('lstm_expected_arrival_7d_mt', 0.0)) if pd.notna(row.get('lstm_expected_arrival_7d_mt')) else 0.0,
            lstm_projected_stock_mt=float(row.get('lstm_projected_stock_mt', 0.0)) if pd.notna(row.get('lstm_projected_stock_mt')) else 0.0,
            lstm_utilization_pct=float(row.get('lstm_utilization_pct', 0.0)) if pd.notna(row.get('lstm_utilization_pct')) else 0.0,
            lstm_overflow_mt=float(row.get('lstm_overflow_mt', 0.0)) if pd.notna(row.get('lstm_overflow_mt')) else 0.0,
            lstm_risk_tier=str(row.get('lstm_risk_tier', 'GREEN')),
            lstm_risk_reasons=json.loads(row.get('lstm_risk_reasons_json', '[]')) if pd.notna(row.get('lstm_risk_reasons_json')) else [],
            baseline_expected_arrival_1d_mt=float(row.get('baseline_expected_arrival_1d_mt', 0.0)) if pd.notna(row.get('baseline_expected_arrival_1d_mt')) else 0.0,
            baseline_expected_arrival_3d_mt=float(row.get('baseline_expected_arrival_3d_mt', 0.0)) if pd.notna(row.get('baseline_expected_arrival_3d_mt')) else 0.0,
            baseline_expected_arrival_7d_mt=float(row.get('baseline_expected_arrival_7d_mt', 0.0)) if pd.notna(row.get('baseline_expected_arrival_7d_mt')) else 0.0,
            baseline_projected_stock_mt=float(row.get('baseline_projected_stock_mt', 0.0)) if pd.notna(row.get('baseline_projected_stock_mt')) else 0.0,
            baseline_utilization_pct=float(row.get('baseline_utilization_pct', 0.0)) if pd.notna(row.get('baseline_utilization_pct')) else 0.0,
            baseline_overflow_mt=float(row.get('baseline_overflow_mt', 0.0)) if pd.notna(row.get('baseline_overflow_mt')) else 0.0,
            baseline_risk_tier=str(row.get('baseline_risk_tier', 'GREEN')),
            baseline_risk_reasons=json.loads(row.get('baseline_risk_reasons_json', '[]')) if pd.notna(row.get('baseline_risk_reasons_json')) else []
        ))
    return results

@router.get("/{dpc_id}", response_model=DPCBase)
def get_dpc(dpc_id: str, target_date: Optional[str] = Query('2025-11-29'), db: Session = Depends(get_db)):
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    query = f"SELECT * FROM dpc_risk_scores WHERE dpc_id = '{dpc_id}' AND date = '{target_date}'"
    df = pd.read_sql_query(query, conn)
    if df.empty:
        # Fallback to any date for this DPC
        df = pd.read_sql_query(f"SELECT * FROM dpc_risk_scores WHERE dpc_id = '{dpc_id}' ORDER BY date DESC LIMIT 1", conn)
    conn.close()
    
    if df.empty:
        raise HTTPException(status_code=404, detail="DPC not found")
        
    row = df.iloc[0]
    reasons = []
    if pd.notna(row.get('risk_reasons_json')):
        try:
            reasons = json.loads(row['risk_reasons_json'])
        except Exception:
            reasons = []
            
    return DPCBase(
        dpc_id=str(row['dpc_id']),
        dpc_name=row.get('name') or str(row['dpc_id']),
        latitude=float(row['latitude']) if pd.notna(row.get('latitude')) else None,
        longitude=float(row['longitude']) if pd.notna(row.get('longitude')) else None,
        block_panchayat_union=row.get('block'),
        village=row.get('village'),
        capacity_mt=float(row['capacity_mt']) if pd.notna(row.get('capacity_mt')) else 100.0,
        current_stock_mt=float(row['current_stock_mt']) if pd.notna(row.get('current_stock_mt')) else 0.0,
        expected_arrival_1d_mt=float(row['expected_arrival_1d_mt']) if pd.notna(row.get('expected_arrival_1d_mt')) else 0.0,
        expected_arrival_3d_mt=float(row['expected_arrival_3d_mt']) if pd.notna(row.get('expected_arrival_3d_mt')) else 0.0,
        expected_arrival_7d_mt=float(row['expected_arrival_7d_mt']) if pd.notna(row.get('expected_arrival_7d_mt')) else 0.0,
        estimated_outflow_3d_mt=float(row['estimated_outflow_3d_mt']) if pd.notna(row.get('estimated_outflow_3d_mt')) else 0.0,
        projected_stock_mt=float(row['projected_stock_mt']) if pd.notna(row.get('projected_stock_mt')) else 0.0,
        utilization_pct=float(row['utilization_pct']) if pd.notna(row.get('utilization_pct')) else 0.0,
        overflow_mt=float(row['overflow_mt']) if pd.notna(row.get('overflow_mt')) else 0.0,
        risk_tier=str(row['risk_tier']),
        risk_reasons=reasons,
        arrival_trend=str(row.get('arrival_trend', 'Stable')),
        arrival_surge_flag=bool(row.get('arrival_surge_flag', False)),
        flood_exposure_pct=float(row['flood_exposure_pct']) if pd.notna(row.get('flood_exposure_pct')) else 0.0,
        rainfall_7d_mm=float(row['rainfall_7d_mm']) if pd.notna(row.get('rainfall_7d_mm')) else 0.0,
        access_disrupted=bool(row.get('access_disrupted', False)),
        is_active_season=bool(row.get('is_active_season', True)),
        outflow_assumption_note=str(row.get('outflow_assumption_note', '')),
        lstm_expected_arrival_1d_mt=float(row.get('lstm_expected_arrival_1d_mt', 0.0)) if pd.notna(row.get('lstm_expected_arrival_1d_mt')) else 0.0,
        lstm_expected_arrival_3d_mt=float(row.get('lstm_expected_arrival_3d_mt', 0.0)) if pd.notna(row.get('lstm_expected_arrival_3d_mt')) else 0.0,
        lstm_expected_arrival_7d_mt=float(row.get('lstm_expected_arrival_7d_mt', 0.0)) if pd.notna(row.get('lstm_expected_arrival_7d_mt')) else 0.0,
        lstm_projected_stock_mt=float(row.get('lstm_projected_stock_mt', 0.0)) if pd.notna(row.get('lstm_projected_stock_mt')) else 0.0,
        lstm_utilization_pct=float(row.get('lstm_utilization_pct', 0.0)) if pd.notna(row.get('lstm_utilization_pct')) else 0.0,
        lstm_overflow_mt=float(row.get('lstm_overflow_mt', 0.0)) if pd.notna(row.get('lstm_overflow_mt')) else 0.0,
        lstm_risk_tier=str(row.get('lstm_risk_tier', 'GREEN')),
        lstm_risk_reasons=json.loads(row.get('lstm_risk_reasons_json', '[]')) if pd.notna(row.get('lstm_risk_reasons_json')) else [],
        baseline_expected_arrival_1d_mt=float(row.get('baseline_expected_arrival_1d_mt', 0.0)) if pd.notna(row.get('baseline_expected_arrival_1d_mt')) else 0.0,
        baseline_expected_arrival_3d_mt=float(row.get('baseline_expected_arrival_3d_mt', 0.0)) if pd.notna(row.get('baseline_expected_arrival_3d_mt')) else 0.0,
        baseline_expected_arrival_7d_mt=float(row.get('baseline_expected_arrival_7d_mt', 0.0)) if pd.notna(row.get('baseline_expected_arrival_7d_mt')) else 0.0,
        baseline_projected_stock_mt=float(row.get('baseline_projected_stock_mt', 0.0)) if pd.notna(row.get('baseline_projected_stock_mt')) else 0.0,
        baseline_utilization_pct=float(row.get('baseline_utilization_pct', 0.0)) if pd.notna(row.get('baseline_utilization_pct')) else 0.0,
        baseline_overflow_mt=float(row.get('baseline_overflow_mt', 0.0)) if pd.notna(row.get('baseline_overflow_mt')) else 0.0,
        baseline_risk_tier=str(row.get('baseline_risk_tier', 'GREEN')),
        baseline_risk_reasons=json.loads(row.get('baseline_risk_reasons_json', '[]')) if pd.notna(row.get('baseline_risk_reasons_json')) else []
    )
