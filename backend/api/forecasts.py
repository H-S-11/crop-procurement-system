import json
import sqlite3
import pandas as pd
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db, DEFAULT_DB_PATH
from schemas.forecast import ForecastResponse, HistoryPoint

router = APIRouter(prefix="/dpcs", tags=["Forecasts"])

@router.get("/{dpc_id}/forecast", response_model=ForecastResponse)
def get_dpc_forecast(
    dpc_id: str,
    target_date: Optional[str] = Query('2025-11-29'),
    db: Session = Depends(get_db)
):
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    query = f"""
    SELECT r.*, f.surge_threshold_mt, f.rainfall_7d
    FROM dpc_risk_scores r
    LEFT JOIN dpc_feature_store f ON r.dpc_id = f.dpc_id AND r.date = f.date
    WHERE r.dpc_id = '{dpc_id}' AND r.date = '{target_date}'
    """
    df = pd.read_sql_query(query, conn)
    if df.empty:
        df = pd.read_sql_query(f"SELECT * FROM dpc_risk_scores WHERE dpc_id = '{dpc_id}' ORDER BY date DESC LIMIT 1", conn)
    conn.close()
    
    if df.empty:
        raise HTTPException(status_code=404, detail="DPC forecast not found")
        
    row = df.iloc[0]
    reasons = []
    if pd.notna(row.get('risk_reasons_json')):
        try:
            reasons = json.loads(row['risk_reasons_json'])
        except Exception:
            reasons = []

    return ForecastResponse(
        date=str(row['date']),
        dpc_id=str(row['dpc_id']),
        dpc_name=row.get('name') or str(row['dpc_id']),
        expected_arrival_1d_mt=float(row.get('expected_arrival_1d_mt') or 0.0),
        expected_arrival_3d_mt=float(row.get('expected_arrival_3d_mt') or 0.0),
        expected_arrival_7d_mt=float(row.get('expected_arrival_7d_mt') or 0.0),
        arrival_trend=str(row.get('arrival_trend') or 'Stable'),
        arrival_surge_flag=bool(row.get('arrival_surge_flag') or False),
        surge_threshold_mt=float(row.get('surge_threshold_mt') or 25.0),
        current_stock_mt=float(row.get('current_stock_mt') or 0.0),
        capacity_mt=float(row.get('capacity_mt') or 100.0),
        estimated_outflow_3d_mt=float(row.get('estimated_outflow_3d_mt') or 0.0),
        projected_stock_mt=float(row.get('projected_stock_mt') or 0.0),
        utilization_pct=float(row.get('utilization_pct') or 0.0),
        overflow_mt=float(row.get('overflow_mt') or 0.0),
        flood_exposure_pct=float(row.get('flood_exposure_pct') or 0.0),
        flood_methodology_note="Derived from Sentinel-1 SAR 10m water classification mask within 500m buffer. Indicates observed standing water exposure, not a future flood predictive model.",
        rainfall_7d_mm=float(row.get('rainfall_7d_mm') or 0.0),
        moisture_status="Elevated Weather Risk Proxy" if float(row.get('rainfall_7d_mm') or 0) > 40 else "Normal Proxy",
        moisture_proxy_note="Field moisture readings absent. Metric is an environmental proxy computed from 7-day rainfall and SAR flood proximity.",
        access_status="Road Closure Flagged in Corridor" if bool(row.get('access_disrupted')) else "Roads Open",
        access_proxy_note="Network route disruption model unavailable. Based on radial proximity to recorded road closure events and OSM major roads.",
        risk_tier=str(row.get('risk_tier') or 'GREEN'),
        risk_reasons=reasons,
        outflow_assumption_note=str(row.get('outflow_assumption_note') or "Estimated outflow modeled at 10% capacity/day (TNCSC Godown B5 unlinked to DPCs)"),
        lstm_expected_arrival_1d_mt=float(row.get('lstm_expected_arrival_1d_mt') or 0.0),
        lstm_expected_arrival_3d_mt=float(row.get('lstm_expected_arrival_3d_mt') or 0.0),
        lstm_expected_arrival_7d_mt=float(row.get('lstm_expected_arrival_7d_mt') or 0.0),
        lstm_projected_stock_mt=float(row.get('lstm_projected_stock_mt') or 0.0),
        lstm_utilization_pct=float(row.get('lstm_utilization_pct') or 0.0),
        lstm_overflow_mt=float(row.get('lstm_overflow_mt') or 0.0),
        lstm_risk_tier=str(row.get('lstm_risk_tier') or 'GREEN'),
        lstm_risk_reasons=json.loads(row.get('lstm_risk_reasons_json') or '[]') if pd.notna(row.get('lstm_risk_reasons_json')) else [],
        baseline_expected_arrival_1d_mt=float(row.get('baseline_expected_arrival_1d_mt') or 0.0),
        baseline_expected_arrival_3d_mt=float(row.get('baseline_expected_arrival_3d_mt') or 0.0),
        baseline_expected_arrival_7d_mt=float(row.get('baseline_expected_arrival_7d_mt') or 0.0),
        baseline_projected_stock_mt=float(row.get('baseline_projected_stock_mt') or 0.0),
        baseline_utilization_pct=float(row.get('baseline_utilization_pct') or 0.0),
        baseline_overflow_mt=float(row.get('baseline_overflow_mt') or 0.0),
        baseline_risk_tier=str(row.get('baseline_risk_tier') or 'GREEN'),
        baseline_risk_reasons=json.loads(row.get('baseline_risk_reasons_json') or '[]') if pd.notna(row.get('baseline_risk_reasons_json')) else []
    )

@router.get("/{dpc_id}/history", response_model=List[HistoryPoint])
def get_dpc_history(
    dpc_id: str,
    start_date: Optional[str] = '2025-09-01',
    end_date: Optional[str] = '2026-04-20',
    db: Session = Depends(get_db)
):
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    query = f"""
    SELECT 
        f.date,
        f.arrival_mt as actual_arrivals,
        r.expected_arrival_1d_mt as forecast_arrivals,
        r.baseline_expected_arrival_1d_mt as baseline_forecast_arrivals,
        r.lstm_expected_arrival_1d_mt as lstm_forecast_arrivals,
        r.projected_stock_mt,
        f.rainfall_1d as rainfall,
        f.capacity
    FROM dpc_feature_store f
    LEFT JOIN dpc_risk_scores r ON f.dpc_id = r.dpc_id AND f.date = r.date
    WHERE f.dpc_id = '{dpc_id}'
      AND f.date >= '{start_date}'
      AND f.date <= '{end_date}'
    ORDER BY f.date ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return []
        
    points = []
    for _, row in df.iterrows():
        points.append(HistoryPoint(
            date=str(row['date']),
            actual_arrivals=float(row['actual_arrivals']) if pd.notna(row['actual_arrivals']) else None,
            forecast_arrivals=float(row['forecast_arrivals']) if pd.notna(row['forecast_arrivals']) else None,
            baseline_forecast_arrivals=float(row['baseline_forecast_arrivals']) if pd.notna(row.get('baseline_forecast_arrivals')) else None,
            lstm_forecast_arrivals=float(row['lstm_forecast_arrivals']) if pd.notna(row.get('lstm_forecast_arrivals')) else None,
            projected_stock=float(row['projected_stock_mt']) if pd.notna(row['projected_stock_mt']) else None,
            rainfall=float(row['rainfall']) if pd.notna(row['rainfall']) else 0.0,
            capacity=float(row['capacity']) if pd.notna(row['capacity']) else 100.0
        ))
    return points
