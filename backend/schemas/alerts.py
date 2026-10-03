from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class AlertBase(BaseModel):
    alert_id: str
    dpc_id: str
    dpc_name: str
    alert_type: str
    severity: str
    status: str
    event_date: str
    trigger_value: float
    threshold: float
    explanation: str
    contributing_factors: Optional[str] = None
    provenance: str

class AlertCreate(AlertBase):
    pass

class Alert(AlertBase):
    class Config:
        orm_mode = True

class AlertSummary(BaseModel):
    total_active: int
    high_count: int
    critical_count: int
    storage_count: int
    rainfall_count: int
    flood_count: int
    recently_resolved: int
