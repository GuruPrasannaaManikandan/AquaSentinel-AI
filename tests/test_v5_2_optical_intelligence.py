import io
import pytest
import datetime
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from src.cv.camera_driver import CameraFrame
from src.cv.image_preprocessing import ImagePreprocessor, PreprocessedImage
from src.cv.cv_model import CVPrediction, AquaticBloomCVModel
from src.cv.visual_detection import VisualEvidence, VisualDetector
from src.cv.optical_quality import OpticalQualityEvaluator, OpticalQualityResult
from src.cv.temporal_visual import TemporalVisualBuffer, TemporalVisualConsistencyResult
from src.iot.sensor_quality import SensorQualityEvaluator
from src.fusion.runtime_orchestrator import MultimodalRuntimeOrchestrator


def generate_synthetic_image(mode: str = "NORMAL") -> bytes:
    """Generates synthetic JPEG bytes for deterministic optical testing."""
    if mode == "CORRUPTED":
        return b"CORRUPTED_NOT_A_VALID_JPEG_DATA_STREAM"

    img = Image.new("RGB", (224, 224), color=(128, 128, 128))
    draw = ImageDraw.Draw(img)

    if mode == "NORMAL":
        # Rich geometric patterns with high contrast and edge density
        for i in range(0, 224, 14):
            draw.line([(i, 0), (224 - i, 224)], fill=((i * 7) % 255, (i * 3) % 255, (i * 5) % 255), width=3)
            draw.rectangle([i // 2, i // 2, 224 - i // 2, 224 - i // 2], outline=((i * 4) % 255, 120, 180), width=2)
    elif mode == "BLURRED":
        # Create patterned image then heavily blur it
        for i in range(0, 224, 14):
            draw.line([(i, 0), (224 - i, 224)], fill=((i * 7) % 255, (i * 3) % 255, (i * 5) % 255), width=3)
        img = img.filter(ImageFilter.GaussianBlur(radius=12))
    elif mode == "DARK":
        # Severe underexposure
        img = Image.new("RGB", (224, 224), color=(8, 10, 12))
    elif mode == "OVEREXPOSED":
        # Severe overexposure
        img = Image.new("RGB", (224, 224), color=(248, 250, 252))
    elif mode == "LOW_INFORMATION":
        # Flat monochromatic field
        img = Image.new("RGB", (224, 224), color=(128, 128, 128))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def make_prediction(
    frame_id: str = "f_test",
    timestamp: str = "2026-08-26T12:00:00Z",
    predicted_class: str = "NORMAL_WATER",
    confidence: float = 0.90,
    status: str = "SUCCESS",
    metadata: dict = None
) -> CVPrediction:
    """Helper to construct valid CVPrediction instances for testing."""
    dangerous = predicted_class in ["ALGAL_BLOOM", "ALGAL_BLOOM_RISK"]
    return CVPrediction(
        frame_id=frame_id,
        timestamp=timestamp,
        predicted_class=predicted_class,
        confidence=confidence,
        dangerous_visual_class=dangerous,
        detections_count=1 if dangerous else 0,
        bounding_boxes=[{"class": predicted_class, "confidence": confidence}] if dangerous else [],
        inference_time_ms=10.0,
        preprocessing_time_ms=3.0,
        total_pipeline_time_ms=13.0,
        model_name="MobileNetV3-Small",
        model_version="1.0.0",
        status=status,
        metadata=metadata or {}
    )


class TestV52OpticalIntelligence:
    """
    Comprehensive verification suite for V5.2 Advanced Optical Quality & Multi-Frame Vision.
    Tests optical evaluation, sharpness, exposure, entropy, bounds, determinism,
    effective confidence discounting, multi-frame consistency (K=3), and backward compatibility.
    """

    @pytest.fixture
    def evaluator(self):
        return OpticalQualityEvaluator()

    @pytest.fixture
    def preprocessor(self):
        return ImagePreprocessor(target_size=(224, 224))

    @pytest.fixture
    def detector(self):
        return VisualDetector(high_confidence_threshold=0.85, medium_confidence_threshold=0.60)

    # 1. Valid Image Quality
    def test_valid_image_quality(self, evaluator):
        raw_bytes = generate_synthetic_image("NORMAL")
        res = evaluator.evaluate_image(raw_bytes, frame_id="f_normal")

        assert isinstance(res, OpticalQualityResult)
        assert 0.80 <= res.q_visual <= 1.0
        assert res.quality_state in ["RELIABLE", "ACCEPTABLE"]
        assert res.sharpness_variance > 100.0
        assert 70.0 <= res.mean_luminance <= 190.0
        assert res.entropy_score >= 4.0
        assert "BLURRED" not in res.quality_flags
        assert "DARK" not in res.quality_flags
        assert "OVEREXPOSED" not in res.quality_flags

    # 2. Blur Detection
    def test_blur_detection(self, evaluator):
        raw_bytes = generate_synthetic_image("BLURRED")
        res = evaluator.evaluate_image(raw_bytes, frame_id="f_blur")

        assert "BLURRED" in res.quality_flags
        assert res.sharpness_variance < 100.0
        assert res.q_visual < 0.70
        assert res.quality_state in ["DEGRADED", "UNRELIABLE"]
        assert any("blurred" in r.lower() for r in res.reason_codes)

    # 3. Dark Frame Detection
    def test_dark_frame_detection(self, evaluator):
        raw_bytes = generate_synthetic_image("DARK")
        res = evaluator.evaluate_image(raw_bytes, frame_id="f_dark")

        assert "DARK" in res.quality_flags
        assert res.mean_luminance < 30.0
        assert res.q_visual < 0.50
        assert res.quality_state in ["DEGRADED", "UNRELIABLE"]
        assert any("underexposure" in r.lower() for r in res.reason_codes)

    # 4. Overexposure Detection
    def test_overexposure_detection(self, evaluator):
        raw_bytes = generate_synthetic_image("OVEREXPOSED")
        res = evaluator.evaluate_image(raw_bytes, frame_id="f_over")

        assert "OVEREXPOSED" in res.quality_flags
        assert res.mean_luminance > 225.0
        assert res.q_visual < 0.50
        assert res.quality_state in ["DEGRADED", "UNRELIABLE"]
        assert any("overexposure" in r.lower() for r in res.reason_codes)

    # 5. Low Information Detection
    def test_low_information_detection(self, evaluator):
        raw_bytes = generate_synthetic_image("LOW_INFORMATION")
        res = evaluator.evaluate_image(raw_bytes, frame_id="f_low_info")

        assert any(f in res.quality_flags for f in ["LOW_INFORMATION", "LOW_CONTRAST"])
        assert res.entropy_score < 3.5
        assert res.q_visual < 0.60
        assert res.quality_state in ["DEGRADED", "UNRELIABLE"]

    # 6. Corrupt Image Handling (No Runtime Crash)
    def test_corrupt_image(self, evaluator):
        raw_bytes = generate_synthetic_image("CORRUPTED")
        res = evaluator.evaluate_image(raw_bytes, frame_id="f_corrupt")

        assert res.q_visual == 0.0
        assert res.quality_state == "CORRUPTED"
        assert "CORRUPTED" in res.quality_flags
        assert any("corrupt" in r.lower() or "stream" in r.lower() for r in res.reason_codes)

    # 7. Quality Bounds Guarantee
    def test_quality_bounds(self, evaluator):
        rng = np.random.default_rng(54321)
        for i in range(50):
            # Random noise arrays
            arr = rng.integers(0, 256, size=(100, 100, 3), dtype=np.uint8)
            res = evaluator.evaluate_image(arr, frame_id=f"f_rand_{i}")
            assert 0.0 <= res.q_visual <= 1.0
            assert 0.0 <= res.sharpness_score <= 1.0
            assert 0.0 <= res.exposure_score <= 1.0
            assert 0.0 <= res.contrast_score <= 1.0

    # 8. Quality Determinism
    def test_quality_determinism(self, evaluator):
        raw_bytes = generate_synthetic_image("NORMAL")
        res1 = evaluator.evaluate_image(raw_bytes)
        res2 = evaluator.evaluate_image(raw_bytes)

        assert res1.q_visual == res2.q_visual
        assert res1.sharpness_variance == res2.sharpness_variance
        assert res1.mean_luminance == res2.mean_luminance
        assert res1.quality_flags == res2.quality_flags

    # 9. Raw Model Confidence Preserved
    def test_raw_model_confidence_preserved(self, detector):
        pred = make_prediction(
            frame_id="f_trace",
            timestamp="2026-08-26T12:00:00Z",
            predicted_class="ALGAL_BLOOM",
            confidence=0.88,
            metadata={"source_metadata": {"optical_quality": {"q_visual": 0.50, "quality_state": "DEGRADED"}}}
        )
        ev = detector.evaluate_prediction(pred)

        # Raw confidence must be strictly preserved
        assert ev.confidence == 0.88
        assert ev.q_visual == 0.50
        assert ev.effective_confidence == round(0.88 * 0.50, 4)

    # 10. Visual Quality Reduces Effective Confidence
    def test_visual_quality_reduces_effective_confidence(self, detector):
        pred_good = make_prediction(
            frame_id="f_good",
            timestamp="2026-08-26T12:00:00Z",
            predicted_class="ALGAL_BLOOM",
            confidence=0.90,
            metadata={"source_metadata": {"optical_quality": {"q_visual": 0.95, "quality_state": "RELIABLE"}}}
        )
        pred_bad = make_prediction(
            frame_id="f_bad",
            timestamp="2026-08-26T12:00:01Z",
            predicted_class="ALGAL_BLOOM",
            confidence=0.90,
            metadata={"source_metadata": {"optical_quality": {"q_visual": 0.35, "quality_state": "UNRELIABLE"}}}
        )
        ev_good = detector.evaluate_prediction(pred_good)
        ev_bad = detector.evaluate_prediction(pred_bad)

        assert ev_good.effective_confidence > 0.80
        assert ev_bad.effective_confidence < 0.40
        assert ev_bad.visual_state == "UNCERTAIN"
        assert ev_bad.quality_state == "UNRELIABLE"

    # 11. Three-Frame Consistency
    def test_three_frame_consistency(self):
        buffer = TemporalVisualBuffer(window_size_k=3)
        t0 = datetime.datetime(2026, 8, 26, 12, 0, 0)

        # Feed 3 consecutive consistent normal frames
        res = None
        for i in range(3):
            t = (t0 + datetime.timedelta(seconds=i * 5)).isoformat()
            res = buffer.add_frame(
                frame_id=f"f_{i}",
                timestamp=t,
                predicted_class="NORMAL_WATER",
                raw_confidence=0.90,
                q_visual=0.95
            )

        assert res.consistency_state == "CONSISTENT_NORMAL"
        assert res.temporal_consistency == 1.0
        assert res.is_consistent is True
        assert res.frames_evaluated == 3

    # 12. Single Transient Frame Does Not Establish Strong Evidence
    def test_single_transient_frame(self):
        buffer = TemporalVisualBuffer(window_size_k=3)
        t0 = datetime.datetime(2026, 8, 26, 12, 0, 0)

        # Frame 0: NORMAL
        buffer.add_frame("f0", t0.isoformat(), "NORMAL_WATER", 0.90, 0.95)
        # Frame 1: Transient BLOOM
        t1 = (t0 + datetime.timedelta(seconds=5)).isoformat()
        res_bloom = buffer.add_frame("f1", t1, "ALGAL_BLOOM", 0.92, 0.95)

        assert res_bloom.consistency_state == "TRANSIENT_BLOOM"
        assert res_bloom.is_transient is True
        assert res_bloom.is_consistent is False
        assert res_bloom.temporal_consistency <= 0.35

    # 13. Consistent Bloom Sequence
    def test_consistent_bloom_sequence(self):
        buffer = TemporalVisualBuffer(window_size_k=3)
        t0 = datetime.datetime(2026, 8, 26, 12, 0, 0)

        res = None
        for i in range(3):
            t = (t0 + datetime.timedelta(seconds=i * 5)).isoformat()
            res = buffer.add_frame(
                frame_id=f"f_bloom_{i}",
                timestamp=t,
                predicted_class="ALGAL_BLOOM",
                raw_confidence=0.92,
                q_visual=0.90
            )

        assert res.consistency_state == "CONSISTENT_BLOOM"
        assert res.is_consistent is True
        assert res.temporal_consistency == 1.0
        assert res.effective_confidence > 0.75

    # 14. Conflicting Sequence Flags Ambiguity
    def test_conflicting_sequence(self):
        buffer = TemporalVisualBuffer(window_size_k=3)
        t0 = datetime.datetime(2026, 8, 26, 12, 0, 0)

        # Normal -> Bloom -> Normal
        buffer.add_frame("f0", (t0 + datetime.timedelta(seconds=0)).isoformat(), "NORMAL_WATER", 0.90, 0.95)
        buffer.add_frame("f1", (t0 + datetime.timedelta(seconds=5)).isoformat(), "ALGAL_BLOOM", 0.91, 0.95)
        res = buffer.add_frame("f2", (t0 + datetime.timedelta(seconds=10)).isoformat(), "NORMAL_WATER", 0.89, 0.95)

        assert res.consistency_state == "TRANSIENT_BLOOM"
        assert res.is_consistent is False

        # Bloom -> Normal -> Bloom (oscillating conflicting)
        buffer.clear()
        buffer.add_frame("f0", (t0 + datetime.timedelta(seconds=0)).isoformat(), "ALGAL_BLOOM", 0.90, 0.95)
        buffer.add_frame("f1", (t0 + datetime.timedelta(seconds=5)).isoformat(), "NORMAL_WATER", 0.91, 0.95)
        res_alt = buffer.add_frame("f2", (t0 + datetime.timedelta(seconds=10)).isoformat(), "ALGAL_BLOOM", 0.89, 0.95)

        assert res_alt.consistency_state in ["AMBIGUOUS", "TRANSIENT_BLOOM"]
        assert res_alt.temporal_consistency < 0.50

    # 15. Mixed Quality Sequence
    def test_mixed_quality_sequence(self):
        buffer = TemporalVisualBuffer(window_size_k=3)
        t0 = datetime.datetime(2026, 8, 26, 12, 0, 0)

        # Good Bloom -> Blurred Bloom -> Good Bloom
        buffer.add_frame("f0", (t0 + datetime.timedelta(seconds=0)).isoformat(), "ALGAL_BLOOM", 0.92, 0.95)
        buffer.add_frame("f1", (t0 + datetime.timedelta(seconds=5)).isoformat(), "ALGAL_BLOOM", 0.85, 0.40)
        res = buffer.add_frame("f2", (t0 + datetime.timedelta(seconds=10)).isoformat(), "ALGAL_BLOOM", 0.91, 0.95)

        # Mean Q_visual is reduced by the blurred middle frame
        assert res.mean_q_visual < 0.85
        assert res.frames_evaluated == 3

    # 16. Frame Age Handling
    def test_frame_age_handling(self):
        buffer = TemporalVisualBuffer(window_size_k=3, max_frame_age_seconds=20.0)
        t0 = datetime.datetime(2026, 8, 26, 12, 0, 0)

        # Frame 0 and Frame 1 with 45s gap (> 20s max age)
        buffer.add_frame("f0", t0.isoformat(), "NORMAL_WATER", 0.90, 0.95)
        t1 = (t0 + datetime.timedelta(seconds=45)).isoformat()
        res = buffer.add_frame("f1", t1, "NORMAL_WATER", 0.90, 0.95)

        assert any("span" in r.lower() for r in res.reasons)
        assert res.temporal_consistency < 1.0

    # 17. Provenance Preserved Across Pipeline
    def test_provenance_preserved(self, preprocessor, detector):
        raw_bytes = generate_synthetic_image("NORMAL")
        frame = CameraFrame(
            frame_id="cam_prov_123",
            timestamp="2026-08-26T12:34:56Z",
            width=224,
            height=224,
            channels=3,
            format="JPEG",
            image_bytes=raw_bytes,
            status="OK"
        )
        preproc = preprocessor.process(frame)
        assert preproc.frame_id == "cam_prov_123"
        assert preproc.timestamp == "2026-08-26T12:34:56Z"
        assert "optical_quality" in preproc.metadata
        assert 0.0 <= preproc.metadata["q_visual"] <= 1.0

        model = AquaticBloomCVModel()
        model.load()
        pred = model.predict(preproc)
        ev = detector.evaluate_prediction(pred)

        assert ev.frame_id == "cam_prov_123"
        assert ev.timestamp == "2026-08-26T12:34:56Z"
        assert ev.q_visual == preproc.metadata["q_visual"]

    # 18. V5.1 Sensor Quality Compatibility
    def test_v5_1_sensor_quality_compatibility(self):
        # Ensure Q_sensor and Q_visual run side by side without interference
        sensor_eval = SensorQualityEvaluator()
        optical_eval = OpticalQualityEvaluator()

        reading = {"temperature_c": 23.0, "ph": 7.4, "turbidity_ntu": 3.0, "salinity_ppt": 0.2, "dissolved_oxygen_mg_l": 8.2}
        sq_res = sensor_eval.evaluate(reading, timestamp="2026-08-26T12:00:00Z")

        raw_bytes = generate_synthetic_image("NORMAL")
        oq_res = optical_eval.evaluate_image(raw_bytes, frame_id="f_multimodal")

        assert 0.0 <= sq_res.overall_quality <= 1.0
        assert 0.0 <= oq_res.q_visual <= 1.0
        assert sq_res.validation_state in ["RELIABLE", "DEGRADED"]
        assert oq_res.quality_state in ["RELIABLE", "ACCEPTABLE"]

    # 19. Backward Compatibility with V4 Visual Detection
    def test_v4_backward_compatibility(self, detector):
        # Legacy prediction evaluation without optical quality in metadata
        pred_legacy = make_prediction(
            frame_id="f_legacy",
            timestamp="2026-08-26T12:00:00Z",
            predicted_class="NORMAL_WATER",
            confidence=0.88,
            status="SUCCESS"
        )
        ev = detector.evaluate_prediction(pred_legacy)

        assert isinstance(ev, VisualEvidence)
        assert ev.visual_state == "NO_VISUAL_BLOOM"
        assert ev.risk_level == "NONE"
        assert ev.confidence == 0.88
        assert ev.q_visual == 1.0
        assert ev.effective_confidence == 0.88
