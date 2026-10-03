import json
import sqlite3
import pandas as pd
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db, DEFAULT_DB_PATH
from schemas.risk import RiskZone, RiskSummary

router = APIRouter(tags=["Risk"])

@router.get("/priority-zones", response_model=List[RiskZone])
def get_priority_zones(
    risk_tier: Optional[str] = None,
    block: Optional[str] = None,
    target_date: Optional[str] = Query('2025-11-29', description="Format: YYYY-MM-DD"),
    min_utilization: Optional[float] = None,
    overflow_only: Optional[bool] = False,
    active_only: Optional[bool] = True,
    limit: int = Query(500, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    
    # Query risk scores for target date
    query = f"""
    SELECT * FROM dpc_risk_scores
    WHERE date = '{target_date}'
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        # Fallback to max date if target_date has no records
        conn = sqlite3.connect(DEFAULT_DB_PATH)
        max_date = pd.read_sql_query("SELECT MAX(date) FROM dpc_risk_scores", conn).iloc[0, 0]
        df = pd.read_sql_query(f"SELECT * FROM dpc_risk_scores WHERE date = '{max_date}'", conn)
        conn.close()
        
    if active_only:
        df = df[df['is_active_season'] == 1]
    if risk_tier and risk_tier.upper() != 'ALL':
        df = df[df['risk_tier'] == risk_tier.upper()]
    if block and block != '':
        df = df[df['block'] == block]
    if min_utilization is not None:
        df = df[df['utilization_pct'] >= min_utilization]
    if overflow_only:
        df = df[df['overflow_mt'] > 0]
        
    # Sort order: DARK_RED first, then RED, then YELLOW, then GREEN, then highest overflow
    tier_order = {'DARK_RED': 0, 'RED': 1, 'YELLOW': 2, 'GREEN': 3, 'OFF_SEASON': 4}
    df['sort_order'] = df['risk_tier'].map(tier_order).fillna(5)
    df = df.sort_values(by=['sort_order', 'overflow_mt', 'utilization_pct'], ascending=[True, False, False])
    
    if limit:
        df = df.head(limit)
        
    records = []
    for _, row in df.iterrows():
        reasons = []
        if pd.notna(row.get('risk_reasons_json')):
            try:
                reasons = json.loads(row['risk_reasons_json'])
            except Exception:
                reasons = []
                
        records.append(RiskZone(
            dpc_id=str(row['dpc_id']),
            dpc_name=row.get('name') or str(row['dpc_id']),
            block_panchayat_union=row.get('block'),
            village=row.get('village'),
            latitude=float(row['latitude']) if pd.notna(row.get('latitude')) else None,
            longitude=float(row['longitude']) if pd.notna(row.get('longitude')) else None,
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
            outflow_assumption_note=str(row.get('outflow_assumption_note', ''))
        ))
        
    return records

@router.get("/risk-summary", response_model=RiskSummary)
def get_risk_summary(
    target_date: Optional[str] = Query('2025-11-29', description="Format: YYYY-MM-DD"),
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
        
    active = df[df['is_active_season'] == 1]
    
    return RiskSummary(
        total_dpcs=len(df),
        active_dpcs=len(active),
        green_count=int((active['risk_tier'] == 'GREEN').sum()),
        yellow_count=int((active['risk_tier'] == 'YELLOW').sum()),
        red_count=int((active['risk_tier'] == 'RED').sum()),
        dark_red_count=int((active['risk_tier'] == 'DARK_RED').sum()),
        off_season_count=int((df['is_active_season'] == 0).sum()),
        average_utilization_pct=float(active['utilization_pct'].mean() if not active.empty else 0.0),
        total_projected_overflow_mt=float(active['overflow_mt'].sum() if not active.empty else 0.0),
        total_expected_7d_arrivals_mt=float(active['expected_arrival_7d_mt'].sum() if not active.empty else 0.0),
        centres_with_overflow=int((active['overflow_mt'] > 0).sum()),
        centres_with_surges=int((active['arrival_surge_flag'] == 1).sum()),
        outflow_assumption="Modeled at 10% capacity/day (TNCSC Godown B5 ledger is unlinked to individual DPCs)"
    )
