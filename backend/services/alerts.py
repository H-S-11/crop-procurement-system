import json
import os
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from db_models import Alert, DPCFeatureStore, DPCRiskScore
from database import get_db

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'alert_thresholds.json')

def load_thresholds():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def generate_alerts_for_date(db: Session, target_date: str):
    thresholds = load_thresholds()
    
    features = db.query(DPCFeatureStore).filter(DPCFeatureStore.date == target_date).all()
    risks = db.query(DPCRiskScore).filter(DPCRiskScore.date == target_date).all()
    
    risk_map = {r.dpc_id: r for r in risks}
    
    current_alerts = []
    
    for feat in features:
        dpc_id = feat.dpc_id
        dpc_name = feat.name or dpc_id
        risk = risk_map.get(dpc_id)
        
        # 1. HIGH_RISK_DPC
        if risk and risk.composite_risk_score is not None:
            if risk.composite_risk_score >= thresholds["critical_risk_score"]:
                current_alerts.append(_create_alert(
                    dpc_id, dpc_name, target_date, "HIGH_RISK_DPC", "CRITICAL",
                    risk.composite_risk_score, thresholds["critical_risk_score"],
                    "Risk score reached CRITICAL level", "Composite Risk Model"
                ))
            elif risk.composite_risk_score >= thresholds["high_risk_score"]:
                current_alerts.append(_create_alert(
                    dpc_id, dpc_name, target_date, "HIGH_RISK_DPC", "HIGH",
                    risk.composite_risk_score, thresholds["high_risk_score"],
                    "Risk score reached HIGH level", "Composite Risk Model"
                ))
                
        # 2. STORAGE_SATURATION
        if risk and risk.capacity_utilization is not None:
            util_pct = risk.capacity_utilization * 100
            if util_pct >= thresholds["storage_saturation_pct"]:
                current_alerts.append(_create_alert(
                    dpc_id, dpc_name, target_date, "STORAGE_SATURATION", "HIGH",
                    util_pct, thresholds["storage_saturation_pct"],
                    f"Storage utilization at {util_pct:.1f}% (Fallback: 10% outflow assumption)",
                    "Derived Storage Model"
                ))
                
        # 3. FLOOD_EXPOSURE
        if feat.flood_exposure and feat.flood_exposure > 0:
            current_alerts.append(_create_alert(
                dpc_id, dpc_name, target_date, "FLOOD_EXPOSURE", "HIGH",
                feat.flood_exposure, 0,
                "Flood exposure detected in vicinity",
                "Derived (Classified Flood Extent)"
            ))
            
        # 4. HEAVY_RAINFALL
        if feat.rainfall_1d and feat.rainfall_1d >= thresholds["heavy_rainfall_1d_mm"]:
            current_alerts.append(_create_alert(
                dpc_id, dpc_name, target_date, "HEAVY_RAINFALL", "MODERATE",
                feat.rainfall_1d, thresholds["heavy_rainfall_1d_mm"],
                f"Heavy rainfall observed: {feat.rainfall_1d}mm",
                "Observed Rainfall"
            ))

    # Deduplication and resolution
    _merge_alerts(db, target_date, current_alerts)

def _create_alert(dpc_id, dpc_name, date, alert_type, severity, val, threshold, explanation, provenance):
    return {
        "dpc_id": dpc_id,
        "dpc_name": dpc_name,
        "alert_type": alert_type,
        "severity": severity,
        "event_date": date,
        "trigger_value": val,
        "threshold": threshold,
        "explanation": explanation,
        "provenance": provenance
    }

def _merge_alerts(db: Session, current_date: str, new_alerts: list):
    # Get all ACTIVE alerts
    active_db_alerts = db.query(Alert).filter(Alert.status == "ACTIVE").all()
    
    active_map = {(a.dpc_id, a.alert_type): a for a in active_db_alerts}
    new_map = {(a["dpc_id"], a["alert_type"]): a for a in new_alerts}
    
    # Check existing active to see if resolved
    for key, db_alert in active_map.items():
        if key not in new_map:
            db_alert.status = "RESOLVED"
            db.add(db_alert)
            
    # Add or update active
    for key, new_a in new_map.items():
        if key in active_map:
            # Update values if needed, keep ACTIVE
            db_alert = active_map[key]
            db_alert.trigger_value = new_a["trigger_value"]
            db_alert.severity = new_a["severity"]
            db_alert.explanation = new_a["explanation"]
            db_alert.event_date = current_date # update last seen
            db.add(db_alert)
        else:
            # New alert
            alert = Alert(
                alert_id=str(uuid.uuid4()),
                dpc_id=new_a["dpc_id"],
                dpc_name=new_a["dpc_name"],
                alert_type=new_a["alert_type"],
                severity=new_a["severity"],
                status="ACTIVE",
                event_date=new_a["event_date"],
                trigger_value=new_a["trigger_value"],
                threshold=new_a["threshold"],
                explanation=new_a["explanation"],
                provenance=new_a["provenance"]
            )
            db.add(alert)
            
    db.commit()
