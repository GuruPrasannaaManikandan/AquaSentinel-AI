import os
import json
import joblib
import pandas as pd
import numpy as np

class DeploymentModelLoader:
    """
    Utility to load and run inference on validated DEPLOYMENT_CANDIDATE models.
    Rejects INVALIDATED models and validates features schemas.
    """
    def __init__(self, workspace_dir=None):
        if workspace_dir is None:
            # Default to the capstone project root directory (two levels up from src/models)
            workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.workspace_dir = workspace_dir
        self.manifest_path = os.path.join(workspace_dir, "models", "deployment", "model_manifest.json")
        self.registry_path = os.path.join(workspace_dir, "models", "model_registry.json")
        
        self.manifest = self._load_json(self.manifest_path)
        self.registry = self._load_json(self.registry_path)
        self.models = {}

    def _load_json(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required configuration file not found at: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_model(self, key):
        """
        Loads the active model artifact specified by the manifest key.
        Checks the registry to verify audit integrity and status. Rejects invalid models.
        """
        if key not in self.manifest["models"]:
            raise ValueError(f"Model key '{key}' is not defined in the model manifest.")

        manifest_entry = self.manifest["models"][key]
        model_id = manifest_entry["model_id"]
        version = manifest_entry["version"]

        # Search for model entry in the model registry
        registry_entries = self.registry.get("models", [])
        registry_entry = None
        for entry in registry_entries:
            if entry.get("model_id") == model_id:
                registry_entry = entry
                break

        if not registry_entry:
            raise ValueError(f"Model ID '{model_id}' found in manifest is missing from registry.")

        # Validate status and audit verification
        status = registry_entry.get("status")
        audit_status = registry_entry.get("audit_status")

        if status == "INVALIDATED" or audit_status == "FAILED_PHASE45_INTEGRITY_AUDIT":
            raise PermissionError(f"Security Warning: Attempted to load INVALIDATED model '{model_id}' (Audit status: {audit_status}). Loading blocked.")

        if status != "DEPLOYMENT_CANDIDATE":
            raise ValueError(f"Model '{model_id}' is not marked as DEPLOYMENT_CANDIDATE in registry (Status: {status}).")

        if audit_status != "VERIFIED_AFTER_PHASE45":
            raise ValueError(f"Model '{model_id}' failed audit verification check (Audit status: {audit_status}).")

        # Verify model version matches manifest
        if manifest_entry.get("version") != "3.0.0":
            raise ValueError(f"Model version mismatch or invalid: expected version {version}")

        # Resolve artifact absolute path
        artifact_path = os.path.join(self.workspace_dir, manifest_entry["artifact_path"])
        if not os.path.exists(artifact_path):
            raise FileNotFoundError(f"Model artifact file not found at: {artifact_path}")

        # Ensure dependencies (e.g. custom preprocessing classes) are bound correctly
        from src.data.preprocessing import GroupMedianImputer, DepthImputer
        import sys
        sys.modules['__main__'].GroupMedianImputer = GroupMedianImputer
        sys.modules['__main__'].DepthImputer = DepthImputer

        # Load joblib file
        model_pipeline = joblib.load(artifact_path)

        self.models[key] = {
            "pipeline": model_pipeline,
            "manifest_entry": manifest_entry,
            "registry_entry": registry_entry
        }
        return model_pipeline

    def predict(self, key, X):
        """
        Runs model prediction on the input data X.
        Validates schemas, reorders features, runs inference, and formats the output payload.
        """
        if key not in self.models:
            self.load_model(key)

        model_info = self.models[key]
        pipeline = model_info["pipeline"]
        manifest_entry = model_info["manifest_entry"]
        expected_features = manifest_entry["expected_features"]

        if not isinstance(X, pd.DataFrame):
            raise TypeError("Input features must be provided as a pandas DataFrame.")

        # Schema Validation
        missing_features = [col for col in expected_features if col not in X.columns]
        if missing_features:
            raise ValueError(f"Input data is missing expected columns: {missing_features}")

        # Reorder columns to match the model training feature schema exactly
        X_aligned = X[expected_features].copy()

        # Run model inference
        raw_preds = pipeline.predict(X_aligned)
        raw_probs = pipeline.predict_proba(X_aligned)

        # For single row or multiple rows, we construct the payload.
        # As per the inference contract, we support single row prediction.
        # Let's handle row-wise prediction packaging.
        results = []
        classes = pipeline.classes_
        dangerous_classes = manifest_entry["dangerous_classes"]

        for pred, prob_vector in zip(raw_preds, raw_probs):
            # Format probabilities dictionary preserving class ordering
            probs_dict = {}
            for cls, prob in zip(classes, prob_vector):
                cls_key = int(cls) if isinstance(cls, (int, np.integer)) else str(cls)
                probs_dict[cls_key] = float(prob)

            confidence = float(np.max(prob_vector))
            pred_formatted = int(pred) if isinstance(pred, (int, np.integer)) else str(pred)
            dangerous_detected = pred_formatted in dangerous_classes

            payload = {
                "model_id": manifest_entry["model_id"],
                "model_version": manifest_entry["version"],
                "prediction": pred_formatted,
                "probabilities": probs_dict,
                "confidence": confidence,
                "dangerous_detected": bool(dangerous_detected)
            }
            results.append(payload)

        # Return single dictionary if input has 1 row, else return list of dictionaries
        return results[0] if len(results) == 1 else results
