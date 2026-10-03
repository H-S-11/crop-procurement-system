import json
import os
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from database import SessionLocal
from db_models import DPCFeatureStore, DPCRiskScore

def run_hindcast(db: Session):
    damage_count = db.execute(text("SELECT count(*) FROM damage_incidents")).scalar()
    road_closure_count = db.execute(text("SELECT count(*) FROM road_closures")).scalar()
    
    total_events = damage_count + road_closure_count
    
    # Count events that have DPC linkage (for data quality reporting)
    matched_events = db.execute(text("SELECT count(*) FROM road_closures WHERE dpc_id IS NOT NULL")).scalar()
    matched_damage = db.execute(text("SELECT count(*) FROM damage_incidents WHERE dpc_id IS NOT NULL")).scalar()
    
    total_matched = matched_events + matched_damage

    # Check which risk models are actually trained and producing predictions
    # A model is "trained" if its risk score column has any non-zero values
    access_has_predictions = db.execute(
        text("SELECT COUNT(*) FROM dpc_risk_scores WHERE access_risk_score > 0")
    ).scalar() > 0
    
    damage_has_predictions = db.execute(
        text("SELECT COUNT(*) FROM dpc_risk_scores WHERE damage_risk_score > 0")
    ).scalar() > 0

    storage_has_predictions = db.execute(
        text("SELECT COUNT(*) FROM dpc_risk_scores WHERE storage_risk_score > 0")
    ).scalar() > 0

    # Build per-model validation status — only report real metrics if
    # both predictions AND ground truth events exist for that model
    model_statuses = {}

    if not access_has_predictions:
        model_statuses["access_disruption"] = {
            "status": "not_yet_validated",
            "reason": "Access disruption model has not produced non-zero predictions. "
                      "Cannot compute precision/recall without predictions to evaluate."
        }
    else:
        model_statuses["access_disruption"] = {
            "status": "pending_evaluation",
            "reason": "Model produces predictions but formal hindcast evaluation has not been run."
        }

    if not damage_has_predictions:
        model_statuses["damage_risk"] = {
            "status": "not_yet_validated",
            "reason": "Damage risk score is not yet wired to real data (currently hardcoded 0). "
                      "Cannot compute precision/recall without predictions to evaluate."
        }
    else:
        model_statuses["damage_risk"] = {
            "status": "pending_evaluation",
            "reason": "Model produces predictions but formal hindcast evaluation has not been run."
        }

    model_statuses["storage_saturation"] = {
        "status": "validated_partial" if storage_has_predictions else "not_yet_validated",
        "reason": "Storage simulation runs on arrival data. Validation limited by lack of "
                  "ground-truth DPC-level stock records (B5 is godown-level only)."
    }

    model_statuses["moisture_rejection"] = {
        "status": "not_yet_validated",
        "reason": "Moisture risk uses a proxy formula (rainfall + flood exposure), not a "
                  "trained classifier. No confusion matrix is applicable."
    }

    # Determine overall validation status
    trained_count = sum(1 for m in model_statuses.values() if m["status"] != "not_yet_validated")
    total_models = len(model_statuses)

    if trained_count == 0:
        overall_status = "NOT_VALIDATED — No risk models have produced real predictions yet"
    elif trained_count < total_models:
        overall_status = f"PARTIALLY_VALIDATED — {trained_count}/{total_models} models producing predictions"
    else:
        overall_status = "VALIDATED"

    results = {
        "evaluation_period": "2025-08-01 to 2026-01-31",
        "num_dpcs": db.query(DPCFeatureStore.dpc_id).distinct().count(),
        "num_events": total_events,
        "matched_events": total_matched,
        "unmatched_events": total_events - total_matched,
        "metrics": {
            "binary_event_detection": None,
            "risk_ranking": None,
            "precision": None,
            "recall": None,
            "f1": None,
            "note": "Metrics are null because underlying risk models (access disruption, "
                    "damage) have not yet produced predictions. Real metrics will be "
                    "computed once models are trained and produce non-trivial outputs."
        },
        "model_statuses": model_statuses,
        "threshold_configuration": "default",
        "validation_status": overall_status,
        "limitations": [
            "Damage risk score is not yet wired to B10 incident data.",
            "Access disruption model has not been trained — B11 labels not yet constructed.",
            "Moisture risk uses a rainfall/flood proxy, not actual moisture measurements.",
            "Storage outflow uses a synthetic 10% daily decay assumption.",
            "Flood exposure is derived from classified SAR flood extent.",
            "Arrival Random Forest does not outperform the 7-day mean baseline.",
            "Validation metrics (precision, recall, F1) will only be populated once "
            "the underlying models produce real predictions to compare against events."
        ]
    }
    
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results.json'), 'w') as f:
        json.dump(results, f, indent=2)
        
    return results

if __name__ == "__main__":
    db = SessionLocal()
    run_hindcast(db)
    db.close()
