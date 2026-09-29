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
from src.fusion.multimodal_alignment import (
    MultimodalEvidenceItem,
    MultimodalSnapshot,
    TemporalAlignmentEngine,
    build_multimodal_snapshot
)
from src.fusion.multimodal_intelligence import (
    ConcordanceEngine,
    ConflictDetector,
    MultimodalStateEstimator,
    ConcordanceResult,
    ConflictResult,
    MultimodalStateResult
)

class FusionEngine:
    """
    Transparent, deterministic, testable evidence-fusion engine.
    Combines supervised ML outputs, unsupervised AIS anomaly detection outputs,
    and visual computer-vision evidence into a final system state
    (NORMAL, WARNING, CRITICAL, UNKNOWN_ANOMALY).
    Integrates V7 multimodal alignment, cross-modality concordance, conflict resolution,
    and dominance-prevention state estimation.
    """
    def __init__(self, policy_path=None):
        if policy_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            policy_path = os.path.join(base_dir, "config", "fusion_policy.json")
        self.policy_path = policy_path
        self.policy = self._load_policy(policy_path)
        
        # V7 Multimodal Intelligence Components
        self.temporal_alignment_engine = TemporalAlignmentEngine()
        self.concordance_engine = ConcordanceEngine()
        self.conflict_detector = ConflictDetector()
        self.state_estimator = MultimodalStateEstimator()

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
        visual_evidence: Optional[Union[VisualEvidence, Dict[str, Any]]] = None,
        sensor_quality: Optional[Dict[str, Any]] = None,
        temporal_evidence: Optional[Union[Any, Dict[str, Any]]] = None,
        historical_evidence: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Combines ML, AIS, optional Visual computer vision evidence, V5.1 sensor quality,
        V5.3 temporal environmental trajectory, and V7 multimodal alignment/conflict intelligence
        into a reliability-weighted evidential decision.
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

        # Parse temporal evidence if provided
        temp_dict = None
        if temporal_evidence is not None:
            temp_dict = temporal_evidence.to_dict() if hasattr(temporal_evidence, "to_dict") else temporal_evidence

        # Parse sensor quality
        q_sensor = 1.0
        if sensor_quality is not None:
            q_sensor = float(sensor_quality.get("q_sensor", 1.0))

        # 3. Multimodal Visual Evidence Fusion Check
        visual_dict = self.validate_visual_payload(visual_evidence) if visual_evidence is not None else None

        # Build V7 Multimodal Evidence Alignment Snapshot
        snapshot = build_multimodal_snapshot(
            sensor_evidence=ml_evidence,
            visual_evidence=visual_dict,
            temporal_evidence=temp_dict,
            ais_evidence=ais_evidence,
            historical_evidence=historical_evidence,
            sensor_quality=sensor_quality,
            alignment_engine=self.temporal_alignment_engine
        )
        concordance = self.concordance_engine.evaluate(snapshot)
        conflict = self.conflict_detector.detect(snapshot)
        state_res = self.state_estimator.estimate(snapshot, concordance, conflict)

        # Compute Continuous Evidential Threat Scores
        # 1. Sensor Threat Score
        t_sensor = 0.85 if is_dangerous_ml else 0.05
        w_sensor = 0.40 * q_sensor

        # 2. AIS Novelty Score
        t_ais = float(ais_evidence.get("anomaly_score", 0.80 if is_anomaly_ais else 0.05))
        if ais_evidence.get("immune_response_type") == "SECONDARY_RESPONSE":
            t_ais = min(1.0, t_ais + 0.15)
        dataset_rel = self.policy.get("dataset_reliability", {}).get(dataset, {})
        ais_reliable = dataset_rel.get("ais_reliable", True)
        w_ais = 0.20 if ais_reliable else 0.05

        # 3. Temporal Threat Score
        t_temporal = 0.0
        w_temporal = 0.0
        if temp_dict is not None:
            t_temporal = float(temp_dict.get("trajectory_risk_score", 0.0))
            w_temporal = 0.30 if temp_dict.get("window_size_evaluated", 0) >= 2 else 0.10

        # 4. Visual Threat Score
        t_visual = 0.0
        w_visual = 0.0
        q_visual = 1.0
        if visual_dict is not None:
            q_visual = float(visual_dict.get("q_visual", 1.0))
            v_state = visual_dict.get("visual_state", "UNCERTAIN")
            if v_state == "BLOOM_EVIDENCE":
                t_visual = float(visual_dict.get("effective_confidence", 0.90))
                w_visual = 0.35 * q_visual
            elif v_state == "TURBID_DISCOLORATION":
                t_visual = 0.15
                w_visual = 0.35 * q_visual
            elif v_state == "NO_VISUAL_BLOOM":
                t_visual = 0.0
                w_visual = 0.35 * q_visual
            else:
                # Camera fault or degraded
                t_visual = 0.0
                w_visual = 0.0

        # Composite Evidential Threat Calculation
        total_w = w_sensor + w_ais + w_temporal + w_visual
        if total_w > 0:
            composite_risk = (w_sensor * t_sensor + w_ais * t_ais + w_temporal * t_temporal + w_visual * t_visual) / total_w
        else:
            composite_risk = 0.0

        composite_risk = round(float(composite_risk), 4)

        multimodal_intel_summary = {
            "concordance": concordance.to_dict(),
            "conflict": conflict.to_dict(),
            "state_result": state_res.to_dict(),
            "snapshot_summary": {
                "available_modalities": snapshot.available_modalities,
                "missing_modalities": snapshot.missing_modalities,
                "degraded_modalities": snapshot.degraded_modalities,
                "alignment_quality": snapshot.alignment_quality,
                "effective_risk_score": state_res.effective_risk_score,
                "dominance_prevented": state_res.dominance_prevented
            }
        }

        if visual_dict is None:
            # Sensor-only Mode (100% Backward Compatible)
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # Derive 5-Tier Ecological State
            if sensor_state == "CRITICAL" or composite_risk >= 0.70 or (temp_dict and temp_dict.get("temporal_state") == "BLOOM_CONFIRMED"):
                eco_state = "BLOOM_CONFIRMED"
            elif composite_risk >= 0.50 or (temp_dict and temp_dict.get("temporal_state") == "HIGH_RISK"):
                eco_state = "HIGH_RISK"
            elif sensor_state == "WARNING" or composite_risk >= 0.30 or (temp_dict and temp_dict.get("temporal_state") == "EARLY_WARNING"):
                eco_state = "EARLY_WARNING"
            elif composite_risk >= 0.18 or (temp_dict and temp_dict.get("temporal_state") == "WATCH"):
                eco_state = "WATCH"
            else:
                eco_state = "NORMAL"

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
                    "ais_model_id": ais_evidence["ais_model_id"],
                    "immune_response_type": ais_evidence.get("immune_response_type", "PRIMARY_RESPONSE" if is_anomaly_ais else "SELF_TOLERANT")
                },
                "fusion": {
                    "final_state": sensor_state,
                    "ecological_state": eco_state,
                    "composite_risk_score": composite_risk,
                    "reason_code": sensor_reason_code,
                    "reasoning": sensor_reasoning,
                    "confidence_band": confidence_band,
                    "multimodal": False,
                    "modality_weights": {
                        "sensor": round(w_sensor, 3),
                        "ais": round(w_ais, 3),
                        "temporal": round(w_temporal, 3),
                        "visual": 0.0
                    }
                },
                "sensor_quality": sensor_quality,
                "temporal_evidence": temp_dict,
                "multimodal_snapshot": snapshot.to_dict(),
                "concordance": concordance.to_dict(),
                "conflict": conflict.to_dict(),
                "multimodal_state": state_res.to_dict(),
                "multimodal_intelligence": multimodal_intel_summary,
                "system_metadata": {
                    "fusion_version": self.policy["fusion_version"],
                    "fusion_pipeline_time_ms": round(duration_ms, 3),
                    "sensor_quality": sensor_quality,
                    "temporal_evidence": temp_dict
                }
            }

        # Multimodal Fusion Execution
        final_state, reason_code, reasoning = self._fuse_multimodal_table(
            sensor_state, sensor_reason_code, sensor_reasoning, visual_dict
        )

        # Apply V7 Conflict & Dominance Governance
        if conflict.has_conflict:
            if conflict.prescriptive_action == "SUPPRESS_EMERGENCY" and final_state == "CRITICAL":
                final_state = "WARNING"
                reasoning = f"{reasoning} [V7 Conflict Resolution: Emergency suppressed due to cross-modality conflict ({conflict.conflict_type})]."
            elif conflict.prescriptive_action == "CONSERVATIVE_HOLD" and final_state == "NORMAL":
                final_state = "WARNING"
                reasoning = f"{reasoning} [V7 Conflict Resolution: Elevated to WARNING for conservative hold ({conflict.conflict_type})]."

        # Multi-Tier Ecological State Mapping
        if state_res.dominance_prevented and state_res.ecological_state in ["EARLY_WARNING", "WATCH", "NORMAL"]:
            eco_state = state_res.ecological_state
        elif final_state == "CRITICAL" or reason_code == "MULTIMODAL_BLOOM_CONFIRMED" or composite_risk >= 0.75 or state_res.ecological_state == "BLOOM_CONFIRMED":
            eco_state = "BLOOM_CONFIRMED"
        elif composite_risk >= 0.55 or state_res.ecological_state == "HIGH_RISK":
            eco_state = "HIGH_RISK"
        elif final_state == "WARNING" or reason_code == "VISUAL_EARLY_WARNING" or composite_risk >= 0.35 or state_res.ecological_state == "EARLY_WARNING":
            eco_state = "EARLY_WARNING"
        elif composite_risk >= 0.20 or (temp_dict and temp_dict.get("temporal_state") == "WATCH") or state_res.ecological_state == "WATCH":
            eco_state = "WATCH"
        else:
            eco_state = "NORMAL"

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
                "ais_model_id": ais_evidence["ais_model_id"],
                "immune_response_type": ais_evidence.get("immune_response_type", "PRIMARY_RESPONSE" if is_anomaly_ais else "SELF_TOLERANT")
            },
            "visual_evidence": visual_dict,
            "fusion": {
                "final_state": final_state,
                "ecological_state": eco_state,
                "composite_risk_score": composite_risk,
                "reason_code": reason_code,
                "reasoning": reasoning,
                "confidence_band": confidence_band,
                "multimodal": True,
                "modality_weights": {
                    "sensor": round(w_sensor, 3),
                    "ais": round(w_ais, 3),
                    "temporal": round(w_temporal, 3),
                    "visual": round(w_visual, 3)
                }
            },
            "sensor_quality": sensor_quality,
            "temporal_evidence": temp_dict,
            "multimodal_snapshot": snapshot.to_dict(),
            "concordance": concordance.to_dict(),
            "conflict": conflict.to_dict(),
            "multimodal_state": state_res.to_dict(),
            "multimodal_intelligence": multimodal_intel_summary,
            "system_metadata": {
                "fusion_version": self.policy["fusion_version"],
                "fusion_pipeline_time_ms": round(duration_ms, 3),
                "sensor_quality": sensor_quality,
                "temporal_evidence": temp_dict
            }
        }

    def fuse_multimodal_snapshot(self, snapshot: MultimodalSnapshot) -> Dict[str, Any]:
        """
        Directly evaluates a pre-constructed MultimodalSnapshot, returning
        concordance analysis, conflict resolution, and dominance-governed state.
        """
        concordance = self.concordance_engine.evaluate(snapshot)
        conflict = self.conflict_detector.detect(snapshot)
        state_res = self.state_estimator.estimate(snapshot, concordance, conflict)

        return {
            "multimodal_snapshot": snapshot.to_dict(),
            "concordance": concordance.to_dict(),
            "conflict": conflict.to_dict(),
            "multimodal_state": state_res.to_dict(),
            "fusion": {
                "final_state": state_res.ecological_state,
                "ecological_state": state_res.ecological_state,
                "composite_risk_score": state_res.effective_risk_score,
                "reason_code": conflict.conflict_type if conflict.has_conflict else "MULTIMODAL_CONCORDANT",
                "reasoning": state_res.diagnostic_rationale,
                "confidence_band": "HIGH" if state_res.confidence_score >= 0.75 else ("MEDIUM" if state_res.confidence_score >= 0.5 else "LOW"),
                "multimodal": True
            },
            "multimodal_intelligence": {
                "concordance": concordance.to_dict(),
                "conflict": conflict.to_dict(),
                "state_result": state_res.to_dict(),
                "snapshot_summary": {
                    "available_modalities": snapshot.available_modalities,
                    "missing_modalities": snapshot.missing_modalities,
                    "degraded_modalities": snapshot.degraded_modalities,
                    "alignment_quality": snapshot.alignment_quality,
                    "effective_risk_score": state_res.effective_risk_score,
                    "dominance_prevented": state_res.dominance_prevented
                }
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

        # Handle Camera Faults, Temporal Faults, Inference Failures & Degraded Visual Quality
        if v_state in ["CAMERA_FAULT", "INFERENCE_FAILURE", "DEGRADED_VISUAL", "DEGRADED_VISUAL_EVIDENCE"]:
            reason_code = visual_dict.get("reason_code") or "VISUAL_CAMERA_FAULT"
            if reason_code in ["OK", "NONE"]:
                reason_code = "VISUAL_CAMERA_FAULT" if v_state == "CAMERA_FAULT" else "VISUAL_QUALITY_DEGRADED"
            return sensor_state, reason_code, f"Camera hardware/optical fault ({v_state}, {reason_code}). Maintained base sensor fusion decision: {sensor_state}."

        # Case A: Sensor threat confirmed by visual bloom evidence
        if sensor_state in ["WARNING", "CRITICAL"] and v_state == "BLOOM_EVIDENCE":
            final_state = "CRITICAL"
            reason_code = "MULTIMODAL_BLOOM_CONFIRMED"
            reasoning = f"Multimodal confirmation: Sensor evidence ({sensor_state}) and camera visual evidence (BLOOM_EVIDENCE, risk={risk_level}) independently confirm bloom threat. Elevated system state to CRITICAL."
            return final_state, reason_code, reasoning

        # Case A2: Telemetry anomaly confirmed by visual bloom evidence
        if sensor_state == "UNKNOWN_ANOMALY" and v_state == "BLOOM_EVIDENCE":
            final_state = "CRITICAL" if risk_level == "CRITICAL" else "WARNING"
            reason_code = "VISUAL_CONFIRMED_ANOMALY"
            reasoning = f"Multimodal confirmation: Telemetry anomaly confirmed by camera visual evidence (BLOOM_EVIDENCE, risk={risk_level}). Elevated system state to {final_state}."
            return final_state, reason_code, reasoning

        # Case B: Sensor normal but visual camera detects strong bloom risk (Visual Early Warning)
        if sensor_state == "NORMAL" and v_state == "BLOOM_EVIDENCE" and risk_level in ["HIGH", "CRITICAL"]:
            final_state = "WARNING"
            reason_code = "VISUAL_EARLY_WARNING"
            reasoning = f"Visual Early Warning: Water chemistry sensors read normal, but camera detects strong visual algal bloom surface evidence (risk={risk_level}). System state elevated to WARNING."
            return final_state, reason_code, reasoning

        # Case C: Sensor ML low confidence / anomaly but camera disconfirms bloom (Visual Disconfirmed Normal)
        if sensor_state in ["WARNING", "UNKNOWN_ANOMALY"] and sensor_reason_code == "ML_LOW_CONFIDENCE" and v_state in ["NO_VISUAL_BLOOM", "NORMAL_WATER"]:
            final_state = "NORMAL"
            reason_code = "VISUAL_DISCONFIRMED_NORMAL"
            reasoning = "Visual Disconfirmation: Sensor ML had low confidence, but camera confirms clear visual water (NO_VISUAL_BLOOM). System state set to NORMAL."
            return final_state, reason_code, reasoning

        # Case D: Sediment Turbidity Discoloration
        if v_state in ["TURBID_DISCOLORATION", "TURBIDITY_EVIDENCE"]:
            final_state = sensor_state
            reason_code = "VISUAL_TURBIDITY_MITIGATED"
            reasoning = f"Camera identified sediment turbidity discoloration without photosynthetic green bloom scum. Preserved sensor decision ({sensor_state})."
            return final_state, reason_code, reasoning

        # Default fallback
        return sensor_state, sensor_reason_code, f"{sensor_reasoning} (Visual evidence: {v_state}, risk={risk_level})."


MultimodalFusionEngine = FusionEngine
