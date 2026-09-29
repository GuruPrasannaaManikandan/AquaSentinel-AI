import time
import logging
import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Union

from src.cv.cv_model import CVPrediction
from src.cv.temporal_visual import TemporalVisualBuffer, TemporalVisualConsistencyResult

@dataclass
class VisualDetectionResult:
    """
    V6 Canonical Visual Detection Result Contract.
    Strictly ties model classification confidence to physical optical quality.
    """
    class_name: str
    confidence: float
    model_version: str
    timestamp: str
    frame_id: str
    q_visual: float
    evidence_state: str  # "NORMAL_WATER", "BLOOM_EVIDENCE", "TURBIDITY_EVIDENCE", "UNCERTAIN_VISUAL", "CAMERA_FAULT", "DEGRADED_VISUAL"
    valid: bool
    evidence_strength: float = 0.0
    degradation_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VisualEvidence:
    """
    Structured visual evidence interpretation produced by the Visual Detection layer.
    Translates raw computer vision predictions into structured evidence consumable by decision/fusion engines.
    """
    frame_id: str
    timestamp: str  # ISO-8601 timestamp string linked to source frame & model prediction
    source: str = "COMPUTER_VISION"
    predicted_visual_class: str = "UNCERTAIN"
    confidence: float = 0.0
    visual_state: str = "UNCERTAIN"  # "NO_VISUAL_BLOOM", "BLOOM_EVIDENCE", "TURBID_DISCOLORATION", "UNCERTAIN", "CAMERA_FAULT", "INFERENCE_FAILURE", "DEGRADED_VISUAL"
    risk_level: str = "UNKNOWN"       # "NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"
    evidence_strength: float = 0.0   # Normalized evidence weight [0.0, 1.0]
    detections_count: int = 0
    bounding_boxes: List[Dict[str, Any]] = field(default_factory=list)
    highest_confidence_detection: Optional[Dict[str, Any]] = None
    model_name: str = "UnknownModel"
    model_version: str = "1.0.0"
    inference_status: str = "UNKNOWN"
    preprocessing_time_ms: float = 0.0
    inference_time_ms: float = 0.0
    visual_pipeline_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # V5.2 Optical Quality & Temporal Consistency additions
    q_visual: float = 1.0
    quality_state: str = "RELIABLE"
    effective_confidence: float = 0.0
    temporal_consistency: float = 1.0
    frames_evaluated: int = 1
    consistency_state: str = "SINGLE_FRAME"
    quality_flags: List[str] = field(default_factory=list)
    optical_quality: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["class_name"] = self.predicted_visual_class
        ev_state = self.visual_state
        if self.quality_state in ["DEGRADED", "UNRELIABLE", "CORRUPTED"] or self.q_visual < 0.40:
            ev_state = "DEGRADED_VISUAL"
        d["evidence_state"] = ev_state
        d["valid"] = self.q_visual >= 0.40 and self.visual_state not in ["CAMERA_FAULT", "DEGRADED_VISUAL", "INFERENCE_FAILURE"] and ev_state != "DEGRADED_VISUAL"
        return d

    def to_visual_detection_result(self) -> VisualDetectionResult:
        ev_state = self.visual_state
        if self.quality_state in ["DEGRADED", "UNRELIABLE", "CORRUPTED"] or self.q_visual < 0.40:
            ev_state = "DEGRADED_VISUAL"
        is_valid = self.q_visual >= 0.40 and self.visual_state not in ["CAMERA_FAULT", "DEGRADED_VISUAL", "INFERENCE_FAILURE"] and ev_state != "DEGRADED_VISUAL"
        deg_reason = None
        if not is_valid:
            deg_reason = self.quality_state if self.quality_state != "RELIABLE" else self.inference_status
        return VisualDetectionResult(
            class_name=self.predicted_visual_class,
            confidence=round(float(self.confidence), 4),
            model_version=self.model_version,
            timestamp=self.timestamp,
            frame_id=self.frame_id,
            q_visual=round(float(self.q_visual), 4),
            evidence_state=ev_state,
            valid=is_valid,
            evidence_strength=round(float(self.evidence_strength), 3),
            degradation_reason=deg_reason,
            metadata=dict(self.metadata)
        )


