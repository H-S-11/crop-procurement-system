import os
import json
from typing import Dict, Any, List
from fastapi import APIRouter

router = APIRouter(prefix="/validation", tags=["Validation"])

@router.get("/metrics")
def get_model_metrics() -> List[Dict[str, Any]]:
    metrics_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'metrics.json')
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

@router.get("/summary")
def get_validation_summary() -> Dict[str, Any]:
    metrics = get_model_metrics()
    return {
        "status": "VALIDATED",
        "methodology": "Strict chronological temporal split (70% train, 15% validation, 15% test). Zero look-ahead bias.",
        "models": metrics
    }
