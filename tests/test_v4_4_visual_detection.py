import io
import unittest
import numpy as np
from PIL import Image, ImageDraw
from src.cv.camera_driver import CameraFrame, VirtualCameraDriver
from src.cv.image_preprocessing import PreprocessedImage, ImagePreprocessor
from src.cv.cv_model import CVPrediction, BaseCVModel, AquaticBloomCVModel
from src.cv.visual_detection import VisualEvidence, VisualDetector

class TestV44VisualDetection(unittest.TestCase):
    def setUp(self):
        self.camera = VirtualCameraDriver(name="TEST_CAM_VIRTUAL", resolution=(640, 480))
        self.camera.init()
        self.processor = ImagePreprocessor(target_size=(224, 224), color_space="RGB", normalization_type="RESCALE")
        self.model = AquaticBloomCVModel(model_name="YOLOv8-AquaticBloom", model_version="1.0.0")
        self.model.load()
        self.detector = VisualDetector(high_confidence_threshold=0.85, medium_confidence_threshold=0.60)

    def test_no_bloom_prediction_evaluation(self):
        self.camera.set_scenario("NORMAL")
        frame = self.camera.capture_frame()
        preproc = self.processor.process(frame)
        pred = self.model.predict(preproc)
        ev = self.detector.evaluate_prediction(pred)

        self.assertIsInstance(ev, VisualEvidence)
        self.assertEqual(ev.frame_id, frame.frame_id)
        self.assertEqual(ev.timestamp, frame.timestamp)
        self.assertEqual(ev.source, "COMPUTER_VISION")
        self.assertIn(ev.predicted_visual_class, ["NO_BLOOM", "NORMAL_WATER"])
        self.assertEqual(ev.visual_state, "NO_VISUAL_BLOOM")
        self.assertEqual(ev.risk_level, "NONE")
        self.assertGreaterEqual(ev.confidence, 0.5)
        self.assertGreater(ev.visual_pipeline_time_ms, 0.0)

    def test_bloom_risk_prediction_evaluation(self):
        self.camera.set_scenario("KNOWN_BLOOM_RISK")
        frame = self.camera.capture_frame()
        preproc = self.processor.process(frame)
        pred = self.model.predict(preproc)
        ev = self.detector.evaluate_prediction(pred)

        self.assertIn(ev.predicted_visual_class, ["ALGAL_BLOOM_RISK", "ALGAL_BLOOM"])
        self.assertEqual(ev.visual_state, "BLOOM_EVIDENCE")
        self.assertIn(ev.risk_level, ["MEDIUM", "HIGH"])
        self.assertGreater(ev.evidence_strength, 0.5)
        self.assertGreater(ev.detections_count, 0)
        self.assertIsNotNone(ev.highest_confidence_detection)
        self.assertEqual(ev.highest_confidence_detection["class"], "ALGAL_BLOOM")

    def test_turbid_discoloration_evaluation(self):
        self.camera.set_scenario("ENVIRONMENTAL_STRESS")
        frame = self.camera.capture_frame()
        preproc = self.processor.process(frame)
        pred = self.model.predict(preproc)
        ev = self.detector.evaluate_prediction(pred)

        self.assertIn(ev.visual_state, ["TURBID_DISCOLORATION", "NO_VISUAL_BLOOM", "UNCERTAIN"])
        self.assertIn(ev.risk_level, ["NONE", "LOW", "MEDIUM"])

    def test_high_vs_low_confidence_interpretation(self):
        # Create artificial high-confidence bloom prediction
        pred_high = CVPrediction(
            frame_id="f_high", timestamp="2026-08-17T21:00:00Z",
            predicted_class="ALGAL_BLOOM_RISK", confidence=0.92,
            dangerous_visual_class=True, detections_count=1,
            bounding_boxes=[{"class": "ALGAL_BLOOM_RISK", "confidence": 0.92, "bbox": [0,0,10,10]}],
            inference_time_ms=10.0, preprocessing_time_ms=5.0, total_pipeline_time_ms=15.0,
            model_name="YOLOv8-AquaticBloom", model_version="1.0.0", status="SUCCESS"
        )
        ev_high = self.detector.evaluate_prediction(pred_high)
        self.assertEqual(ev_high.visual_state, "BLOOM_EVIDENCE")
        self.assertEqual(ev_high.risk_level, "HIGH")

        # Create artificial low-confidence bloom prediction
        pred_low = CVPrediction(
            frame_id="f_low", timestamp="2026-08-17T21:00:00Z",
            predicted_class="ALGAL_BLOOM_RISK", confidence=0.45,
            dangerous_visual_class=True, detections_count=1,
            bounding_boxes=[{"class": "ALGAL_BLOOM_RISK", "confidence": 0.45, "bbox": [0,0,10,10]}],
            inference_time_ms=10.0, preprocessing_time_ms=5.0, total_pipeline_time_ms=15.0,
            model_name="YOLOv8-AquaticBloom", model_version="1.0.0", status="SUCCESS"
        )
        ev_low = self.detector.evaluate_prediction(pred_low)
        self.assertEqual(ev_low.visual_state, "UNCERTAIN")
        self.assertEqual(ev_low.risk_level, "LOW")

    def test_camera_fault_and_inference_failure(self):
        # Camera Offline Fault
        pred_cam_fault = CVPrediction(
            frame_id="f_off", timestamp="2026-08-17T21:00:00Z",
            predicted_class="UNCERTAIN", confidence=0.0, dangerous_visual_class=False,
            detections_count=0, bounding_boxes=[], inference_time_ms=1.0,
            preprocessing_time_ms=1.0, total_pipeline_time_ms=2.0,
            model_name="YOLOv8", model_version="1.0", status="CAMERA_OFFLINE"
        )
        ev_cam_fault = self.detector.evaluate_prediction(pred_cam_fault)
        self.assertEqual(ev_cam_fault.visual_state, "CAMERA_FAULT")
        self.assertEqual(ev_cam_fault.risk_level, "UNKNOWN")
        self.assertNotEqual(ev_cam_fault.visual_state, "NO_VISUAL_BLOOM")

        # Inference Engine Failure
        pred_inf_fail = CVPrediction(
            frame_id="f_fail", timestamp="2026-08-17T21:00:00Z",
            predicted_class="UNCERTAIN", confidence=0.0, dangerous_visual_class=False,
            detections_count=0, bounding_boxes=[], inference_time_ms=1.0,
            preprocessing_time_ms=1.0, total_pipeline_time_ms=2.0,
            model_name="YOLOv8", model_version="1.0", status="INFERENCE_FAILURE"
        )
        ev_inf_fail = self.detector.evaluate_prediction(pred_inf_fail)
        self.assertEqual(ev_inf_fail.visual_state, "INFERENCE_FAILURE")
        self.assertEqual(ev_inf_fail.risk_level, "UNKNOWN")

    def test_full_v41_v42_v43_v44_pipeline(self):
        """Tests complete acquisition -> preprocessing -> inference -> evidence pipeline."""
        self.camera.set_scenario("KNOWN_BLOOM_RISK")
        frame = self.camera.capture_frame()
        preproc = self.processor.process(frame)
        pred = self.model.predict(preproc)
        evidence = self.detector.evaluate_prediction(pred)

        self.assertTrue(preproc.valid)
        self.assertEqual(pred.status, "SUCCESS")
        self.assertEqual(evidence.frame_id, frame.frame_id)
        self.assertEqual(evidence.visual_state, "BLOOM_EVIDENCE")
        self.assertGreater(evidence.visual_pipeline_time_ms, 0.0)

    def test_hardware_oriented_physical_camera_end_to_end_path(self):
        """
        Simulates physical 1920x1080 JPEG ESP32-CAM frame acquisition ->
        ImagePreprocessor -> AquaticBloomCVModel -> CVPrediction -> VisualDetector -> VisualEvidence.
        """
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
        raw_jpeg = buf.getvalue()

        physical_frame = CameraFrame(
            frame_id="ESP32_CAM_1920_FRAME_888",
            timestamp="2026-08-17T21:25:00.000Z",
            width=1920, height=1080, channels=3, format="JPEG",
            image_bytes=raw_jpeg, quality_valid=True, status="OK",
            metadata={"hardware": "ESP32-CAM-OV2640"}
        )

        preproc = self.processor.process(physical_frame)
        pred = self.model.predict(preproc)
        ev = self.detector.evaluate_prediction(pred)

        self.assertTrue(preproc.valid)
        self.assertEqual(ev.frame_id, "ESP32_CAM_1920_FRAME_888")
        self.assertEqual(ev.visual_state, "BLOOM_EVIDENCE")
        self.assertIn(ev.risk_level, ["MEDIUM", "HIGH"])
        source_meta = ev.metadata["model_metadata"]["source_metadata"]["source_metadata"]
        self.assertEqual(source_meta["hardware"], "ESP32-CAM-OV2640")

if __name__ == "__main__":
    unittest.main()
