from pydantic import BaseModel
from typing import Optional, List, Any

class RiskZone(BaseModel):
    dpc_id: str
    dpc_name: Optional[str] = None
    block_panchayat_union: Optional[str] = None
    village: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    capacity_mt: Optional[float] = None
    current_stock_mt: Optional[float] = None
    expected_arrival_1d_mt: Optional[float] = None
    expected_arrival_3d_mt: Optional[float] = None
    expected_arrival_7d_mt: Optional[float] = None
    estimated_outflow_3d_mt: Optional[float] = None
    projected_stock_mt: Optional[float] = None
    utilization_pct: Optional[float] = None
    overflow_mt: Optional[float] = None
    risk_tier: Optional[str] = None
    risk_reasons: Optional[List[str]] = []
    arrival_trend: Optional[str] = None
    arrival_surge_flag: Optional[bool] = None
    flood_exposure_pct: Optional[float] = None
    rainfall_7d_mm: Optional[float] = None
    access_disrupted: Optional[bool] = None
    is_active_season: Optional[bool] = None
    outflow_assumption_note: Optional[str] = None

    class Config:
        from_attributes = True

class RiskSummary(BaseModel):
    total_dpcs: int
    active_dpcs: int
    green_count: int
    yellow_count: int
    red_count: int
    dark_red_count: int
    off_season_count: int
    average_utilization_pct: float
    total_projected_overflow_mt: float
    total_expected_7d_arrivals_mt: float
    centres_with_overflow: int
    centres_with_surges: int
    outflow_assumption: str
