from pydantic import BaseModel
from typing import Optional, List

class DPCBase(BaseModel):
    dpc_id: str
    dpc_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    block_panchayat_union: Optional[str] = None
    village: Optional[str] = None
    capacity_mt: Optional[float] = 100.0
    current_stock_mt: Optional[float] = 0.0
    expected_arrival_1d_mt: Optional[float] = 0.0
    expected_arrival_3d_mt: Optional[float] = 0.0
    expected_arrival_7d_mt: Optional[float] = 0.0
    estimated_outflow_3d_mt: Optional[float] = 0.0
    projected_stock_mt: Optional[float] = 0.0
    utilization_pct: Optional[float] = 0.0
    overflow_mt: Optional[float] = 0.0
    risk_tier: Optional[str] = 'GREEN'
    risk_reasons: Optional[List[str]] = []
    
    lstm_expected_arrival_1d_mt: Optional[float] = 0.0
    lstm_expected_arrival_3d_mt: Optional[float] = 0.0
    lstm_expected_arrival_7d_mt: Optional[float] = 0.0
    lstm_projected_stock_mt: Optional[float] = 0.0
    lstm_utilization_pct: Optional[float] = 0.0
    lstm_overflow_mt: Optional[float] = 0.0
    lstm_risk_tier: Optional[str] = 'GREEN'
    lstm_risk_reasons: Optional[List[str]] = []
    
    baseline_expected_arrival_1d_mt: Optional[float] = 0.0
    baseline_expected_arrival_3d_mt: Optional[float] = 0.0
    baseline_expected_arrival_7d_mt: Optional[float] = 0.0
    baseline_projected_stock_mt: Optional[float] = 0.0
    baseline_utilization_pct: Optional[float] = 0.0
    baseline_overflow_mt: Optional[float] = 0.0
    baseline_risk_tier: Optional[str] = 'GREEN'
    baseline_risk_reasons: Optional[List[str]] = []
    arrival_trend: Optional[str] = 'Stable'
    arrival_surge_flag: Optional[bool] = False
    flood_exposure_pct: Optional[float] = 0.0
    rainfall_7d_mm: Optional[float] = 0.0
    access_disrupted: Optional[bool] = False
    is_active_season: Optional[bool] = True
    outflow_assumption_note: Optional[str] = ''
    suggested_alternatives: Optional[List[dict]] = []

    class Config:
        from_attributes = True
