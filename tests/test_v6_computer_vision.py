"""
tests/test_v6_computer_vision.py
================================
V6 Computer Vision Comprehensive Verification Suite.

Validates the 12 mandatory failure & operational scenarios:
1. Clear water -> NORMAL_WATER
2. Clear water + high quality -> Strong normal evidence
3. Algal bloom -> ALGAL_BLOOM / BLOOM_EVIDENCE
4. Turbid water -> TURBID_DISCOLORATION / TURBIDITY_EVIDENCE
5. Blurry image -> DEGRADED_VISUAL / UNCERTAIN
6. Overexposed image -> DEGRADED_VISUAL
7. Glare -> Reduced Q_visual with GLARE_DETECTED flag
8. Stale frame -> Stale frame rejected (>30s)
9. Camera disconnected -> CAMERA_FAULT / CAMERA_OFFLINE
10. Intermittent camera -> Graceful recovery with fault_recovered=True
11. Conflict: Sensor bloom risk vs camera normal -> Handled by fusion engine
12. Multimodal confirmation: Sensor bloom + visual bloom -> Elevates to CRITICAL / BLOOM_CONFIRMED

Also validates Gateway frame ingestion, caching, and FastAPI REST endpoint.
"""

import io
import time
import base64
import datetime
import pytest
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from src.cv.camera_driver import (
    CameraFrame,
    CameraAcquisitionManager,
    CameraAcquisitionStatus,
    VirtualCameraDriver,
)
from src.cv.optical_quality import (
    OpticalQualityEvaluator,
    OpticalQualityResult,
    VisualQualityResult,
)
from src.cv.cv_model import CVPrediction, AquaticBloomCVModel
from src.cv.visual_detection import (
    VisualDetector,
    VisualEvidence,
    VisualDetectionResult,
)
from src.cv.temporal_visual import (
    TemporalVisualBuffer,
    TemporalVisualConsistencyResult,
)
from src.fusion.fusion_engine import MultimodalFusionEngine
from src.fusion.decision_pipeline import DecisionPipeline
from src.iot.gateway import IoTEdgeGateway


