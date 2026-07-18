import os
import json
import numpy as np

class FusionEngine:
    """
    Transparent, deterministic, testable evidence-fusion engine.
    Combines supervised ML outputs and unsupervised AIS anomaly detection outputs
    into a final system state (NORMAL, WARNING, CRITICAL, UNKNOWN_ANOMALY).
    """
    def __init__(self, policy_path=None):
        if policy_path is None:
            # Default path relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            policy_path = os.path.join(base_dir, "config", "fusion_policy.json")
        self.policy_path = policy_path
        self.policy = self._load_policy(policy_path)

    def _load_policy(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Fusion policy file not found at: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def validate_ml_payload(self, ml_payload):
        """Validates the schema and fields of the ML payload."""
        required = ["dataset", "predicted_class", "class_probabilities", "confidence", "dangerous_class", "model_id"]
        for field in required:
            if field not in ml_payload:
                raise ValueError(f"ML payload missing required field: {field}")
        
        # Check types
        if ml_payload["dataset"].lower() not in self.policy["supported_datasets"]:
            raise ValueError(f"Unsupported dataset: {ml_payload['dataset']}")
        if not isinstance(ml_payload["class_probabilities"], dict):
            raise TypeError("class_probabilities must be a dictionary")
        if not isinstance(ml_payload["confidence"], (int, float)) or not (0.0 <= ml_payload["confidence"] <= 1.0):
            raise ValueError("confidence must be a float between 0.0 and 1.0")
        if not isinstance(ml_payload["dangerous_class"], bool):
            raise TypeError("dangerous_class must be a boolean")

    def validate_ais_payload(self, ais_payload):
        """Validates the schema and fields of the AIS payload."""
        required = ["dataset", "is_anomaly", "anomaly_score", "matched_detector_count", "nearest_detector_distance", "ais_model_id"]
        for field in required:
            if field not in ais_payload:
                raise ValueError(f"AIS payload missing required field: {field}")
        
        if ais_payload["dataset"].lower() not in self.policy["supported_datasets"]:
            raise ValueError(f"Unsupported dataset: {ais_payload['dataset']}")
        if not isinstance(ais_payload["is_anomaly"], bool):
            raise TypeError("is_anomaly must be a boolean")
        if not isinstance(ais_payload["anomaly_score"], (int, float)) or not (0.0 <= ais_payload["anomaly_score"] <= 1.0):
            raise ValueError("anomaly_score must be a float between 0.0 and 1.0")
        if not isinstance(ais_payload["matched_detector_count"], int) or ais_payload["matched_detector_count"] < 0:
            raise ValueError("matched_detector_count must be a non-negative integer")
        if not isinstance(ais_payload["nearest_detector_distance"], (int, float)):
            raise TypeError("nearest_detector_distance must be a float")

    def get_confidence_band(self, dataset, confidence):
        """Categorizes ML confidence into LOW, MEDIUM, or HIGH bands based on policy."""
        thresholds = self.policy["confidence_thresholds"][dataset]
        if confidence < thresholds["low"]:
            return "LOW"
        elif confidence >= thresholds["high"]:
            return "HIGH"
        else:
            return "MEDIUM"

    def fuse(self, ml_evidence, ais_evidence, sensors=None):
        """
        Combines ML and AIS outputs, and optional raw sensor values,
        into a final system state (NORMAL, WARNING, CRITICAL, UNKNOWN_ANOMALY).
        """
        # 1. Validation
        self.validate_ml_payload(ml_evidence)
        self.validate_ais_payload(ais_evidence)

        # 2. Match dataset identities
        dataset_ml = ml_evidence["dataset"].lower()
        dataset_ais = ais_evidence["dataset"].lower()
        if dataset_ml != dataset_ais:
            raise ValueError(f"Dataset identity mismatch: ML={dataset_ml}, AIS={dataset_ais}")

        dataset = dataset_ml

        # 3. Categorize Confidence
        confidence = ml_evidence["confidence"]
        confidence_band = self.get_confidence_band(dataset, confidence)

        # 4. Extract indicators
        is_dangerous_ml = ml_evidence["dangerous_class"]
        is_anomaly_ais = ais_evidence["is_anomaly"]
        predicted_class = ml_evidence["predicted_class"]

        # Determine states by executing decision tables
        final_state, reason_code, reasoning = self._fuse_original_table(confidence_band, is_dangerous_ml, is_anomaly_ais, predicted_class, dataset)

        # Package the standard final payload
        payload = {
            "dataset": ml_evidence["dataset"],
            "ml_evidence": {
                "predicted_class": ml_evidence["predicted_class"],
                "confidence": float(ml_evidence["confidence"]),
                "dangerous_class": ml_evidence["dangerous_class"],
                "model_id": ml_evidence["model_id"]
            },
            "ais_evidence": {
                "is_anomaly": bool(ais_evidence["is_anomaly"]),
                "anomaly_score": float(ais_evidence["anomaly_score"]),
                "matched_detector_count": int(ais_evidence["matched_detector_count"]),
                "nearest_detector_distance": float(ais_evidence["nearest_detector_distance"]),
                "ais_model_id": ais_evidence["ais_model_id"]
            },
            "fusion": {
                "final_state": final_state,
                "reason_code": reason_code,
                "reasoning": reasoning,
                "confidence_band": confidence_band
            },
            "system_metadata": {
                "fusion_version": self.policy["fusion_version"]
            }
        }
        return payload

    def _fuse_original_table(self, confidence_band, is_dangerous_ml, is_anomaly_ais, predicted_class, dataset):
        final_state = "NORMAL"
        reason_code = "ML_NORMAL_AIS_NORMAL"
        reasoning = ""

        if confidence_band == "LOW":
            # ML is uncertain, AIS is highly critical for OOD detection
            if is_anomaly_ais:
                if is_dangerous_ml:
                    # ML is uncertain but suspects a threat, and AIS signals OOD
                    final_state = "CRITICAL" if str(predicted_class).lower() == "critical" else "WARNING"
                    reason_code = "ML_LOW_CONFIDENCE"
                    reasoning = f"ML predicted a dangerous class ({predicted_class}) with LOW confidence, and AIS detected an anomaly. Elevated state to {final_state} for precautionary safety."
                else:
                    # ML is uncertain, and AIS confirms physical OOD telemetry
                    final_state = "UNKNOWN_ANOMALY"
                    reason_code = "ML_LOW_CONFIDENCE"
                    reasoning = "ML model output normal with LOW confidence, and AIS flagged a physical anomaly. Classified as UNKNOWN_ANOMALY due to OOD telemetry."
            else:
                # No anomaly detected by AIS
                if is_dangerous_ml:
                    final_state = "CRITICAL" if str(predicted_class).lower() == "critical" else "WARNING"
                    reason_code = "ML_LOW_CONFIDENCE"
                    reasoning = f"ML predicted dangerous class ({predicted_class}) with LOW confidence, but AIS was normal. Maintained {final_state} as a safety precaution."
                else:
                    final_state = "NORMAL"
                    reason_code = "ML_LOW_CONFIDENCE"
                    reasoning = "ML model predicted normal with LOW confidence. Telemetry was in-distribution (AIS normal). System state set to NORMAL."

        else:
            # ML confidence is MEDIUM or HIGH
            if is_dangerous_ml:
                # Strong known threat
                final_state = "CRITICAL" if str(predicted_class).lower() == "critical" else "WARNING"
                reason_code = "ML_DANGEROUS"
                if is_anomaly_ais:
                    reasoning = f"Supervised ML predicted dangerous class ({predicted_class}) with {confidence_band} confidence, confirmed by parallel AIS anomaly."
                else:
                    reasoning = f"Supervised ML predicted dangerous class ({predicted_class}) with {confidence_band} confidence. Parallel AIS did not detect novelty (in-distribution)."
            else:
                # ML predicts normal class
                if is_anomaly_ais:
                    # Contradiction: ML says NORMAL with confidence, AIS says ANOMALY
                    # Lookup dynamic reliability from policy configuration
                    dataset_rel = self.policy.get("dataset_reliability", {}).get(dataset, {})
                    ais_reliable = dataset_rel.get("ais_reliable", False)
                    
                    if ais_reliable:
                        final_state = "UNKNOWN_ANOMALY"
                        reason_code = "ML_NORMAL_AIS_ANOMALY"
                        reasoning = f"ML predicted normal with {confidence_band} confidence, but reliable {dataset.upper()} AIS flagged anomaly. Emitted UNKNOWN_ANOMALY."
                    else:
                        final_state = "NORMAL"
                        reason_code = "HABSOS_AIS_LIMITED_RELIABILITY"
                        reasoning = f"ML predicted normal with {confidence_band} confidence. {dataset.upper()} AIS flagged an anomaly, but its validation reliability is limited. Disregarded anomaly to prevent false alarm."
                else:
                    # Both agree normal
                    final_state = "NORMAL"
                    reason_code = "ML_NORMAL_AIS_NORMAL"
                    reasoning = f"Both supervised ML ({confidence_band} confidence) and parallel AIS confirm normal, in-distribution telemetry."

        return final_state, reason_code, reasoning
