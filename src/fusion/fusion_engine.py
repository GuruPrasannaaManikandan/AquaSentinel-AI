import os
import time
import json
import logging
import datetime
import numpy as np
from dataclasses import is_dataclass, asdict
from typing import Optional, Dict, Any, Union

from src.cv.visual_detection import VisualEvidence
from src.fusion.multimodal_fusion import FusedEvidence

class FusionEngine:
    """
    Transparent, deterministic, testable evidence-fusion engine.
    Combines supervised ML outputs, unsupervised AIS anomaly detection outputs,
    and visual computer-vision evidence into a final system state
    (NORMAL, WARNING, CRITICAL, UNKNOWN_ANOMALY).
    """
    def __init__(self, policy_path=None):
        if policy_path is None:
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

    def validate_visual_payload(self, visual_payload: Union[VisualEvidence, Dict[str, Any]]) -> Dict[str, Any]:
        """Validates and standardizes VisualEvidence payload into dictionary format."""
        if visual_payload is None:
            return None

        if is_dataclass(visual_payload):
            v_dict = asdict(visual_payload)
        elif isinstance(visual_payload, dict):
            v_dict = visual_payload.copy()
        else:
            raise TypeError("visual_evidence must be a VisualEvidence dataclass or dictionary")

        required = ["visual_state", "confidence", "risk_level"]
        for field in required:
            if field not in v_dict:
                raise ValueError(f"Visual payload missing required field: {field}")

        return v_dict

    def get_confidence_band(self, dataset, confidence):
        """Categorizes ML confidence into LOW, MEDIUM, or HIGH bands based on policy."""
        thresholds = self.policy["confidence_thresholds"][dataset]
        if confidence < thresholds["low"]:
            return "LOW"
        elif confidence >= thresholds["high"]:
            return "HIGH"
        else:
            return "MEDIUM"

    def fuse(
        self,
        ml_evidence: Dict[str, Any],
        ais_evidence: Dict[str, Any],
        sensors: Optional[Dict[str, Any]] = None,
        visual_evidence: Optional[Union[VisualEvidence, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Combines ML, AIS, and optional Visual computer vision evidence
        into a final system decision (NORMAL, WARNING, CRITICAL, UNKNOWN_ANOMALY).
        """
        start_time = time.perf_counter()

        # 1. Validate Sensor Payloads
        self.validate_ml_payload(ml_evidence)
        self.validate_ais_payload(ais_evidence)

        # 2. Match dataset identities
        dataset_ml = ml_evidence["dataset"].lower()
        dataset_ais = ais_evidence["dataset"].lower()
        if dataset_ml != dataset_ais:
            raise ValueError(f"Dataset identity mismatch: ML={dataset_ml}, AIS={dataset_ais}")

        dataset = dataset_ml
        confidence = ml_evidence["confidence"]
        confidence_band = self.get_confidence_band(dataset, confidence)

        is_dangerous_ml = ml_evidence["dangerous_class"]
        is_anomaly_ais = ais_evidence["is_anomaly"]
        predicted_class = ml_evidence["predicted_class"]

        # Base Sensor Decision
        sensor_state, sensor_reason_code, sensor_reasoning = self._fuse_original_table(
            confidence_band, is_dangerous_ml, is_anomaly_ais, predicted_class, dataset
        )

        # 3. Multimodal Visual Evidence Fusion Check
        visual_dict = self.validate_visual_payload(visual_evidence) if visual_evidence is not None else None

        if visual_dict is None:
            # Sensor-only Mode (100% Backward Compatible)
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return {
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
                    "final_state": sensor_state,
                    "reason_code": sensor_reason_code,
                    "reasoning": sensor_reasoning,
                    "confidence_band": confidence_band,
                    "multimodal": False
                },
                "system_metadata": {
                    "fusion_version": self.policy["fusion_version"],
                    "fusion_pipeline_time_ms": round(duration_ms, 3)
                }
            }

        # Multimodal Fusion Execution
        final_state, reason_code, reasoning = self._fuse_multimodal_table(
            sensor_state, sensor_reason_code, sensor_reasoning, visual_dict
        )

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return {
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
            "visual_evidence": visual_dict,
            "fusion": {
                "final_state": final_state,
                "reason_code": reason_code,
                "reasoning": reasoning,
                "confidence_band": confidence_band,
                "multimodal": True
            },
            "system_metadata": {
                "fusion_version": self.policy["fusion_version"],
                "fusion_pipeline_time_ms": round(duration_ms, 3)
            }
        }

    def _fuse_original_table(self, confidence_band, is_dangerous_ml, is_anomaly_ais, predicted_class, dataset):
        """Standard V3 sensor decision logic."""
        final_state = "NORMAL"
        reason_code = "ML_NORMAL_AIS_NORMAL"
        reasoning = ""

        if confidence_band == "LOW":
            if is_anomaly_ais:
                if is_dangerous_ml:
                    final_state = "CRITICAL" if str(predicted_class).lower() == "critical" else "WARNING"
                    reason_code = "ML_LOW_CONFIDENCE"
                    reasoning = f"ML predicted a dangerous class ({predicted_class}) with LOW confidence, and AIS detected an anomaly. Elevated state to {final_state} for precautionary safety."
                else:
                    final_state = "UNKNOWN_ANOMALY"
                    reason_code = "ML_LOW_CONFIDENCE"
                    reasoning = "ML model output normal with LOW confidence, and AIS flagged a physical anomaly. Classified as UNKNOWN_ANOMALY due to OOD telemetry."
            else:
                if is_dangerous_ml:
                    final_state = "CRITICAL" if str(predicted_class).lower() == "critical" else "WARNING"
                    reason_code = "ML_LOW_CONFIDENCE"
                    reasoning = f"ML predicted dangerous class ({predicted_class}) with LOW confidence, but AIS was normal. Maintained {final_state} as a safety precaution."
                else:
                    final_state = "NORMAL"
                    reason_code = "ML_LOW_CONFIDENCE"
                    reasoning = "ML model predicted normal with LOW confidence. Telemetry was in-distribution (AIS normal). System state set to NORMAL."
        else:
            if is_dangerous_ml:
                final_state = "CRITICAL" if str(predicted_class).lower() == "critical" else "WARNING"
                reason_code = "ML_DANGEROUS"
                if is_anomaly_ais:
                    reasoning = f"Supervised ML predicted dangerous class ({predicted_class}) with {confidence_band} confidence, confirmed by parallel AIS anomaly."
                else:
                    reasoning = f"Supervised ML predicted dangerous class ({predicted_class}) with {confidence_band} confidence. Parallel AIS did not detect novelty (in-distribution)."
            else:
                if is_anomaly_ais:
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
                    final_state = "NORMAL"
                    reason_code = "ML_NORMAL_AIS_NORMAL"
                    reasoning = f"Both supervised ML ({confidence_band} confidence) and parallel AIS confirm normal, in-distribution telemetry."

        return final_state, reason_code, reasoning

    def _fuse_multimodal_table(self, sensor_state, sensor_reason_code, sensor_reasoning, visual_dict):
        """Multimodal Dempster-Shafer belief fusion logic combining sensor decision with visual evidence."""
        v_state = visual_dict.get("visual_state", "UNCERTAIN")
        risk_level = visual_dict.get("risk_level", "NONE")

        # Handle Camera Faults & Inference Failures
        if v_state in ["CAMERA_FAULT", "INFERENCE_FAILURE"]:
            return sensor_state, "VISUAL_CAMERA_FAULT", f"Camera hardware/inference fault ({v_state}). Maintained base sensor fusion decision: {sensor_state}."

        # Case A: Sensor threat confirmed by visual bloom evidence
        if sensor_state in ["WARNING", "CRITICAL"] and v_state == "BLOOM_EVIDENCE":
            final_state = "CRITICAL"
            reason_code = "MULTIMODAL_BLOOM_CONFIRMED"
            reasoning = f"Multimodal confirmation: Sensor evidence ({sensor_state}) and camera visual evidence (BLOOM_EVIDENCE, risk={risk_level}) independently confirm bloom threat. Elevated system state to CRITICAL."
            return final_state, reason_code, reasoning

        # Case B: Sensor normal but visual camera detects strong bloom risk (Visual Early Warning)
        if sensor_state == "NORMAL" and v_state == "BLOOM_EVIDENCE" and risk_level in ["HIGH", "CRITICAL"]:
            final_state = "WARNING"
            reason_code = "VISUAL_EARLY_WARNING"
            reasoning = f"Visual Early Warning: Water chemistry sensors read normal, but camera detects strong visual algal bloom surface evidence (risk={risk_level}). System state elevated to WARNING."
            return final_state, reason_code, reasoning

        # Case C: Sensor ML low confidence / anomaly but camera disconfirms bloom (Visual Disconfirmed Normal)
        if sensor_state in ["WARNING", "UNKNOWN_ANOMALY"] and sensor_reason_code == "ML_LOW_CONFIDENCE" and v_state == "NO_VISUAL_BLOOM":
            final_state = "NORMAL"
            reason_code = "VISUAL_DISCONFIRMED_NORMAL"
            reasoning = "Visual Disconfirmation: Sensor ML had low confidence, but camera confirms clear visual water (NO_VISUAL_BLOOM). System state set to NORMAL."
            return final_state, reason_code, reasoning

        # Case D: Sediment Turbidity Discoloration
        if v_state == "TURBID_DISCOLORATION":
            final_state = sensor_state
            reason_code = "VISUAL_TURBIDITY_MITIGATED"
            reasoning = f"Camera identified sediment turbidity discoloration without photosynthetic green bloom scum. Preserved sensor decision ({sensor_state})."
            return final_state, reason_code, reasoning

        # Default fallback
        return sensor_state, sensor_reason_code, f"{sensor_reasoning} (Visual evidence: {v_state}, risk={risk_level})."
