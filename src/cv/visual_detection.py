import time
import logging
import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from src.cv.cv_model import CVPrediction

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
    visual_state: str = "UNCERTAIN"  # "NO_VISUAL_BLOOM", "BLOOM_EVIDENCE", "TURBID_DISCOLORATION", "UNCERTAIN", "CAMERA_FAULT", "INFERENCE_FAILURE"
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

    def evaluate_prediction(self, prediction: CVPrediction) -> VisualEvidence:
        """
        Evaluates a raw CVPrediction and returns structured VisualEvidence.
        Preserves complete provenance, latency metrics, and detection bounding boxes.
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
        if prediction.status in ["CAMERA_OFFLINE", "CORRUPTED", "EMPTY_PAYLOAD", "NULL_FRAME", "NULL_INPUT"]:
            detection_time_ms = (time.perf_counter() - start_time) * 1000.0
            total_ms = prediction.total_pipeline_time_ms + detection_time_ms
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
                metadata={"error": f"Camera hardware fault: {prediction.status}", "source_metadata": prediction.metadata}
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

        # Step 3: Detections & Bounding Box Aggregation
        highest_det = None
        if prediction.bounding_boxes and len(prediction.bounding_boxes) > 0:
            # Sort detections by confidence descending
            sorted_dets = sorted(prediction.bounding_boxes, key=lambda d: d.get("confidence", 0.0), reverse=True)
            highest_det = sorted_dets[0]

        conf = prediction.confidence
        pred_cls = prediction.predicted_class

        # Step 4: Visual State & Risk Level Interpretation
        if pred_cls in ["ALGAL_BLOOM_RISK", "ALGAL_BLOOM"]:
            if conf >= self.high_confidence_threshold:
                v_state = "BLOOM_EVIDENCE"
                risk = "HIGH"
                strength = conf
            elif conf >= self.medium_confidence_threshold:
                v_state = "BLOOM_EVIDENCE"
                risk = "MEDIUM"
                strength = conf * 0.8
            else:
                v_state = "UNCERTAIN"
                risk = "LOW"
                strength = conf * 0.5

        elif pred_cls == "TURBID_DISCOLORATION":
            if conf >= self.medium_confidence_threshold:
                v_state = "TURBID_DISCOLORATION"
                risk = "MEDIUM"
                strength = conf * 0.7
            else:
                v_state = "UNCERTAIN"
                risk = "LOW"
                strength = conf * 0.4

        elif pred_cls in ["NO_BLOOM", "NORMAL_WATER"]:
            if conf >= self.medium_confidence_threshold:
                v_state = "NO_VISUAL_BLOOM"
                risk = "NONE"
                strength = conf
            else:
                v_state = "UNCERTAIN"
                risk = "NONE"
                strength = conf * 0.5

        else: # UNCERTAIN or unrecognized class
            v_state = "UNCERTAIN"
            risk = "LOW" if conf >= self.low_confidence_threshold else "UNKNOWN"
            strength = conf * 0.3

        # Step 5: Final Latency & Evidence Packaging
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
                "model_metadata": prediction.metadata
            }
        )
