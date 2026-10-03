import os

class AccessModel:
    def __init__(self):
        self.features = ['rainfall_7d', 'flood_exposure', 'nearest_road_dist', 'major_road_dist']
        self.target = 'access_disruption'

    def train_and_evaluate(self, df):
        print("Access Disruption Forecast: Target data unavailable or insufficient for reliable classification. Documenting limitation.")
        return {
            "model_name": "Access Disruption Model",
            "target": self.target,
            "training_period": "N/A",
            "validation_period": "N/A",
            "test_period": "N/A",
            "training_rows": 0,
            "features": self.features,
            "baseline_metrics": {"precision": None, "recall": None, "f1": None, "roc_auc": None},
            "model_metrics": {"precision": None, "recall": None, "f1": None, "roc_auc": None},
            "note": "TARGET UNAVAILABLE: DPC-to-road network graph and historical disruption ground-truth labels are unavailable. Proximity flags are displayed in the dashboard as an operational proxy only."
        }
