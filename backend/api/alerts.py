from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from database import get_db
from db_models import Alert
from schemas.alerts import Alert as AlertSchema, AlertSummary

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertSchema])
def get_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    dpc_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    query = db.query(Alert)
    
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if dpc_id:
        query = query.filter(Alert.dpc_id == dpc_id)
        
    return query.order_by(Alert.event_date.desc()).limit(limit).all()

@router.get("/summary", response_model=AlertSummary)
def get_alert_summary(db: Session = Depends(get_db)):
    active_alerts = db.query(Alert).filter(Alert.status == 'ACTIVE').all()
    
    total = len(active_alerts)
    high = sum(1 for a in active_alerts if a.severity == 'HIGH')
    crit = sum(1 for a in active_alerts if a.severity == 'CRITICAL')
    storage = sum(1 for a in active_alerts if a.alert_type == 'STORAGE_SATURATION')
    rainfall = sum(1 for a in active_alerts if a.alert_type == 'HEAVY_RAINFALL')
    flood = sum(1 for a in active_alerts if a.alert_type == 'FLOOD_EXPOSURE')
    
    resolved = db.query(Alert).filter(Alert.status == 'RESOLVED').count()
    
    return {
        "total_active": total,
        "high_count": high,
        "critical_count": crit,
        "storage_count": storage,
        "rainfall_count": rainfall,
        "flood_count": flood,
        "recently_resolved": resolved
    }

@router.get("/{alert_id}", response_model=AlertSchema)
def get_alert(alert_id: str, db: Session = Depends(get_db)):
    return db.query(Alert).filter(Alert.alert_id == alert_id).first()