def create_synthetic_image(mode: str = "NORMAL") -> bytes:
    """Helper to generate synthetic JPEG images for CV testing."""
    img = Image.new("RGB", (224, 224), color=(128, 128, 128))
    draw = ImageDraw.Draw(img)

    if mode == "NORMAL":
        # Clear water pattern with edges
        for i in range(0, 224, 16):
            draw.line([(i, 0), (224 - i, 224)], fill=(40, 120, 200), width=2)
            draw.rectangle([i // 2, i // 2, 224 - i // 2, 224 - i // 2], outline=(30, 90, 160), width=2)
    elif mode == "BLURRED":
        for i in range(0, 224, 16):
            draw.line([(i, 0), (224 - i, 224)], fill=(40, 120, 200), width=2)
        img = img.filter(ImageFilter.GaussianBlur(radius=15))
    elif mode == "OVEREXPOSED":
        img = Image.new("RGB", (224, 224), color=(250, 252, 255))
    elif mode == "DARK":
        img = Image.new("RGB", (224, 224), color=(10, 10, 15))
    elif mode == "GLARE":
        # Base image with a high-intensity specular highlight covering ~15% area
        for i in range(0, 224, 16):
            draw.line([(i, 0), (224 - i, 224)], fill=(40, 120, 200), width=2)
        # Add bright specular spot (>=250)
        draw.ellipse([60, 60, 160, 160], fill=(255, 255, 255))
    elif mode == "CORRUPTED":
        return b"NOT_A_VALID_JPEG_STREAM"

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def build_mock_prediction(
    predicted_class: str,
    confidence: float,
    frame_id: str = "f_test",
    timestamp: str = None,
    q_visual: float = 0.95,
    quality_state: str = "RELIABLE"
) -> CVPrediction:
    """Helper to build a deterministic CVPrediction."""
    if timestamp is None:
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return CVPrediction(
        frame_id=frame_id,
        timestamp=timestamp,
        predicted_class=predicted_class,
        confidence=confidence,
        dangerous_visual_class=predicted_class in ["ALGAL_BLOOM", "ALGAL_BLOOM_RISK"],
        detections_count=1 if predicted_class in ["ALGAL_BLOOM", "ALGAL_BLOOM_RISK"] else 0,
        bounding_boxes=[{"class": predicted_class, "confidence": confidence}] if predicted_class in ["ALGAL_BLOOM", "ALGAL_BLOOM_RISK"] else [],
        inference_time_ms=12.0,
        preprocessing_time_ms=4.0,
        total_pipeline_time_ms=16.0,
        model_name="MobileNetV3-Small",
        model_version="1.0.0",
        status="SUCCESS",
        metadata={"source_metadata": {"optical_quality": {"q_visual": q_visual, "quality_state": quality_state}}}
    )


class TestV6ComputerVision:
    """
    Verification suite for V6 Computer Vision release.
    """

    @pytest.fixture
    def optical_evaluator(self):
        return OpticalQualityEvaluator()

    @pytest.fixture
    def visual_detector(self):
        return VisualDetector(high_confidence_threshold=0.85, medium_confidence_threshold=0.60)

    @pytest.fixture
    def acquisition_manager(self):
        return CameraAcquisitionManager(acquisition_timeout_sec=5.0, max_frame_age_sec=30.0)

    @pytest.fixture
    def temporal_buffer(self):
        return TemporalVisualBuffer(window_size_k=3)

    # -------------------------------------------------------------------------
    # Scenario 1: Clear water -> NORMAL_WATER
    # -------------------------------------------------------------------------
    def test_scenario_01_clear_water_classification(self, visual_detector):
        """Scenario 1: Clear water is classified as NORMAL_WATER / NO_VISUAL_BLOOM."""
        pred = build_mock_prediction(predicted_class="NORMAL_WATER", confidence=0.92)
        ev = visual_detector.evaluate_prediction(pred)

        assert ev.visual_state == "NO_VISUAL_BLOOM"
        assert ev.predicted_visual_class == "NORMAL_WATER"
        assert ev.risk_level == "NONE"

        res = ev.to_visual_detection_result()
        assert isinstance(res, VisualDetectionResult)
        assert res.class_name == "NORMAL_WATER"
        assert res.evidence_state in ["NORMAL_WATER", "NO_VISUAL_BLOOM"]
        assert res.valid is True

    # -------------------------------------------------------------------------
    # Scenario 2: Clear water + high quality -> Strong normal evidence
    # -------------------------------------------------------------------------
    def test_scenario_02_clear_water_strong_evidence(self, optical_evaluator, visual_detector):
        """Scenario 2: Clear water with high visual quality produces strong normal evidence."""
        raw_bytes = create_synthetic_image("NORMAL")
        opt = optical_evaluator.evaluate_image(raw_bytes, frame_id="f_clear_hq")

        assert opt.q_visual >= 0.80
        assert opt.quality_state in ["RELIABLE", "ACCEPTABLE"]

        pred = build_mock_prediction(
            predicted_class="NORMAL_WATER",
            confidence=0.94,
            q_visual=opt.q_visual,
            quality_state=opt.quality_state
        )
        ev = visual_detector.evaluate_prediction(pred)

        assert ev.visual_state == "NO_VISUAL_BLOOM"
        assert ev.effective_confidence >= 0.75
        assert ev.evidence_strength >= 0.75
        assert ev.risk_level == "NONE"
        assert ev.to_dict()["valid"] is True

    # -------------------------------------------------------------------------
    # Scenario 3: Algal bloom -> ALGAL_BLOOM / BLOOM_EVIDENCE
    # -------------------------------------------------------------------------
    def test_scenario_03_algal_bloom_evidence(self, visual_detector):
        """Scenario 3: Algal bloom model detection generates BLOOM_EVIDENCE."""
        pred = build_mock_prediction(
            predicted_class="ALGAL_BLOOM",
            confidence=0.95,
            q_visual=0.92,
            quality_state="RELIABLE"
        )
        ev = visual_detector.evaluate_prediction(pred)

        assert ev.visual_state == "BLOOM_EVIDENCE"
        assert ev.risk_level == "HIGH"
        assert ev.effective_confidence > 0.85
        assert ev.evidence_strength > 0.80

        res = ev.to_visual_detection_result()
        assert res.evidence_state == "BLOOM_EVIDENCE"
        assert res.class_name == "ALGAL_BLOOM"
        assert res.valid is True

    # -------------------------------------------------------------------------
    # Scenario 4: Turbid water -> TURBID_DISCOLORATION / TURBIDITY_EVIDENCE
    # -------------------------------------------------------------------------
    def test_scenario_04_turbid_water_evidence(self, visual_detector):
        """Scenario 4: Turbid discoloration generates turbidity evidence with MEDIUM risk."""
        pred = build_mock_prediction(
            predicted_class="TURBID_DISCOLORATION",
            confidence=0.88,
            q_visual=0.85,
            quality_state="RELIABLE"
        )
        ev = visual_detector.evaluate_prediction(pred)

        assert ev.visual_state == "TURBID_DISCOLORATION"
        assert ev.risk_level == "MEDIUM"
        assert ev.effective_confidence >= 0.60

        d = ev.to_dict()
        assert d["evidence_state"] in ["TURBID_DISCOLORATION", "TURBIDITY_EVIDENCE"]
        assert d["valid"] is True

    # -------------------------------------------------------------------------
    # Scenario 5: Blurry image -> DEGRADED_VISUAL / UNCERTAIN
    # -------------------------------------------------------------------------
    def test_scenario_05_blurry_image_degraded(self, optical_evaluator, visual_detector):
        """Scenario 5: Blurry image drops Q_visual and maps to DEGRADED_VISUAL / UNCERTAIN."""
        raw_bytes = create_synthetic_image("BLURRED")
        opt = optical_evaluator.evaluate_image(raw_bytes, frame_id="f_blurred")

        assert "BLURRED" in opt.quality_flags
        assert opt.q_visual < 0.70

        # Even if a model mistakenly predicts ALGAL_BLOOM on blur:
        pred = build_mock_prediction(
            predicted_class="ALGAL_BLOOM",
            confidence=0.80,
            q_visual=opt.q_visual,
            quality_state=opt.quality_state
        )
        ev = visual_detector.evaluate_prediction(pred)

        # Effective confidence is reduced
        assert ev.effective_confidence < 0.60
        # If Q_visual is degraded (<0.40), evidence_state becomes DEGRADED_VISUAL
        res = ev.to_visual_detection_result()
        if opt.q_visual < 0.40 or opt.quality_state in ["DEGRADED", "UNRELIABLE"]:
            assert res.evidence_state == "DEGRADED_VISUAL"
            assert res.valid is False
        else:
            assert ev.visual_state in ["UNCERTAIN", "BLOOM_EVIDENCE"]

    # -------------------------------------------------------------------------
    # Scenario 6: Overexposed image -> DEGRADED_VISUAL
    # -------------------------------------------------------------------------
    def test_scenario_06_overexposed_image_degraded(self, optical_evaluator, visual_detector):
        """Scenario 6: Overexposed saturated frame maps to DEGRADED_VISUAL, preventing false alarms."""
        raw_bytes = create_synthetic_image("OVEREXPOSED")
        opt = optical_evaluator.evaluate_image(raw_bytes, frame_id="f_overexposed")

        assert "OVEREXPOSED" in opt.quality_flags
        assert opt.q_visual < 0.50
        assert opt.quality_state in ["DEGRADED", "UNRELIABLE"]

        pred = build_mock_prediction(
            predicted_class="ALGAL_BLOOM",
            confidence=0.91,
            q_visual=opt.q_visual,
            quality_state=opt.quality_state
        )
        ev = visual_detector.evaluate_prediction(pred)

        assert ev.effective_confidence < 0.50
        res = ev.to_visual_detection_result()
        assert res.evidence_state == "DEGRADED_VISUAL"
        assert res.valid is False

    # -------------------------------------------------------------------------
    # Scenario 7: Glare -> Reduced Q_visual with GLARE_DETECTED flag
    # -------------------------------------------------------------------------
    def test_scenario_07_glare_detected(self, optical_evaluator):
        """Scenario 7: Localized specular reflection flags GLARE_DETECTED and discounts Q_visual."""
        raw_bytes = create_synthetic_image("GLARE")
        opt = optical_evaluator.evaluate_image(raw_bytes, frame_id="f_glare")

        assert "GLARE_DETECTED" in opt.quality_flags
        vq = opt.to_visual_quality_result()
        assert vq.glare is True
        assert vq.q_visual < 0.90
        assert any("glare" in r.lower() or "specular" in r.lower() for r in vq.degradation_reasons)

    # -------------------------------------------------------------------------
    # Scenario 8: Stale frame -> Stale frame rejected (>30s)
    # -------------------------------------------------------------------------
    def test_scenario_08_stale_frame_rejection(self, acquisition_manager):
        """Scenario 8: Frame older than 30s is rejected by CameraAcquisitionManager."""
        old_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=45)).isoformat()
        frame = CameraFrame(
            frame_id="f_stale",
            timestamp=old_time,
            width=224,
            height=224,
            channels=3,
            format="JPEG",
            image_bytes=create_synthetic_image("NORMAL"),
            status="OK"
        )
        status, verified_frame = acquisition_manager.receive_frame("cam_01", frame)

        assert status == CameraAcquisitionStatus.STALE_FRAME
        assert verified_frame is None or verified_frame.status == "STALE_FRAME"

    # -------------------------------------------------------------------------
    # Scenario 9: Camera disconnected -> CAMERA_FAULT / CAMERA_OFFLINE
    # -------------------------------------------------------------------------
    def test_scenario_09_camera_disconnected_fault(self, visual_detector):
        """Scenario 9: Disconnected camera produces CAMERA_FAULT / CAMERA_OFFLINE evidence."""
        # Simulated fault prediction when camera is offline
        fault_pred = CVPrediction(
            frame_id="f_offline",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            predicted_class="UNCERTAIN",
            confidence=0.0,
            dangerous_visual_class=False,
            detections_count=0,
            bounding_boxes=[],
            inference_time_ms=0.0,
            preprocessing_time_ms=0.0,
            total_pipeline_time_ms=0.0,
            model_name="MobileNetV3-Small",
            model_version="1.0.0",
            status="CAMERA_OFFLINE"
        )
        ev = visual_detector.evaluate_prediction(fault_pred)

        assert ev.visual_state == "CAMERA_FAULT"
        assert ev.risk_level == "UNKNOWN"
        assert ev.evidence_strength == 0.0

        res = ev.to_visual_detection_result()
        assert res.evidence_state == "CAMERA_FAULT"
        assert res.valid is False

    # -------------------------------------------------------------------------
    # Scenario 10: Intermittent camera -> Graceful recovery with fault_recovered=True
    # -------------------------------------------------------------------------
    def test_scenario_10_intermittent_camera_recovery(self, temporal_buffer):
        """Scenario 10: Intermittent faults followed by valid frames recover gracefully."""
        # Record hardware dropouts
        temporal_buffer.record_fault("f_err_1", "TIMEOUT")
        temporal_buffer.record_fault("f_err_2", "CORRUPTED")

        # Now a good frame arrives
        t = datetime.datetime.now(datetime.timezone.utc).isoformat()
        res = temporal_buffer.add_frame(
            frame_id="f_recov",
            timestamp=t,
            predicted_class="NORMAL_WATER",
            raw_confidence=0.92,
            q_visual=0.95
        )

        assert isinstance(res, TemporalVisualConsistencyResult)
        assert res.fault_recovered is True
        assert res.is_consistent is False  # 1 frame does not yet establish 3-frame consistent sequence
        assert res.consecutive_count == 1

        # Feed 2 more normal frames to re-establish full consistency
        res2 = temporal_buffer.add_frame("f_recov2", t, "NORMAL_WATER", 0.93, 0.95)
        res3 = temporal_buffer.add_frame("f_recov3", t, "NORMAL_WATER", 0.94, 0.95)

        assert res3.is_consistent is True
        assert res3.consistency_state == "CONSISTENT_NORMAL"
        assert res3.consecutive_count == 3
        assert res3.persistence_score == 0.0  # Zero bloom persistence

    # -------------------------------------------------------------------------
    # Scenario 11: Conflict: Sensor bloom risk vs camera normal -> Handled by fusion engine
    # -------------------------------------------------------------------------
    def test_scenario_11_sensor_bloom_camera_normal_conflict(self):
        """Scenario 11: Sensor indicates bloom risk while camera is normal water -> Discordant / Suspected."""
        fusion = MultimodalFusionEngine()

        ml_low_conf = {
            "dataset": "caml",
            "predicted_class": 4,
            "class_probabilities": {0: 0.55, 4: 0.45},
            "confidence": 0.45,
            "dangerous_class": True,
            "model_id": "RandomForest-v1.0.0"
        }
        ais_normal = {
            "dataset": "caml",
            "is_anomaly": False,
            "anomaly_score": 0.15,
            "matched_detector_count": 6,
            "nearest_detector_distance": 0.04,
            "ais_model_id": "NSA-v1.0.0"
        }
        # Visual: high quality normal water
        visual_evidence = {
            "visual_state": "NORMAL_WATER",
            "class_name": "NORMAL_WATER",
            "confidence": 0.94,
            "q_visual": 0.95,
            "effective_confidence": 0.893,
            "risk_level": "NONE",
            "evidence_state": "NORMAL_WATER"
        }

        fused = fusion.fuse(ml_low_conf, ais_normal, visual_evidence=visual_evidence)

        # Discordant / Suspected: Visual normal suppresses false critical bloom lockout
        assert fused["fusion"]["final_state"] != "CRITICAL"
        assert fused["fusion"]["reason_code"] in ["VISUAL_DISCONFIRMED_NORMAL", "ML_LOW_CONFIDENCE", "ML_NORMAL_AIS_NORMAL"]
        assert fused["fusion"]["multimodal"] is True

    # -------------------------------------------------------------------------
    # Scenario 12: Multimodal confirmation: Sensor bloom + visual bloom -> Elevates to CRITICAL
    # -------------------------------------------------------------------------
    def test_scenario_12_multimodal_bloom_confirmation(self):
        """Scenario 12: Both sensor bloom and visual bloom confirm each other, elevating to CRITICAL."""
        fusion = MultimodalFusionEngine()

        ml_dangerous = {
            "dataset": "caml",
            "predicted_class": 4,
            "class_probabilities": {0: 0.05, 4: 0.95},
            "confidence": 0.95,
            "dangerous_class": True,
            "model_id": "RandomForest-v1.0.0"
        }
        ais_normal = {
            "dataset": "caml",
            "is_anomaly": False,
            "anomaly_score": 0.20,
            "matched_detector_count": 4,
            "nearest_detector_distance": 0.08,
            "ais_model_id": "NSA-v1.0.0"
        }
        visual_evidence = {
            "visual_state": "BLOOM_EVIDENCE",
            "class_name": "ALGAL_BLOOM",
            "confidence": 0.96,
            "q_visual": 0.95,
            "effective_confidence": 0.912,
            "risk_level": "HIGH",
            "evidence_state": "BLOOM_EVIDENCE",
            "temporal_consistency": 1.0,
            "persistence_score": 0.85
        }

        fused = fusion.fuse(ml_dangerous, ais_normal, visual_evidence=visual_evidence)

        assert fused["fusion"]["final_state"] == "CRITICAL"
        assert fused["fusion"]["reason_code"] == "MULTIMODAL_BLOOM_CONFIRMED"
        assert fused["fusion"]["ecological_state"] == "BLOOM_CONFIRMED"
        assert fused["fusion"]["multimodal"] is True

    # -------------------------------------------------------------------------
    # Gateway & Pipeline Integration
    # -------------------------------------------------------------------------
    def test_gateway_frame_ingestion_and_pipeline_injection(self):
        """Test Gateway processes incoming camera frame, caches it, and injects into pipeline."""
        gateway = IoTEdgeGateway()
        raw_bytes = create_synthetic_image("NORMAL")

        # Ingest frame
        ev_dict = gateway.process_camera_frame("esp32_device_01", raw_bytes)

        assert ev_dict is not None
        assert "visual_state" in ev_dict
        assert "q_visual" in ev_dict
        assert gateway.latest_visual_evidence is not None
        assert "esp32_device_01" in gateway.latest_visual_evidence
        assert gateway.latest_visual_evidence["esp32_device_01"]["frame_id"] == ev_dict["frame_id"]

    # -------------------------------------------------------------------------
    # REST API Frame Ingestion Endpoint
    # -------------------------------------------------------------------------
    def test_rest_api_frame_endpoint(self):
        """Test POST /devices/{device_id}/frame Base64 ingestion endpoint."""
        from fastapi.testclient import TestClient
        from src.backend.app import app

        client = TestClient(app)
        raw_bytes = create_synthetic_image("NORMAL")
        b64_str = base64.b64encode(raw_bytes).decode("ascii")

        payload = {
            "image_base64": b64_str,
            "format": "JPEG",
            "width": 224,
            "height": 224,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        resp = client.post("/devices/esp32_device_01/frame", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["status"] == "SUCCESS"
        assert data["device_id"] == "esp32_device_01"
        assert "evidence_state" in data
        assert "q_visual" in data
        assert data["q_visual"] > 0.0
