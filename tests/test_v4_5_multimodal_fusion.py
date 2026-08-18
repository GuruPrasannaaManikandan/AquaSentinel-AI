import io
import unittest
import numpy as np
from PIL import Image, ImageDraw

from src.cv.camera_driver import CameraFrame, VirtualCameraDriver
from src.cv.image_preprocessing import ImagePreprocessor
from src.cv.cv_model import AquaticBloomCVModel
from src.cv.visual_detection import VisualDetector, VisualEvidence
from src.fusion.fusion_engine import FusionEngine

class TestV45MultimodalFusion(unittest.TestCase):
    def setUp(self):
        self.fusion_engine = FusionEngine()
        self.camera = VirtualCameraDriver(name="TEST_CAM_V45", resolution=(640, 480))
        self.camera.init()
        self.preprocessor = ImagePreprocessor(target_size=(224, 224), color_space="RGB", normalization_type="RESCALE")
        self.cv_model = AquaticBloomCVModel()
        self.cv_model.load()
        self.visual_detector = VisualDetector()

        self.mock_ml_normal = {
            "dataset": "caml",
            "predicted_class": 0,
            "class_probabilities": {0: 0.90, 1: 0.10},
            "confidence": 0.90,
            "dangerous_class": False,
            "model_id": "RandomForest-v1.0.0"
        }
        self.mock_ml_dangerous = {
            "dataset": "caml",
            "predicted_class": 4,
            "class_probabilities": {0: 0.10, 4: 0.90},
            "confidence": 0.90,
            "dangerous_class": True,
            "model_id": "RandomForest-v1.0.0"
        }
        self.mock_ais_normal = {
            "dataset": "caml",
            "is_anomaly": False,
            "anomaly_score": 0.10,
            "matched_detector_count": 5,
            "nearest_detector_distance": 0.05,
            "ais_model_id": "NSA-v1.0.0"
        }
        self.mock_ais_anomaly = {
            "dataset": "caml",
            "is_anomaly": True,
            "anomaly_score": 0.85,
            "matched_detector_count": 0,
            "nearest_detector_distance": 0.95,
            "ais_model_id": "NSA-v1.0.0"
        }

    def test_sensor_only_backward_compatibility(self):
        """Verifies that visual_evidence=None returns identical V3 sensor output."""
        res = self.fusion_engine.fuse(self.mock_ml_normal, self.mock_ais_normal)
        self.assertEqual(res["fusion"]["final_state"], "NORMAL")
        self.assertEqual(res["fusion"]["reason_code"], "ML_NORMAL_AIS_NORMAL")
        self.assertFalse(res["fusion"]["multimodal"])
        self.assertNotIn("visual_evidence", res)

    def test_multimodal_bloom_confirmed(self):
        """Sensor threat + Visual BLOOM_EVIDENCE -> CRITICAL (MULTIMODAL_BLOOM_CONFIRMED)."""
        visual_ev = VisualEvidence(
            frame_id="F001",
            timestamp="2026-08-17T22:00:00Z",
            predicted_visual_class="ALGAL_BLOOM",
            confidence=0.95,
            visual_state="BLOOM_EVIDENCE",
            risk_level="HIGH",
            evidence_strength=0.95,
            model_name="MobileNetV3",
            model_version="1.0.0",
            inference_status="SUCCESS"
        )
        res = self.fusion_engine.fuse(self.mock_ml_dangerous, self.mock_ais_normal, visual_evidence=visual_ev)
        self.assertEqual(res["fusion"]["final_state"], "CRITICAL")
        self.assertEqual(res["fusion"]["reason_code"], "MULTIMODAL_BLOOM_CONFIRMED")
        self.assertTrue(res["fusion"]["multimodal"])
        self.assertIsNotNone(res["visual_evidence"])

    def test_visual_early_warning(self):
        """Sensor normal + Visual BLOOM_EVIDENCE (HIGH risk) -> WARNING (VISUAL_EARLY_WARNING)."""
        visual_ev = VisualEvidence(
            frame_id="F002",
            timestamp="2026-08-17T22:01:00Z",
            predicted_visual_class="ALGAL_BLOOM",
            confidence=0.92,
            visual_state="BLOOM_EVIDENCE",
            risk_level="HIGH",
            evidence_strength=0.92,
            model_name="MobileNetV3",
            model_version="1.0.0",
            inference_status="SUCCESS"
        )
        res = self.fusion_engine.fuse(self.mock_ml_normal, self.mock_ais_normal, visual_evidence=visual_ev)
        self.assertEqual(res["fusion"]["final_state"], "WARNING")
        self.assertEqual(res["fusion"]["reason_code"], "VISUAL_EARLY_WARNING")
        self.assertTrue(res["fusion"]["multimodal"])

    def test_visual_disconfirmed_normal(self):
        """Sensor ML low confidence warning + Visual NO_VISUAL_BLOOM -> NORMAL (VISUAL_DISCONFIRMED_NORMAL)."""
        ml_low_conf = self.mock_ml_dangerous.copy()
        ml_low_conf["confidence"] = 0.40  # LOW confidence

        visual_ev = VisualEvidence(
            frame_id="F003",
            timestamp="2026-08-17T22:02:00Z",
            predicted_visual_class="NORMAL_WATER",
            confidence=0.98,
            visual_state="NO_VISUAL_BLOOM",
            risk_level="NONE",
            evidence_strength=0.98,
            model_name="MobileNetV3",
            model_version="1.0.0",
            inference_status="SUCCESS"
        )
        res = self.fusion_engine.fuse(ml_low_conf, self.mock_ais_normal, visual_evidence=visual_ev)
        self.assertEqual(res["fusion"]["final_state"], "NORMAL")
        self.assertEqual(res["fusion"]["reason_code"], "VISUAL_DISCONFIRMED_NORMAL")
        self.assertTrue(res["fusion"]["multimodal"])

    def test_camera_fault_handling(self):
        """Camera fault retains sensor decision, flagging VISUAL_CAMERA_FAULT."""
        visual_ev_fault = VisualEvidence(
            frame_id="F004",
            timestamp="2026-08-17T22:03:00Z",
            predicted_visual_class="UNCERTAIN",
            confidence=0.0,
            visual_state="CAMERA_FAULT",
            risk_level="UNKNOWN",
            evidence_strength=0.0,
            model_name="MobileNetV3",
            model_version="1.0.0",
            inference_status="CORRUPTED"
        )
        res = self.fusion_engine.fuse(self.mock_ml_dangerous, self.mock_ais_normal, visual_evidence=visual_ev_fault)
        self.assertEqual(res["fusion"]["final_state"], "WARNING")
        self.assertEqual(res["fusion"]["reason_code"], "VISUAL_CAMERA_FAULT")

    def test_end_to_end_v41_to_v45_hardware_pipeline(self):
        """Full acquisition -> preprocessing -> MobileNetV3 -> VisualDetector -> FusionEngine path."""
        # Create simulated 1920x1080 JPEG frame with bloom scum texture
        img = Image.new("RGB", (1920, 1080), color=(15, 170, 35))
        draw = ImageDraw.Draw(img)
        for _ in range(30):
            x0 = np.random.randint(0, 1500)
            y0 = np.random.randint(0, 800)
            x1 = x0 + np.random.randint(100, 400)
            y1 = y0 + np.random.randint(100, 300)
            draw.ellipse([x0, y0, x1, y1], fill=(5, 220, 20))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        frame = CameraFrame(
            frame_id="HW_CAM_001",
            timestamp="2026-08-17T22:05:00Z",
            width=1920, height=1080, channels=3, format="JPEG",
            image_bytes=buf.getvalue(), quality_valid=True, status="OK"
        )

        preproc = self.preprocessor.process(frame)
        pred = self.cv_model.predict(preproc)
        vis_ev = self.visual_detector.evaluate_prediction(pred)

        fused = self.fusion_engine.fuse(self.mock_ml_dangerous, self.mock_ais_normal, visual_evidence=vis_ev)

        self.assertEqual(fused["fusion"]["final_state"], "CRITICAL")
        self.assertEqual(fused["fusion"]["reason_code"], "MULTIMODAL_BLOOM_CONFIRMED")
        self.assertTrue(fused["fusion"]["multimodal"])
        self.assertGreater(fused["system_metadata"]["fusion_pipeline_time_ms"], 0.0)

    def test_multimodal_fusion_latency(self):
        """Measures execution latency of multimodal fusion engine."""
        vis_ev = VisualEvidence(
            frame_id="F005",
            timestamp="2026-08-17T22:06:00Z",
            predicted_visual_class="ALGAL_BLOOM",
            confidence=0.90,
            visual_state="BLOOM_EVIDENCE",
            risk_level="HIGH",
            evidence_strength=0.90,
            model_name="MobileNetV3",
            model_version="1.0.0",
            inference_status="SUCCESS"
        )
        res = self.fusion_engine.fuse(self.mock_ml_normal, self.mock_ais_normal, visual_evidence=vis_ev)
        self.assertLess(res["system_metadata"]["fusion_pipeline_time_ms"], 5.0)  # Should take under 5ms

if __name__ == "__main__":
    unittest.main()
