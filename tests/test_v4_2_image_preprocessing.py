import io
import unittest
import numpy as np
from PIL import Image
from src.cv.camera_driver import CameraFrame, VirtualCameraDriver
from src.cv.image_preprocessing import PreprocessedImage, ImagePreprocessor

class TestV42ImagePreprocessingHardwareReadiness(unittest.TestCase):
    def setUp(self):
        self.virtual_cam = VirtualCameraDriver(name="TEST_CAM_VIRTUAL", resolution=(640, 480))
        self.virtual_cam.init()
        self.processor = ImagePreprocessor(target_size=(224, 224), color_space="RGB", normalization_type="RESCALE")

    def test_valid_normal_frame_preprocessing(self):
        self.virtual_cam.set_scenario("NORMAL")
        frame = self.virtual_cam.capture_frame()
        result = self.processor.process(frame)

        self.assertIsInstance(result, PreprocessedImage)
        self.assertTrue(result.valid)
        self.assertEqual(result.status, "OK")
        self.assertEqual(result.frame_id, frame.frame_id)
        self.assertEqual(result.timestamp, frame.timestamp)
        self.assertEqual(result.original_width, 640)
        self.assertEqual(result.original_height, 480)
        self.assertEqual(result.processed_width, 224)
        self.assertEqual(result.processed_height, 224)
        self.assertEqual(result.channels, 3)
        self.assertEqual(result.dtype, "float32")
        self.assertIsNotNone(result.tensor_data)
        self.assertEqual(result.tensor_data.shape, (224, 224, 3))
        self.assertIn("preprocessing_time_ms", result.metadata)
        self.assertGreaterEqual(result.metadata["preprocessing_time_ms"], 0.0)

    def test_hardware_replacement_contract(self):
        """
        Demonstrates physical camera replacement capability:
        Constructs a raw CameraFrame independently of VirtualCameraDriver (e.g. from an ESP32-CAM JPEG stream)
        and proves that ImagePreprocessor handles both virtual and physical frames identically.
        """
        # Create raw JPEG bytes for a simulated 1920x1080 HD physical camera frame
        img = Image.new("RGB", (1920, 1080), color=(50, 180, 70))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        raw_jpeg_bytes = buf.getvalue()

        physical_frame = CameraFrame(
            frame_id="ESP32_CAM_01_FRAME_999",
            timestamp="2026-08-17T21:15:00.000Z",
            width=1920,
            height=1080,
            channels=3,
            format="JPEG",
            image_bytes=raw_jpeg_bytes,
            quality_valid=True,
            status="OK",
            metadata={"hardware": "ESP32-CAM-OV2640", "exposure": "auto"}
        )

        result = self.processor.process(physical_frame)
        self.assertTrue(result.valid)
        self.assertEqual(result.frame_id, "ESP32_CAM_01_FRAME_999")
        self.assertEqual(result.original_width, 1920)
        self.assertEqual(result.original_height, 1080)
        self.assertEqual(result.processed_width, 224)
        self.assertEqual(result.processed_height, 224)
        self.assertEqual(result.tensor_data.shape, (224, 224, 3))
        self.assertEqual(result.metadata["source_metadata"]["hardware"], "ESP32-CAM-OV2640")

    def test_raw_frame_non_mutation(self):
        """Proves that processing does not alter or mutate the original CameraFrame."""
        self.virtual_cam.set_scenario("NORMAL")
        frame = self.virtual_cam.capture_frame()
        bytes_before = frame.image_bytes
        id_before = frame.frame_id

        _ = self.processor.process(frame)

        self.assertEqual(frame.image_bytes, bytes_before)
        self.assertEqual(frame.frame_id, id_before)

    def test_aspect_ratio_strategies(self):
        # Create 16:9 widescreen frame (1280x720)
        img = Image.new("RGB", (1280, 720), color=(10, 50, 200))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        raw_bytes = buf.getvalue()

        frame = CameraFrame(
            frame_id="aspect_test_1", timestamp="2026-08-17T21:15:00.000Z",
            width=1280, height=720, channels=3, format="JPEG",
            image_bytes=raw_bytes, quality_valid=True, status="OK"
        )

        # 1. STRETCH
        proc_stretch = ImagePreprocessor(target_size=(224, 224), aspect_ratio_mode="STRETCH")
        res_stretch = proc_stretch.process(frame)
        self.assertEqual(res_stretch.tensor_data.shape, (224, 224, 3))

        # 2. LETTERBOX
        proc_letterbox = ImagePreprocessor(target_size=(224, 224), aspect_ratio_mode="LETTERBOX")
        res_letterbox = proc_letterbox.process(frame)
        self.assertEqual(res_letterbox.tensor_data.shape, (224, 224, 3))

        # 3. CROP
        proc_crop = ImagePreprocessor(target_size=(224, 224), aspect_ratio_mode="CROP")
        res_crop = proc_crop.process(frame)
        self.assertEqual(res_crop.tensor_data.shape, (224, 224, 3))

    def test_normalization_types(self):
        self.virtual_cam.set_scenario("NORMAL")
        frame = self.virtual_cam.capture_frame()

        # Rescale [0..1]
        proc_rescale = ImagePreprocessor(normalization_type="RESCALE")
        res_rescale = proc_rescale.process(frame)
        self.assertTrue(res_rescale.valid)
        self.assertGreaterEqual(res_rescale.tensor_data.min(), 0.0)
        self.assertLessEqual(res_rescale.tensor_data.max(), 1.0)
        self.assertEqual(res_rescale.dtype, "float32")

        # Standard (z-score with ImageNet mean/std)
        proc_std = ImagePreprocessor(normalization_type="STANDARD", mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        res_std = proc_std.process(frame)
        self.assertTrue(res_std.valid)
        self.assertEqual(res_std.dtype, "float32")

        # None (uint8 [0..255])
        proc_none = ImagePreprocessor(normalization_type="NONE")
        res_none = proc_none.process(frame)
        self.assertTrue(res_none.valid)
        self.assertEqual(res_none.dtype, "uint8")

    def test_sequential_frame_streaming_integrity(self):
        """Verifies that sequential frames maintain sequence integrity without memory crosstalk."""
        for i in range(10):
            frame = self.virtual_cam.capture_frame()
            res = self.processor.process(frame)
            self.assertTrue(res.valid)
            self.assertEqual(res.frame_id, f"frame_{i+1}")
            self.assertIn("preprocessing_time_ms", res.metadata)

    def test_fault_handling_and_status_codes(self):
        # Corrupted Frame
        self.virtual_cam.set_fault("CORRUPTED_FRAME")
        frame_corrupted = self.virtual_cam.capture_frame()
        res_corrupted = self.processor.process(frame_corrupted)
        self.assertFalse(res_corrupted.valid)
        self.assertEqual(res_corrupted.status, "CORRUPTED")

        # Camera Offline
        self.virtual_cam.set_fault("CAMERA_OFFLINE")
        frame_offline = self.virtual_cam.capture_frame()
        res_offline = self.processor.process(frame_offline)
        self.assertFalse(res_offline.valid)
        self.assertEqual(res_offline.status, "CAMERA_OFFLINE")

        # Null input
        res_null = self.processor.process(None)
        self.assertFalse(res_null.valid)
        self.assertEqual(res_null.status, "NULL_FRAME")

        # Empty Payload
        empty_frame = CameraFrame("e1", "2026-08-17T21:00:00Z", 224, 224, 3, "JPEG", b"", True, "OK")
        res_empty = self.processor.process(empty_frame)
        self.assertFalse(res_empty.valid)
        self.assertEqual(res_empty.status, "EMPTY_PAYLOAD")

if __name__ == "__main__":
    unittest.main()
