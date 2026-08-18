import io
import unittest
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw

from src.cv.camera_driver import CameraFrame, VirtualCameraDriver
from src.fusion.runtime_orchestrator import MultimodalRuntimeOrchestrator
from src.iot.esp32_device import ESP32Device
from src.iot.actuators import VirtualActuators

class TestV47RuntimeReliability(unittest.TestCase):
    """
    V4.7 Real-Time Multimodal Runtime & Reliability Test Suite.
    Executes sustained 100+ observation simulation, fault matrix injections,
    hardware replacement contract verification, latency profiling, determinism check,
    and explicit bounded queue overflow drop-oldest verification.
    """
    @classmethod
    def setUpClass(cls):
        cls.orchestrator = MultimodalRuntimeOrchestrator(max_queue_size=5)
        cls.camera = VirtualCameraDriver(name="CAM_RELIABILITY_V47", resolution=(224, 224))
        cls.camera.init()

        cls.sample_df_normal = pd.DataFrame([{
            'lat': 27.5,
            'lon': -81.2,
            'distance_to_water_m': 120.0,
            'region': 'south',
            'Season': 'Summer',
            'Year': 2026,
            'Month_sin': 0.0,
            'Month_cos': -1.0,
            'DayOfYear_sin': -0.8,
            'DayOfYear_cos': -0.5
        }])

        cls.sample_df_bloom = pd.DataFrame([{
            'lat': 27.5,
            'lon': -81.2,
            'distance_to_water_m': 10.0,
            'region': 'south',
            'Season': 'Summer',
            'Year': 2026,
            'Month_sin': 0.0,
            'Month_cos': -1.0,
            'DayOfYear_sin': -0.8,
            'DayOfYear_cos': -0.5
        }])

    def test_01_sustained_100_observation_simulation(self):
        """
        Sustained 100+ observation simulation exercising continuous frame streams,
        fault injections (camera offline, frame loss, sensor fault), recovery, and latency stats.
        """
        results = []
        for i in range(105):
            sensors = {"sensor_status": "OK", "temperature_c": 22.0, "ph": 7.4}
            
            # Scenario distribution
            if i < 40:
                # Normal scenario
                self.camera.set_fault(None)
                self.camera.set_scenario("NORMAL")
                frame = self.camera.capture_frame()
                df = self.sample_df_normal
            elif i < 65:
                # Bloom scenario
                self.camera.set_fault(None)
                self.camera.set_scenario("KNOWN_BLOOM_RISK")
                frame = self.camera.capture_frame()
                df = self.sample_df_bloom
            elif i < 80:
                # Turbid discolored scenario
                self.camera.set_fault(None)
                self.camera.set_scenario("ENVIRONMENTAL_STRESS")
                frame = self.camera.capture_frame()
                df = self.sample_df_normal
            elif i < 90:
                # Intermittent frame drop (camera data unavailable)
                frame = None
                df = self.sample_df_normal
            elif i < 95:
                # Camera fault / offline
                self.camera.set_fault("CAMERA_OFFLINE")
                frame = self.camera.capture_frame()
                df = self.sample_df_normal
            elif i < 100:
                # Sensor fault injection
                self.camera.set_fault(None)
                self.camera.set_scenario("NORMAL")
                frame = self.camera.capture_frame()
                sensors["sensor_status"] = "FAULT"
                df = self.sample_df_normal
            else:
                # Recovery phase back to normal
                self.camera.set_fault(None)
                self.camera.set_scenario("NORMAL")
                frame = self.camera.capture_frame()
                df = self.sample_df_normal

            res = self.orchestrator.process_multimodal_observation(
                dataset_key="caml",
                X_df=df,
                sensors=sensors,
                camera_frame=frame
            )
            results.append(res)

        self.assertEqual(len(results), 105)
        self.assertEqual(self.orchestrator.total_observations, 105)
        
        # Verify single model load
        self.assertEqual(self.orchestrator.model_load_count, 1)

        # Verify queue size bounded
        self.assertLessEqual(self.orchestrator.max_queue_occupancy, 5)

        # Verify performance metrics reporting
        metrics = self.orchestrator.get_performance_metrics()
        self.assertEqual(metrics["benchmark_environment"], "GATEWAY/HOST_CPU")
        self.assertIn("latency_ms", metrics)
        self.assertGreater(metrics["latency_ms"]["total_mean"], 0.0)

        # Verify camera fault safe degraded mode (no false NO_BLOOM)
        camera_fault_obs = results[90] # index 90 was CAMERA_OFFLINE
        self.assertEqual(camera_fault_obs.camera_status, "CAMERA_OFFLINE")
        self.assertIn(camera_fault_obs.system_event["reason_code"], ["VISUAL_CAMERA_FAULT", "ML_NORMAL_AIS_NORMAL"])

        # Verify recovery at index 100+
        recovered_obs = results[104]
        self.assertEqual(recovered_obs.camera_status, "OK")
        self.assertEqual(recovered_obs.sensor_status, "OK")
        self.assertTrue(recovered_obs.modality_availability["sensor"])
        self.assertTrue(recovered_obs.modality_availability["visual"])

    def test_02_hardware_replacement_contract(self):
        """
        Verifies downstream pipeline executes seamlessly when VirtualCameraDriver is replaced
        by a realistic physical ESP32-CAM 1920x1080 JPEG payload.
        """
        img = Image.new("RGB", (1920, 1080), color=(20, 180, 40))
        draw = ImageDraw.Draw(img)
        for _ in range(40):
            x0 = np.random.randint(0, 1500)
            y0 = np.random.randint(0, 800)
            x1 = x0 + np.random.randint(100, 400)
            y1 = y0 + np.random.randint(100, 300)
            draw.ellipse([x0, y0, x1, y1], fill=(5, 230, 20))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        frame = CameraFrame(
            frame_id="ESP32_CAM_1920X1080_001",
            timestamp="2026-08-17T23:00:00Z",
            width=1920,
            height=1080,
            channels=3,
            format="JPEG",
            image_bytes=buf.getvalue(),
            quality_valid=True,
            status="OK"
        )

        res = self.orchestrator.process_multimodal_observation(
            dataset_key="caml",
            X_df=self.sample_df_bloom,
            sensors={"sensor_status": "OK"},
            camera_frame=frame
        )

        self.assertIsNotNone(res.system_event)
        self.assertTrue(res.modality_availability["visual"])
        self.assertIn("system_event", res.decision_payload)
        self.assertEqual(res.decision_payload["system_event"]["target_fsm_state"], res.decision_payload["fusion"]["final_state"])

    def test_03_determinism_verification(self):
        """
        Verifies that identical sensor + camera inputs produce identical FusedEvidence and SystemEvent output.
        """
        img = Image.new("RGB", (224, 224), color=(10, 120, 180))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        frame_bytes = buf.getvalue()

        f1 = CameraFrame("F_DET_1", "2026-08-17T23:00:00Z", 224, 224, 3, "JPEG", frame_bytes, True, "OK")
        f2 = CameraFrame("F_DET_2", "2026-08-17T23:00:00Z", 224, 224, 3, "JPEG", frame_bytes, True, "OK")

        r1 = self.orchestrator.process_multimodal_observation("caml", self.sample_df_normal, {"sensor_status": "OK"}, f1)
        r2 = self.orchestrator.process_multimodal_observation("caml", self.sample_df_normal, {"sensor_status": "OK"}, f2)

        self.assertEqual(r1.decision_payload["fusion"]["final_state"], r2.decision_payload["fusion"]["final_state"])
        self.assertEqual(r1.system_event["event_type"], r2.system_event["event_type"])
        self.assertEqual(r1.system_event["target_fsm_state"], r2.system_event["target_fsm_state"])

    def test_04_esp32_device_communication_interruption_and_recovery(self):
        """
        Simulates network communication drop and recovery on ESP32Device without altering V3.8 source code.
        """
        device = ESP32Device(device_id="ESP32_V47_TEST")
        self.assertEqual(device.state, "BOOT")
        
        # Simulate transition to ERROR due to connection failure
        device._transition_to("ERROR")
        self.assertEqual(device.state, "ERROR")

        # Execute recovery mechanism
        device.run_reconnection()
        self.assertEqual(device.state, "ONLINE")

    def test_05_camera_queue_drop_oldest_under_overflow(self):
        """
        Explicitly verifies drop-oldest / newest-frame preservation under queue overflow.
        Enqueues 6 frames into maxsize=5 queue without dequeuing:
        1. Confirms capacity reach at Frame 5.
        2. Verifies Frame 1 is discarded on Frame 6 arrival.
        3. Verifies Frame 6 is retained.
        4. Verifies queue size never exceeds maxsize=5.
        5. Verifies newest-frame preservation continues when additional frames are enqueued.
        """
        orch = MultimodalRuntimeOrchestrator(max_queue_size=5)
        initial_dropped = orch.dropped_frames

        # Create dummy frames 1 to 5
        frames = [
            CameraFrame(f"frame_{idx}", "2026-08-17T23:30:00Z", 224, 224, 3, "JPEG", b"DUMMY", True, "OK")
            for idx in range(1, 6)
        ]

        # Enqueue 5 frames
        for f in frames:
            orch.enqueue_camera_frame(f)

        self.assertEqual(orch.camera_frame_queue.qsize(), 5)
        self.assertTrue(orch.camera_frame_queue.full())

        # Enqueue Frame 6 (overflow event)
        frame_6 = CameraFrame("frame_6", "2026-08-17T23:30:00Z", 224, 224, 3, "JPEG", b"DUMMY", True, "OK")
        accepted = orch.enqueue_camera_frame(frame_6)

        self.assertFalse(accepted) # Queue was full, dropped oldest
        self.assertEqual(orch.dropped_frames, initial_dropped + 1)
        self.assertEqual(orch.camera_frame_queue.qsize(), 5) # Does not exceed 5

        # Enqueue Frames 7 to 10
        for idx in range(7, 11):
            f_extra = CameraFrame(f"frame_{idx}", "2026-08-17T23:30:00Z", 224, 224, 3, "JPEG", b"DUMMY", True, "OK")
            orch.enqueue_camera_frame(f_extra)

        self.assertEqual(orch.camera_frame_queue.qsize(), 5)
        self.assertEqual(orch.dropped_frames, initial_dropped + 5)

        # Dequeue remaining 5 items and verify they are frames 6, 7, 8, 9, 10
        remaining_ids = []
        while not orch.camera_frame_queue.empty():
            remaining_ids.append(orch.camera_frame_queue.get().frame_id)

        self.assertEqual(remaining_ids, ["frame_6", "frame_7", "frame_8", "frame_9", "frame_10"])

if __name__ == "__main__":
    unittest.main()
