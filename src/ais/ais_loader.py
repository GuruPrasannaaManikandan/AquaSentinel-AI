import os
import json
import joblib
import pandas as pd
import numpy as np

class AISLoader:
    """
    Model loader for Artificial Immune System (AIS) Negative Selection models.
    Validates schemas, applies dedicated preprocessing, and returns standardized payloads.
    """
    def __init__(self, workspace_dir=None):
        if workspace_dir is None:
            # Default to the capstone project root directory (two levels up from src/ais)
            workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.workspace_dir = workspace_dir
        self.registry_path = os.path.join(workspace_dir, "models", "ais", "ais_registry.json")
        self.registry = self._load_json(self.registry_path)
        self.active_models = {}

    def _load_json(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"AIS Registry not found at: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_model(self, key):
        """
        Loads the active AIS model specified by the key ('caml' or 'habsos').
        """
        # Find in registry
        registry_entry = None
        for entry in self.registry.get("models", []):
            if entry.get("model_id") == key or entry.get("dataset", "").lower().startswith(key):
                registry_entry = entry
                break

        if not registry_entry:
            raise ValueError(f"AIS model key/id '{key}' not found in registry.")

        # Validate status and audit verification
        status = registry_entry.get("status")
        audit_status = registry_entry.get("audit_status")

        if status == "INVALIDATED" or audit_status == "FAILED_PHASE45_INTEGRITY_AUDIT":
            raise PermissionError(f"Security Warning: Attempted to load INVALIDATED AIS model (Audit status: {audit_status}). Loading blocked.")

        artifact_path = os.path.join(self.workspace_dir, registry_entry["artifact_path"])
        if not os.path.exists(artifact_path):
            raise FileNotFoundError(f"AIS model artifact not found at: {artifact_path}")

        # Ensure custom classes are bindable
        from src.ais.preprocessing import AISPreprocessor
        from src.ais.negative_selection import NegativeSelectionAlgorithm
        import sys
        sys.modules['__main__'].AISPreprocessor = AISPreprocessor
        sys.modules['__main__'].NegativeSelectionAlgorithm = NegativeSelectionAlgorithm

        # Load the serialized joblib artifact
        artifact = joblib.load(artifact_path)
        
        self.active_models[key] = {
            "preprocessor": artifact["preprocessor"],
            "model": artifact["model"],
            "registry_entry": registry_entry
        }
        return artifact["model"]

    def predict_anomaly(self, key, X, matching_radius=None):
        """
        Executes Negative Selection anomaly detection on input DataFrame X.
        """
        if key not in self.active_models:
            self.load_model(key)

        model_info = self.active_models[key]
        preprocessor = model_info["preprocessor"]
        model = model_info["model"]
        registry_entry = model_info["registry_entry"]
        expected_features = registry_entry["feature_schema"]

        if not isinstance(X, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame.")

        # Schema Validation
        missing = [f for f in expected_features if f not in X.columns]
        if missing:
            raise ValueError(f"Input is missing required features: {missing}")

        # Preprocess features (imputation and MinMax scaling)
        X_scaled = preprocessor.transform(X)

        # Run Negative Selection prediction
        is_anomaly, anomaly_scores, matched_counts, min_dists = model.predict_anomaly(X_scaled, matching_radius=matching_radius)

        # Format standardized output payloads
        results = []
        for i in range(len(X)):
            payload = {
                "is_anomaly": bool(is_anomaly[i]),
                "anomaly_score": float(anomaly_scores[i]),
                "matched_detector_count": int(matched_counts[i]),
                "nearest_detector_distance": float(min_dists[i]) if np.isfinite(min_dists[i]) else 999.0,
                "ais_version": registry_entry["version"]
            }
            results.append(payload)

        return results[0] if len(results) == 1 else results