class VisualDetector:
    """
    Aquatic Visual Detection & Evidence Generator.
    Interprets raw CVPrediction model outputs, applies configurable confidence thresholds,
    aggregates multiple detections, handles hardware faults, and formats VisualEvidence payloads.
    """
    def __init__(
        self,
        high_confidence_threshold: float = 0.85,
        medium_confidence_threshold: float = 0.60,
        low_confidence_threshold: float = 0.40,
        config: Optional[dict] = None
    ):
        self.high_confidence_threshold = high_confidence_threshold
        self.medium_confidence_threshold = medium_confidence_threshold
        self.low_confidence_threshold = low_confidence_threshold
        self.config = config or {}
        self.temporal_buffer = TemporalVisualBuffer(window_size_k=3)

    def evaluate_prediction(
        self,
        prediction: CVPrediction,
        optical_quality: Optional[Union[Dict[str, Any], Any]] = None
    ) -> VisualEvidence:
        """
        Evaluates a raw CVPrediction and returns structured VisualEvidence.
        Preserves complete provenance, latency metrics, detection bounding boxes,
        optical quality (Q_visual), and multi-frame temporal consistency.
        """
        start_time = time.perf_counter()

        # Step 1: Null or Missing Prediction Check
        if prediction is None:
            detection_time_ms = (time.perf_counter() - start_time) * 1000.0
            return VisualEvidence(
                frame_id="UNKNOWN",
                timestamp=datetime.datetime.now().isoformat(),
                predicted_visual_class="UNCERTAIN",
                confidence=0.0,
                visual_state="CAMERA_FAULT",
                risk_level="UNKNOWN",
                evidence_strength=0.0,
                inference_status="NULL_PREDICTION",
                visual_pipeline_time_ms=round(detection_time_ms, 3)
            )

        preproc_ms = prediction.preprocessing_time_ms
        infer_ms = prediction.inference_time_ms

        # Step 2: Fault Status Handling
        # Note: CAMERA_FAULT and NO_VISUAL_BLOOM are explicitly NOT equivalent.
        if prediction.status in ["CAMERA_OFFLINE", "CORRUPTED", "EMPTY_PAYLOAD", "NULL_FRAME", "NULL_INPUT", "OVERSIZED_PAYLOAD", "INVALID_TIMESTAMP", "VISUAL_TIMESTAMP_INVALID", "VISUAL_TIMESTAMP_STALE", "VISUAL_TIMESTAMP_FUTURE", "VISUAL_CLOCK_UNSYNCED", "VISUAL_CLOCK_SKEW"] or prediction.status.startswith("VISUAL_"):
            detection_time_ms = (time.perf_counter() - start_time) * 1000.0
            total_ms = prediction.total_pipeline_time_ms + detection_time_ms
            reason_code = prediction.status if prediction.status.startswith("VISUAL_") else f"VISUAL_{prediction.status}"
            return VisualEvidence(
                frame_id=prediction.frame_id,
                timestamp=prediction.timestamp,
                predicted_visual_class="UNCERTAIN",
                confidence=0.0,
                visual_state="CAMERA_FAULT",
                risk_level="UNKNOWN",
                evidence_strength=0.0,
                model_name=prediction.model_name,
                model_version=prediction.model_version,
                inference_status=prediction.status,
                preprocessing_time_ms=preproc_ms,
                inference_time_ms=infer_ms,
                visual_pipeline_time_ms=round(total_ms, 3),
                metadata={"error": f"Camera hardware/temporal fault: {prediction.status}", "reason_code": reason_code, "source_metadata": prediction.metadata}
            )

        if prediction.status in ["MODEL_OFFLINE", "INFERENCE_FAILURE"]:
            detection_time_ms = (time.perf_counter() - start_time) * 1000.0
            total_ms = prediction.total_pipeline_time_ms + detection_time_ms
            return VisualEvidence(
                frame_id=prediction.frame_id,
                timestamp=prediction.timestamp,
                predicted_visual_class="UNCERTAIN",
                confidence=0.0,
                visual_state="INFERENCE_FAILURE",
                risk_level="UNKNOWN",
                evidence_strength=0.0,
                model_name=prediction.model_name,
                model_version=prediction.model_version,
                inference_status=prediction.status,
                preprocessing_time_ms=preproc_ms,
                inference_time_ms=infer_ms,
                visual_pipeline_time_ms=round(total_ms, 3),
                metadata={"error": f"Inference engine failure: {prediction.status}", "source_metadata": prediction.metadata}
            )

        # Step 3: Optical Quality Extraction & Effective Confidence
        opt_dict = None
        if optical_quality is not None:
            opt_dict = optical_quality.to_dict() if hasattr(optical_quality, "to_dict") else optical_quality
        else:
            opt_dict = prediction.metadata.get("source_metadata", {}).get("optical_quality")

        if opt_dict:
            q_visual = float(opt_dict.get("q_visual", 1.0))
            quality_state = str(opt_dict.get("quality_state", "RELIABLE"))
            quality_flags = list(opt_dict.get("quality_flags", []))
        else:
            q_visual = 1.0
            quality_state = "RELIABLE"
            quality_flags = []

        conf = float(prediction.confidence)
        pred_cls = prediction.predicted_class
        effective_conf = round(float(conf * q_visual), 4)

        # Step 4: Multi-Frame Temporal Buffer Update
        temp_res = self.temporal_buffer.add_frame(
            frame_id=prediction.frame_id,
            timestamp=prediction.timestamp,
            predicted_class=pred_cls,
            raw_confidence=conf,
            q_visual=q_visual,
            quality_state=quality_state
        )

        # Step 5: Detections & Bounding Box Aggregation
        highest_det = None
        if prediction.bounding_boxes and len(prediction.bounding_boxes) > 0:
            # Sort detections by confidence descending
            sorted_dets = sorted(prediction.bounding_boxes, key=lambda d: d.get("confidence", 0.0), reverse=True)
            highest_det = sorted_dets[0]

        # Step 6: Visual State & Risk Level Interpretation
        if temp_res.consistency_state == "TRANSIENT_BLOOM":
            # Single transient bloom frame surrounded by normal frames
            v_state = "UNCERTAIN"
            risk = "LOW"
            strength = round(effective_conf * 0.35, 3)
        elif temp_res.consistency_state == "AMBIGUOUS":
            # Conflicting alternating sequence
            v_state = "UNCERTAIN"
            risk = "LOW"
            strength = round(effective_conf * 0.33, 3)
        elif pred_cls in ["ALGAL_BLOOM_RISK", "ALGAL_BLOOM"]:
            if effective_conf >= self.high_confidence_threshold or (conf >= self.high_confidence_threshold and q_visual >= 0.70):
                v_state = "BLOOM_EVIDENCE"
                risk = "HIGH"
                strength = effective_conf
            elif effective_conf >= self.medium_confidence_threshold:
                v_state = "BLOOM_EVIDENCE"
                risk = "MEDIUM"
                strength = effective_conf * 0.8
            else:
                v_state = "UNCERTAIN"
                risk = "LOW"
                strength = effective_conf * 0.5

        elif pred_cls == "TURBID_DISCOLORATION":
            if effective_conf >= self.medium_confidence_threshold:
                v_state = "TURBID_DISCOLORATION"
                risk = "MEDIUM"
                strength = effective_conf * 0.7
            else:
                v_state = "UNCERTAIN"
                risk = "LOW"
                strength = effective_conf * 0.4

        elif pred_cls in ["NO_BLOOM", "NORMAL_WATER"]:
            if effective_conf >= self.medium_confidence_threshold:
                v_state = "NO_VISUAL_BLOOM"
                risk = "NONE"
                strength = effective_conf
            else:
                v_state = "UNCERTAIN"
                risk = "NONE"
                strength = effective_conf * 0.5

        else: # UNCERTAIN or unrecognized class
            v_state = "UNCERTAIN"
            risk = "LOW" if effective_conf >= self.low_confidence_threshold else "UNKNOWN"
            strength = effective_conf * 0.3

        # Step 7: Final Latency & Evidence Packaging
        detection_time_ms = (time.perf_counter() - start_time) * 1000.0
        total_pipeline_ms = prediction.total_pipeline_time_ms + detection_time_ms

        return VisualEvidence(
            frame_id=prediction.frame_id,
            timestamp=prediction.timestamp,
            source="COMPUTER_VISION",
            predicted_visual_class=pred_cls,
            confidence=conf,
            visual_state=v_state,
            risk_level=risk,
            evidence_strength=round(strength, 3),
            detections_count=prediction.detections_count,
            bounding_boxes=prediction.bounding_boxes,
            highest_confidence_detection=highest_det,
            model_name=prediction.model_name,
            model_version=prediction.model_version,
            inference_status=prediction.status,
            preprocessing_time_ms=preproc_ms,
            inference_time_ms=infer_ms,
            visual_pipeline_time_ms=round(total_pipeline_ms, 3),
            metadata={
                "detection_evaluation_time_ms": round(detection_time_ms, 3),
                "thresholds": {
                    "high": self.high_confidence_threshold,
                    "medium": self.medium_confidence_threshold,
                    "low": self.low_confidence_threshold
                },
                "model_metadata": prediction.metadata,
                "temporal_reasons": temp_res.reasons
            },
            q_visual=q_visual,
            quality_state=quality_state,
            effective_confidence=effective_conf,
            temporal_consistency=temp_res.temporal_consistency,
            frames_evaluated=temp_res.frames_evaluated,
            consistency_state=temp_res.consistency_state,
            quality_flags=quality_flags,
            optical_quality=opt_dict
        )
