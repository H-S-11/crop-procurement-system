from pydantic import BaseModel
from typing import Optional, List

class ForecastResponse(BaseModel):
    date: str
    dpc_id: str
    dpc_name: str
    expected_arrival_1d_mt: float
    expected_arrival_3d_mt: float
    expected_arrival_7d_mt: float
    arrival_trend: str
    arrival_surge_flag: bool
    surge_threshold_mt: float
    current_stock_mt: float
    capacity_mt: float
    estimated_outflow_3d_mt: float
    projected_stock_mt: float
    utilization_pct: float
    overflow_mt: float
    flood_exposure_pct: float
    flood_methodology_note: str
    rainfall_7d_mm: float
    moisture_status: str
    moisture_proxy_note: str
    access_status: str
    access_proxy_note: str
    risk_tier: str
    risk_reasons: List[str]
    outflow_assumption_note: str

    lstm_expected_arrival_1d_mt: float = 0.0
    lstm_expected_arrival_3d_mt: float = 0.0
    lstm_expected_arrival_7d_mt: float = 0.0
    lstm_projected_stock_mt: float = 0.0
    lstm_utilization_pct: float = 0.0
    lstm_overflow_mt: float = 0.0
    lstm_risk_tier: str = 'GREEN'
    lstm_risk_reasons: List[str] = []
    
    baseline_expected_arrival_1d_mt: float = 0.0
    baseline_expected_arrival_3d_mt: float = 0.0
    baseline_expected_arrival_7d_mt: float = 0.0
    baseline_projected_stock_mt: float = 0.0
    baseline_utilization_pct: float = 0.0
    baseline_overflow_mt: float = 0.0
    baseline_risk_tier: str = 'GREEN'
    baseline_risk_reasons: List[str] = []

class HistoryPoint(BaseModel):
    date: str
    actual_arrivals: Optional[float] = None
    forecast_arrivals: Optional[float] = None
    baseline_forecast_arrivals: Optional[float] = None
    lstm_forecast_arrivals: Optional[float] = None
    projected_stock: Optional[float] = None
    rainfall: Optional[float] = None
    capacity: Optional[float] = None

class HistoryResponse(BaseModel):
    dpc_id: str
    series: List[HistoryPoint]
