import io
import unittest
import numpy as np
from PIL import Image, ImageDraw
from src.cv.camera_driver import CameraFrame, VirtualCameraDriver
from src.cv.image_preprocessing import PreprocessedImage, ImagePreprocessor
from src.cv.cv_model import CVPrediction, BaseCVModel, AquaticBloomCVModel

class TestV43CVModelIntegration(unittest.TestCase):
    def setUp(self):
        self.camera = VirtualCameraDriver(name="TEST_CAM_VIRTUAL", resolution=(640, 480))
        self.camera.init()
        self.processor = ImagePreprocessor(target_size=(224, 224), color_space="RGB", normalization_type="RESCALE")
        self.model = AquaticBloomCVModel(model_name="MobileNetV3-Small-AquaticBloom", model_version="1.0.0")
        self.assertTrue(self.model.load())

    def test_model_initialization_and_status(self):
        self.assertEqual(self.model.get_status(), "READY")
        self.assertEqual(self.model.model_name, "MobileNetV3-Small-AquaticBloom")
        self.assertEqual(self.model.model_version, "1.0.0")
        self.assertTrue(self.model.is_trained_model_active)

    def test_normal_scenario_inference(self):
        self.camera.set_scenario("NORMAL")
        frame = self.camera.capture_frame()
        preproc_img = self.processor.process(frame)
        prediction = self.model.predict(preproc_img)

        self.assertIsInstance(prediction, CVPrediction)
        self.assertEqual(prediction.status, "SUCCESS")
        self.assertEqual(prediction.frame_id, frame.frame_id)
        self.assertEqual(prediction.timestamp, frame.timestamp)
        self.assertEqual(prediction.predicted_class, "NORMAL_WATER")
        self.assertFalse(prediction.dangerous_visual_class)
        self.assertGreaterEqual(prediction.confidence, 0.5)
        self.assertGreater(prediction.inference_time_ms, 0.0)
        self.assertGreater(prediction.total_pipeline_time_ms, 0.0)

    def test_bloom_risk_scenario_inference(self):
        self.camera.set_scenario("KNOWN_BLOOM_RISK")
        frame = self.camera.capture_frame()
        preproc_img = self.processor.process(frame)
        prediction = self.model.predict(preproc_img)

        self.assertEqual(prediction.status, "SUCCESS")
        self.assertEqual(prediction.predicted_class, "ALGAL_BLOOM")
        self.assertTrue(prediction.dangerous_visual_class)
        self.assertGreaterEqual(prediction.confidence, 0.5)
        self.assertGreater(prediction.detections_count, 0)

    def test_end_to_end_v41_v42_v43_pipeline(self):
        """Verifies full acquisition -> preprocessing -> inference pipeline."""
        scenarios = ["NORMAL", "KNOWN_BLOOM_RISK", "NORMAL"]
        for sc in scenarios:
            self.camera.set_scenario(sc)
            frame = self.camera.capture_frame()
            preproc = self.processor.process(frame)
            pred = self.model.predict(preproc)

            self.assertTrue(preproc.valid)
            self.assertEqual(pred.status, "SUCCESS")
            self.assertEqual(pred.frame_id, frame.frame_id)

    def test_hardware_oriented_physical_camera_path(self):
        """
        Simulates physical ESP32-CAM 1920x1080 JPEG frame acquisition,
        proves V4.1 -> V4.2 -> V4.3 pipeline compatibility for real camera payloads.
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
        raw_jpeg_bytes = buf.getvalue()

        physical_frame = CameraFrame(
            frame_id="ESP32_CAM_01_FRAME_500",
            timestamp="2026-08-17T21:20:00.000Z",
            width=1920, height=1080, channels=3, format="JPEG",
            image_bytes=raw_jpeg_bytes, quality_valid=True, status="OK",
            metadata={"hardware": "ESP32-CAM-OV2640"}
        )

        preproc_img = self.processor.process(physical_frame)
        pred = self.model.predict(preproc_img)

        self.assertTrue(preproc_img.valid)
        self.assertEqual(pred.frame_id, "ESP32_CAM_01_FRAME_500")
        self.assertEqual(pred.predicted_class, "ALGAL_BLOOM")
        self.assertTrue(pred.dangerous_visual_class)

    def test_invalid_input_and_fault_handling(self):
        # Corrupted Frame Input
        self.camera.set_fault("CORRUPTED_FRAME")
        frame_corrupted = self.camera.capture_frame()
        preproc_corrupted = self.processor.process(frame_corrupted)
        pred_corrupted = self.model.predict(preproc_corrupted)

        self.assertFalse(preproc_corrupted.valid)
        self.assertEqual(pred_corrupted.status, "CORRUPTED")
        self.assertEqual(pred_corrupted.predicted_class, "UNCERTAIN")
        self.assertFalse(pred_corrupted.dangerous_visual_class)

        # Model Offline Fault
        self.model.status = "OFFLINE"
        self.camera.set_scenario("NORMAL")
        frame = self.camera.capture_frame()
        preproc = self.processor.process(frame)
        pred_offline = self.model.predict(preproc)

        self.assertEqual(pred_offline.status, "MODEL_OFFLINE")
        self.assertEqual(pred_offline.predicted_class, "UNCERTAIN")

    def test_sequential_frame_inference_latency_measurement(self):
        """Verifies real-time sequential frame processing with timing metrics."""
        self.camera.set_scenario("NORMAL")
        for i in range(5):
            frame = self.camera.capture_frame()
            preproc = self.processor.process(frame)
            pred = self.model.predict(preproc)

            self.assertEqual(pred.frame_id, f"frame_{i+1}")
            self.assertGreater(pred.inference_time_ms, 0.0)
            self.assertGreaterEqual(pred.total_pipeline_time_ms, pred.inference_time_ms)

if __name__ == "__main__":
    unittest.main()
