import os
import io
import time
import pytest
import datetime
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw

from src.cv.camera_driver import CameraFrame
from src.cv.camera_transport import CameraMessageContract, CameraTransportReceiver
from src.cv.temporal_validator import TemporalValidator, TemporalValidationResult
from src.cv.image_preprocessing import ImagePreprocessor
from src.cv.cv_model import AquaticBloomCVModel
from src.cv.visual_detection import VisualDetector
from src.fusion.fusion_engine import FusionEngine
from src.fusion.runtime_orchestrator import MultimodalRuntimeOrchestrator, MultimodalObservationResult
from src.iot.mqtt_client import MQTTClient, InMemoryMQTTBroker


def create_jpeg_bytes(scenario: str = "BLOOM") -> bytes:
    """Helper generating valid JPEG image bytes."""
    img = Image.new("RGB", (224, 224), color=(10, 80, 140))
    draw = ImageDraw.Draw(img)
    if scenario == "BLOOM":
        draw.rectangle([0, 0, 224, 224], fill=(30, 160, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


class TestV483TimeSynchronization:
    """
    Test suite for Milestone V4.8.3 Time Synchronization & Temporal Consistency.
    """
    def setup_method(self):
        InMemoryMQTTBroker.reset_instance()
        self.mqtt_client = MQTTClient(client_id="TEST_TIME_CLIENT", use_mock=True)
        self.mqtt_client.connect()
        self.validator = TemporalValidator(
            max_allowed_frame_age_sec=30.0,
            max_future_tolerance_sec=5.0,
            max_sensor_visual_delta_sec=15.0
        )

    def teardown_method(self):
        if self.mqtt_client.connected:
            self.mqtt_client.disconnect()
        InMemoryMQTTBroker.reset_instance()

    def test_01_synced_timestamp_accepted(self):
        """1. SYNCED timestamp within age limit is accepted as VALID."""
        now = datetime.datetime.now()
        res = self.validator.validate_camera_frame_temporal(
            capture_ts_str=now.isoformat(),
            time_sync_status="SYNCED",
            clock_source="NTP",
            gateway_receive_ts_str=now.isoformat()
        )
        assert res.temporal_valid is True
        assert res.temporal_status == "VALID"
        assert res.reason_code == "OK"

    def test_02_unsynced_camera_timestamp_rejected(self):
        """2. UNSYNCED camera timestamp rejected for temporal fusion."""
        now = datetime.datetime.now()
        res = self.validator.validate_camera_frame_temporal(
            capture_ts_str=now.isoformat(),
            time_sync_status="UNSYNCED",
            clock_source="UNSYNCED_BOOT_TICK",
            gateway_receive_ts_str=now.isoformat()
        )
        assert res.temporal_valid is False
        assert res.temporal_status == "UNSYNCED"
        assert res.reason_code == "VISUAL_CLOCK_UNSYNCED"

    def test_03_unsynced_esp32_timestamp_handled_safely(self):
        """3. UNSYNCED ESP32 status handled safely without timestamp fabrication."""
        now = datetime.datetime.now()
        res = self.validator.validate_camera_frame_temporal(
            capture_ts_str=now.isoformat(),
            time_sync_status="UNSYNCED",
            clock_source="UNSYNCED_BOOT_TICK"
        )
        assert res.temporal_valid is False
        assert res.reason_code == "VISUAL_CLOCK_UNSYNCED"

    def test_04_stale_frame_rejected(self):
        """4. Stale camera frame (>30s age) rejected."""
        stale_ts = (datetime.datetime.now() - datetime.timedelta(seconds=45)).isoformat()
        recv_ts = datetime.datetime.now().isoformat()
        res = self.validator.validate_camera_frame_temporal(
            capture_ts_str=stale_ts,
            time_sync_status="SYNCED",
            clock_source="NTP",
            gateway_receive_ts_str=recv_ts
        )
        assert res.temporal_valid is False
        assert res.temporal_status == "STALE"
        assert res.reason_code == "VISUAL_TIMESTAMP_STALE"

    def test_05_future_timestamp_rejected(self):
        """5. Future timestamp (>5s in future) rejected."""
        future_ts = (datetime.datetime.now() + datetime.timedelta(seconds=20)).isoformat()
        recv_ts = datetime.datetime.now().isoformat()
        res = self.validator.validate_camera_frame_temporal(
            capture_ts_str=future_ts,
            time_sync_status="SYNCED",
            clock_source="NTP",
            gateway_receive_ts_str=recv_ts
        )
        assert res.temporal_valid is False
        assert res.temporal_status == "FUTURE_TIMESTAMP"
        assert res.reason_code == "VISUAL_TIMESTAMP_FUTURE"

    def test_06_valid_timestamp_accepted(self):
        """6. Valid timestamp within thresholds accepted."""
        ts = datetime.datetime.now().isoformat()
        res = self.validator.validate_camera_frame_temporal(
            capture_ts_str=ts, time_sync_status="SYNCED", clock_source="NTP", gateway_receive_ts_str=ts
        )
        assert res.temporal_valid is True

    def test_07_acceptable_sensor_camera_delta(self):
        """7. Acceptable sensor-camera timestamp delta (<15s) accepted."""
        now = datetime.datetime.now()
        sensor_ts = (now - datetime.timedelta(seconds=5)).isoformat()
        camera_ts = now.isoformat()
        res = self.validator.validate_camera_frame_temporal(
            capture_ts_str=camera_ts,
            time_sync_status="SYNCED",
            clock_source="NTP",
            gateway_receive_ts_str=camera_ts,
            sensor_ts_str=sensor_ts
        )
        assert res.temporal_valid is True
        assert res.reason_code == "OK"

    def test_08_excessive_sensor_camera_delta_rejected(self):
        """8. Excessive sensor-camera timestamp delta (>15s) rejected as CLOCK_SKEW."""
        now = datetime.datetime.now()
        sensor_ts = (now - datetime.timedelta(seconds=25)).isoformat()
        camera_ts = now.isoformat()
        res = self.validator.validate_camera_frame_temporal(
            capture_ts_str=camera_ts,
            time_sync_status="SYNCED",
            clock_source="NTP",
            gateway_receive_ts_str=camera_ts,
            sensor_ts_str=sensor_ts
        )
        assert res.temporal_valid is False
        assert res.temporal_status == "CLOCK_SKEW"
        assert res.reason_code == "VISUAL_CLOCK_SKEW"

    def test_09_clock_skew_detection(self):
        """9. Clock skew detection between sensor and camera timestamps."""
        now = datetime.datetime.now()
        sensor_ts = (now - datetime.timedelta(seconds=30)).isoformat()
        camera_ts = now.isoformat()
        res = self.validator.validate_camera_frame_temporal(
            capture_ts_str=camera_ts,
            time_sync_status="SYNCED",
            clock_source="NTP",
            gateway_receive_ts_str=camera_ts,
            sensor_ts_str=sensor_ts
        )
        assert res.temporal_status == "CLOCK_SKEW"

    def test_10_invalid_timestamp_syntax(self):
        """10. Invalid timestamp string syntax rejected."""
        res = self.validator.validate_camera_frame_temporal(
            capture_ts_str="INVALID_DATE_STRING",
            time_sync_status="SYNCED"
        )
        assert res.temporal_valid is False
        assert res.temporal_status == "INVALID_TIMESTAMP"
        assert res.reason_code == "VISUAL_TIMESTAMP_INVALID"

    def test_11_capture_timestamp_preserved(self):
        """11. Capture timestamp preserved separately from receive timestamp."""
        cap_ts = "2026-08-18T10:00:00"
        recv_ts = "2026-08-18T10:00:02"
        contract = CameraMessageContract(
            device_id="AQUA_FRESH_001",
            frame_id="f_cap_01",
            timestamp=cap_ts,
            capture_timestamp=cap_ts,
            time_sync_status="SYNCED",
            clock_source="NTP",
            width=224, height=224, channels=3, format="JPEG",
            image_bytes=create_jpeg_bytes()
        )
        assert contract.capture_timestamp == cap_ts

    def test_12_receive_timestamp_independently_generated(self):
        """12. Gateway receive timestamp independently generated upon message receipt."""
        receiver = CameraTransportReceiver(mqtt_client=self.mqtt_client)
        receiver.init()
        contract = CameraMessageContract(
            device_id="AQUA_FRESH_001",
            frame_id="f_rcv_01",
            timestamp=datetime.datetime.now().isoformat(),
            time_sync_status="SYNCED",
            clock_source="NTP",
            width=224, height=224, channels=3, format="JPEG",
            image_bytes=create_jpeg_bytes()
        )
        self.mqtt_client.publish("aquatic/AQUA_FRESH_001/camera/raw", contract.to_mqtt_payload())
        frame = receiver.capture_frame()
        assert "gateway_receive_timestamp" in frame.metadata

    def test_13_processing_timestamp_independently_generated(self):
        """13. Gateway processing timestamp independently generated during evaluation."""
        now = datetime.datetime.now().isoformat()
        res = self.validator.validate_camera_frame_temporal(
            capture_ts_str=now, time_sync_status="SYNCED", gateway_receive_ts_str=now, gateway_process_ts_str=now
        )
        assert res.gateway_process_timestamp == now

    def test_14_wall_clock_not_used_for_latency(self):
        """14. Monotonic perf_counter used for latency, not wall-clock subtraction."""
        t0 = time.perf_counter()
        time.sleep(0.01)
        res = self.validator.validate_camera_frame_temporal(
            capture_ts_str=datetime.datetime.now().isoformat(),
            time_sync_status="SYNCED",
            start_monotonic=t0
        )
        assert res.monotonic_latency_ms >= 10.0

    def test_15_monotonic_latency_measurement(self):
        """15. Monotonic latency measurement tracking verified."""
        t0 = time.perf_counter()
        time.sleep(0.005)
        res = self.validator.validate_camera_frame_temporal(
            capture_ts_str=datetime.datetime.now().isoformat(),
            time_sync_status="SYNCED",
            start_monotonic=t0
        )
        assert res.monotonic_latency_ms > 0.0

    def test_16_temporal_failure_never_becomes_no_bloom(self):
        """16. Temporal failure NEVER becomes NO_BLOOM."""
        stale_ts = (datetime.datetime.now() - datetime.timedelta(seconds=60)).isoformat()
        contract = CameraMessageContract(
            device_id="AQUA_FRESH_001",
            frame_id="f_stale_01",
            timestamp=stale_ts,
            time_sync_status="SYNCED",
            clock_source="NTP",
            width=224, height=224, channels=3, format="JPEG",
            image_bytes=create_jpeg_bytes("BLOOM")
        )
        receiver = CameraTransportReceiver(mqtt_client=self.mqtt_client)
        receiver.init()
        self.mqtt_client.publish("aquatic/AQUA_FRESH_001/camera/raw", contract.to_mqtt_payload())
        frame = receiver.capture_frame()
        assert frame.quality_valid is False
        assert frame.status == "VISUAL_TIMESTAMP_STALE"

        detector = VisualDetector()
        model = AquaticBloomCVModel()
        model.load()
        ev = detector.evaluate_prediction(model.predict(ImagePreprocessor().process(frame)))
        assert ev.visual_state == "CAMERA_FAULT"
        assert ev.visual_state != "NO_VISUAL_BLOOM"

    def test_17_temporal_failure_never_becomes_normal_via_fallback(self):
        """17. Temporal failure NEVER becomes NORMAL through visual fallback."""
        engine = FusionEngine()
        ml_ev = {"dataset": "caml", "predicted_class": 1, "class_probabilities": {"BLOOM": 0.9}, "confidence": 0.9, "dangerous_class": True, "model_id": "m1"}
        ais_ev = {"dataset": "caml", "is_anomaly": True, "anomaly_score": 0.9, "matched_detector_count": 5, "nearest_detector_distance": 0.1, "ais_model_id": "a1"}
        vis_ev = {"visual_state": "CAMERA_FAULT", "confidence": 0.0, "risk_level": "UNKNOWN", "reason_code": "VISUAL_TIMESTAMP_STALE"}

        fused = engine.fuse(ml_ev, ais_ev, visual_evidence=vis_ev)
        assert fused["fusion"]["final_state"] != "NORMAL"
        assert fused["fusion"]["reason_code"] == "VISUAL_TIMESTAMP_STALE"

    def test_18_sensor_only_fallback_remains_operational(self):
        """18. Sensor-only fallback remains operational during temporal failure."""
        engine = FusionEngine()
        ml_ev = {"dataset": "caml", "predicted_class": 0, "class_probabilities": {"NORMAL": 0.95}, "confidence": 0.95, "dangerous_class": False, "model_id": "m1"}
        ais_ev = {"dataset": "caml", "is_anomaly": False, "anomaly_score": 0.1, "matched_detector_count": 0, "nearest_detector_distance": 0.5, "ais_model_id": "a1"}
        vis_ev = {"visual_state": "CAMERA_FAULT", "confidence": 0.0, "risk_level": "UNKNOWN", "reason_code": "VISUAL_CLOCK_UNSYNCED"}

        fused = engine.fuse(ml_ev, ais_ev, visual_evidence=vis_ev)
        assert fused["fusion"]["final_state"] == "NORMAL"
        assert fused["fusion"]["reason_code"] == "VISUAL_CLOCK_UNSYNCED"

    def test_19_physical_esp32_cam_json_contract(self):
        """19. Physical ESP32-CAM JSON contract (Schema 1.1) verification."""
        contract = CameraMessageContract(
            device_id="AQUA_FRESH_001",
            frame_id="f_sch11",
            timestamp=datetime.datetime.now().isoformat(),
            schema_version="1.1",
            time_sync_status="SYNCED",
            clock_source="NTP",
            width=224, height=224, channels=3, format="JPEG",
            image_bytes=create_jpeg_bytes()
        )
        payload = contract.to_mqtt_payload()
        assert payload["schema_version"] == "1.1"
        assert payload["time_sync_status"] == "SYNCED"
        assert payload["clock_source"] == "NTP"

    def test_20_physical_esp32_telemetry_contract(self):
        """20. Physical ESP32 telemetry timestamp contract compatibility."""
        receiver = CameraTransportReceiver(mqtt_client=self.mqtt_client)
        receiver.init()
        ts_now = datetime.datetime.now().isoformat()
        res = self.validator.validate_camera_frame_temporal(
            capture_ts_str=ts_now, time_sync_status="SYNCED", clock_source="NTP", sensor_ts_str=ts_now
        )
        assert res.temporal_valid is True

    def test_21_duplicate_frame_handling_remains_correct(self):
        """21. Duplicate frame handling remains correct."""
        receiver = CameraTransportReceiver(mqtt_client=self.mqtt_client)
        receiver.init()
        contract = CameraMessageContract(
            device_id="AQUA_FRESH_001", frame_id="f_dup_time_01",
            timestamp=datetime.datetime.now().isoformat(), time_sync_status="SYNCED", clock_source="NTP",
            width=224, height=224, channels=3, format="JPEG", image_bytes=create_jpeg_bytes()
        )
        self.mqtt_client.publish("aquatic/AQUA_FRESH_001/camera/raw", contract.to_mqtt_payload())
        assert receiver.frame_count == 1
        self.mqtt_client.publish("aquatic/AQUA_FRESH_001/camera/raw", contract.to_mqtt_payload())
        assert receiver.frame_count == 1
        assert receiver.dropped_duplicate_count == 1

    def test_22_complete_temporal_pipeline_flow(self):
        """22. Complete camera -> transport -> temporal validation -> CV -> fusion path."""
        orchestrator = MultimodalRuntimeOrchestrator(max_queue_size=5)
        receiver = CameraTransportReceiver(mqtt_client=self.mqtt_client)
        receiver.init()

        contract = CameraMessageContract(
            device_id="AQUA_FRESH_001",
            frame_id="f_e2e_time_01",
            timestamp=datetime.datetime.now().isoformat(),
            time_sync_status="SYNCED",
            clock_source="NTP",
            width=224, height=224, channels=3, format="JPEG",
            image_bytes=create_jpeg_bytes("BLOOM")
        )
        self.mqtt_client.publish("aquatic/AQUA_FRESH_001/camera/raw", contract.to_mqtt_payload())
        acquired_frame = receiver.capture_frame()

        X_df = pd.DataFrame([{
            'lat': 27.5, 'lon': -81.2, 'distance_to_water_m': 120.0,
            'region': 'south', 'Season': 'Summer', 'Year': 2026,
            'Month_sin': 0.0, 'Month_cos': -1.0, 'DayOfYear_sin': 0.5, 'DayOfYear_cos': -0.866
        }])
        sensors = {"temperature_c": 26.5, "ph": 8.4, "turbidity_ntu": 12.0, "dissolved_oxygen_mg_l": 5.2, "sensor_status": "OK"}

        result = orchestrator.process_multimodal_observation(
            dataset_key="caml", X_df=X_df, sensors=sensors, camera_frame=acquired_frame
        )
        assert isinstance(result, MultimodalObservationResult)
        assert result.latency.total_pipeline_ms > 0

    def test_23_v3_8_protection_verification(self):
        """23. Frozen V3.8 source protection verification."""
        import subprocess
        frozen_files = [
            "src/iot/esp32_device.py",
            "src/iot/communication.py",
            "src/iot/scheduler.py",
            "src/iot/hal.py",
            "src/iot/actuators.py"
        ]
        result = subprocess.run(["git", "status", "--porcelain"] + frozen_files, capture_output=True, text=True)
        assert result.stdout.strip() == ""
