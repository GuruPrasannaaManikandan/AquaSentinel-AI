import unittest
import numpy as np
from src.cv.camera_driver import CameraFrame, VirtualCameraDriver

class TestV41CameraAcquisition(unittest.TestCase):
    def setUp(self):
        self.camera = VirtualCameraDriver(name="TEST_CAM_01", resolution=(224, 224))
        self.assertTrue(self.camera.init())

    def test_camera_init_and_status(self):
        self.assertEqual(self.camera.get_status(), "ONLINE")

    def test_normal_frame_capture(self):
        self.camera.set_scenario("NORMAL")
        frame = self.camera.capture_frame()
        self.assertIsInstance(frame, CameraFrame)
        self.assertTrue(frame.quality_valid)
        self.assertEqual(frame.status, "OK")
        self.assertEqual(frame.width, 224)
        self.assertEqual(frame.height, 224)
        self.assertGreater(len(frame.image_bytes), 0)

        # Convert to PIL & NumPy array
        pil_img = frame.to_pil_image()
        self.assertIsNotNone(pil_img)
        self.assertEqual(pil_img.size, (224, 224))

        arr = frame.to_numpy_array()
        self.assertIsNotNone(arr)
        self.assertEqual(arr.shape, (224, 224, 3))

    def test_bloom_frame_capture(self):
        self.camera.set_scenario("KNOWN_BLOOM_RISK")
        frame = self.camera.capture_frame()
        self.assertTrue(frame.quality_valid)
        self.assertEqual(frame.status, "OK")
        self.assertGreater(len(frame.image_bytes), 0)

    def test_camera_offline_fault(self):
        self.camera.set_fault("CAMERA_OFFLINE")
        self.assertEqual(self.camera.get_status(), "OFFLINE")
        frame = self.camera.capture_frame()
        self.assertFalse(frame.quality_valid)
        self.assertEqual(frame.status, "CAMERA_OFFLINE")
        self.assertEqual(len(frame.image_bytes), 0)
        self.assertIsNone(frame.to_pil_image())

    def test_corrupted_frame_fault(self):
        self.camera.set_fault("CORRUPTED_FRAME")
        frame = self.camera.capture_frame()
        self.assertFalse(frame.quality_valid)
        self.assertEqual(frame.status, "CORRUPTED")
        # Attempting PIL conversion on corrupted bytes should return None safely
        self.assertIsNone(frame.to_pil_image())

if __name__ == "__main__":
    unittest.main()
