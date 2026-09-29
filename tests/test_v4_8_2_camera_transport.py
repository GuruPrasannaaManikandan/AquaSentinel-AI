import os
import io
import base64
import json
import time
import pytest
import datetime
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw

from src.cv.camera_driver import CameraFrame
from src.cv.camera_transport import CameraMessageContract, CameraTransportReceiver
from src.cv.image_preprocessing import ImagePreprocessor, PreprocessedImage
from src.cv.cv_model import AquaticBloomCVModel, CVPrediction
from src.cv.visual_detection import VisualDetector, VisualEvidence
from src.fusion.fusion_engine import FusionEngine
from src.fusion.decision_pipeline import DecisionPipeline
from src.fusion.decision_adapter import DecisionAdapter, SystemEvent
from src.fusion.runtime_orchestrator import MultimodalRuntimeOrchestrator, MultimodalObservationResult
from src.iot.mqtt_client import MQTTClient, InMemoryMQTTBroker


def create_realistic_jpeg_bytes(scenario: str = "BLOOM", resolution: tuple = (224, 224)) -> bytes:
    """Helper function generating genuine, valid JPEG image byte buffers."""
    w, h = resolution
    img = Image.new("RGB", (w, h), color=(10, 80, 140))
    draw = ImageDraw.Draw(img)

    if scenario == "BLOOM":
        draw.rectangle([0, 0, w, h], fill=(30, 160, 50))
        for _ in range(20):
            x0 = np.random.randint(0, w)
            y0 = np.random.randint(0, h)
            draw.ellipse([x0, y0, min(w, x0+50), min(h, y0+50)], fill=(10, 200, 30))
    elif scenario == "NORMAL":
        draw.rectangle([0, 0, w, h], fill=(20, 110, 170))
        for _ in range(10):
            x0 = np.random.randint(0, w)
            y0 = np.random.randint(0, h)
            draw.line([x0, y0, min(w, x0+30), y0], fill=(60, 150, 210), width=2)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


class TestV482CameraTransport:
    """
    Test suite for V4.8.2 Physical ESP32-CAM Image Transport & Receiver.
    """
    def setup_method(self):
        InMemoryMQTTBroker.reset_instance()
        self.mqtt_client = MQTTClient(client_id="TEST_CLIENT", use_mock=True)
        self.mqtt_client.connect()

    def teardown_method(self):
        if self.mqtt_client.connected:
            self.mqtt_client.disconnect()
        InMemoryMQTTBroker.reset_instance()

    def test_01_camera_message_contract_serialization(self):
        """Verifies CameraMessageContract Base64 JSON serialization and deserialization."""
        raw_jpeg = create_realistic_jpeg_bytes(scenario="BLOOM")
        contract = CameraMessageContract(
            device_id="AQUA_FRESH_001",
            frame_id="frame_000100",
            timestamp=datetime.datetime.now().isoformat(),
            width=224,
            height=224,
            channels=3,
            format="JPEG",
            image_bytes=raw_jpeg,
            status="OK",
            quality_valid=True,
            metadata={"hardware": "ESP32-CAM"}
        )

        payload = contract.to_mqtt_payload()
        assert isinstance(payload, dict)
        assert payload["frame_id"] == "frame_000100"
        assert "image_b64" in payload
        assert len(payload["image_b64"]) > 0

        deserialized, is_valid, err = CameraMessageContract.from_mqtt_payload(payload)
        assert is_valid is True
        assert err == "OK"
        assert deserialized is not None
        assert deserialized.frame_id == "frame_000100"
        assert deserialized.image_bytes == raw_jpeg

    def test_02_camera_transport_receiver_mqtt_flow(self):
        """Verifies MQTT image transport message reception by CameraTransportReceiver."""
        receiver = CameraTransportReceiver(
            name="TEST_RECEIVER",
            mqtt_client=self.mqtt_client,
            topic_pattern="aquatic/+/camera/raw"
        )
        receiver.init()

        raw_jpeg = create_realistic_jpeg_bytes(scenario="NORMAL")
        contract = CameraMessageContract(
            device_id="AQUA_FRESH_001",
            frame_id="frame_000101",
            timestamp=datetime.datetime.now().isoformat(),
            width=224,
            height=224,
            channels=3,
            format="JPEG",
            image_bytes=raw_jpeg
        )

        # Publish frame over MQTT
        sender_client = MQTTClient(client_id="CAM_SENDER", use_mock=True)
        sender_client.connect()
        sender_client.publish("aquatic/AQUA_FRESH_001/camera/raw", contract.to_mqtt_payload())

        captured_frame = receiver.capture_frame()
        assert captured_frame is not None
        assert captured_frame.frame_id == "frame_000101"
        assert captured_frame.quality_valid is True
        assert captured_frame.status == "OK"
        assert captured_frame.image_bytes == raw_jpeg

    def test_03_end_to_end_physical_jpeg_pipeline(self):
        """
        Verifies complete physical JPEG bytes transport through V4.1 to V4.7 pipeline:
        Physical JPEG Bytes -> TransportReceiver -> CameraFrame -> Preprocessor -> MobileNetV3 -> VisualDetector -> Fusion -> DecisionAdapter -> Orchestrator
        """
        orchestrator = MultimodalRuntimeOrchestrator(max_queue_size=5)
        receiver = CameraTransportReceiver(
            name="PROD_RECEIVER",
            mqtt_client=self.mqtt_client,
            topic_pattern="aquatic/+/camera/raw"
        )
        receiver.init()

        raw_jpeg = create_realistic_jpeg_bytes(scenario="BLOOM")
        contract = CameraMessageContract(
            device_id="AQUA_FRESH_001",
            frame_id="frame_e2e_001",
            timestamp=datetime.datetime.now().isoformat(),
            width=224,
            height=224,
            channels=3,
            format="JPEG",
            image_bytes=raw_jpeg
        )

        sender_client = MQTTClient(client_id="CAM_SENDER_E2E", use_mock=True)
        sender_client.connect()
        sender_client.publish("aquatic/AQUA_FRESH_001/camera/raw", contract.to_mqtt_payload())

        acquired_frame = receiver.capture_frame()
        assert acquired_frame.frame_id == "frame_e2e_001"

        # Create valid telemetry feature row
        X_df = pd.DataFrame([{
            'lat': 27.5, 'lon': -81.2, 'distance_to_water_m': 120.0,
            'region': 'south', 'Season': 'Summer', 'Year': 2026,
            'Month_sin': 0.0, 'Month_cos': -1.0, 'DayOfYear_sin': 0.5, 'DayOfYear_cos': -0.866
        }])
        sensors = {"temperature_c": 26.5, "ph": 8.4, "turbidity_ntu": 12.0, "dissolved_oxygen_mg_l": 5.2, "sensor_status": "OK"}

        result = orchestrator.process_multimodal_observation(
            dataset_key="caml",
            X_df=X_df,
            sensors=sensors,
            camera_frame=acquired_frame
        )

        assert isinstance(result, MultimodalObservationResult)
        assert result.camera_status == "OK"
        assert result.modality_availability["visual"] is True
        assert result.latency.total_pipeline_ms > 0

    def test_04_fault_empty_jpeg_bytes(self):
        """Verifies empty JPEG bytes produces CAMERA_FAULT and NEVER NO_BLOOM."""
        receiver = CameraTransportReceiver(mqtt_client=self.mqtt_client)
        receiver.init()

        payload = {
            "device_id": "AQUA_FRESH_001",
            "frame_id": "frame_empty_01",
            "timestamp": datetime.datetime.now().isoformat(),
            "image_b64": "" # Empty Base64 payload
        }
        self.mqtt_client.publish("aquatic/AQUA_FRESH_001/camera/raw", payload)

        frame = receiver.capture_frame()
        assert frame.quality_valid is False
        assert frame.status in ["EMPTY_PAYLOAD", "CAMERA_OFFLINE"]

        # Run through preprocessor and visual detector
        preproc = ImagePreprocessor()
        pre_img = preproc.process(frame)
        assert pre_img.valid is False

        model = AquaticBloomCVModel()
        model.load()
        pred = model.predict(pre_img)

        detector = VisualDetector()
        evidence = detector.evaluate_prediction(pred)

        assert evidence.visual_state == "CAMERA_FAULT"
        assert evidence.visual_state != "NO_VISUAL_BLOOM"

    def test_05_fault_corrupted_jpeg_bytes(self):
        """Verifies corrupted non-JPEG byte payload produces CAMERA_FAULT and NEVER NO_BLOOM."""
        receiver = CameraTransportReceiver(mqtt_client=self.mqtt_client)
        receiver.init()

        corrupted_bytes = b"CORRUPTED_NON_IMAGE_RAW_DATA_PAYLOAD"
        payload = {
            "device_id": "AQUA_FRESH_001",
            "frame_id": "frame_corrupt_01",
            "timestamp": datetime.datetime.now().isoformat(),
            "image_b64": base64.b64encode(corrupted_bytes).decode("utf-8")
        }
        self.mqtt_client.publish("aquatic/AQUA_FRESH_001/camera/raw", payload)

        frame = receiver.capture_frame()
        assert frame.quality_valid is False
        assert frame.status in ["CORRUPTED", "CAMERA_OFFLINE"]

        detector = VisualDetector()
        model = AquaticBloomCVModel()
        model.load()
        evidence = detector.evaluate_prediction(model.predict(ImagePreprocessor().process(frame)))

        assert evidence.visual_state == "CAMERA_FAULT"
        assert evidence.visual_state != "NO_VISUAL_BLOOM"

    def test_06_fault_oversized_payload(self):
        """Verifies oversized payloads (>500 KB) produce OVERSIZED_PAYLOAD fault."""
        receiver = CameraTransportReceiver(mqtt_client=self.mqtt_client)
        receiver.init()

        huge_bytes = b"\xff\xd8" + (b"X" * (600 * 1024)) + b"\xff\xd9"
        payload = {
            "device_id": "AQUA_FRESH_001",
            "frame_id": "frame_huge_01",
            "timestamp": datetime.datetime.now().isoformat(),
            "image_b64": base64.b64encode(huge_bytes).decode("utf-8")
        }
        self.mqtt_client.publish("aquatic/AQUA_FRESH_001/camera/raw", payload)

        frame = receiver.capture_frame()
        assert frame.quality_valid is False
        assert frame.status in ["OVERSIZED_PAYLOAD", "CAMERA_OFFLINE"]

    def test_07_camera_offline_disconnect_flow(self):
        """Verifies camera disconnect produces CAMERA_OFFLINE and degrades safely to sensor evidence."""
        receiver = CameraTransportReceiver(mqtt_client=self.mqtt_client)
        receiver.init()
        receiver.set_camera_offline()

        frame = receiver.capture_frame()
        assert frame.quality_valid is False
        assert frame.status == "CAMERA_OFFLINE"

        detector = VisualDetector()
        model = AquaticBloomCVModel()
        model.load()
        evidence = detector.evaluate_prediction(model.predict(ImagePreprocessor().process(frame)))
        assert evidence.visual_state == "CAMERA_FAULT"

        # Fuse evidence with normal sensor decision
        engine = FusionEngine()
        ml_ev = {
            "dataset": "caml",
            "predicted_class": 0,
            "class_probabilities": {"NORMAL": 0.95, "BLOOM": 0.05},
            "confidence": 0.95,
            "dangerous_class": False,
            "model_id": "caml_phase3_champion"
        }
        ais_ev = {
            "dataset": "caml",
            "is_anomaly": False,
            "anomaly_score": 0.1,
            "matched_detector_count": 0,
            "nearest_detector_distance": 0.5,
            "ais_model_id": "caml_nsa_v1"
        }
        fused = engine.fuse(ml_ev, ais_ev, visual_evidence=evidence)
        assert fused["fusion"]["final_state"] == "NORMAL"
        assert fused["fusion"]["reason_code"] == "VISUAL_CAMERA_FAULT"

    def test_08_duplicate_and_stale_frame_filtering(self):
        """Verifies receiver drops duplicate frame_ids and stale timestamps cleanly."""
        receiver = CameraTransportReceiver(mqtt_client=self.mqtt_client)
        receiver.init()

        raw_jpeg = create_realistic_jpeg_bytes(scenario="NORMAL")
        t_now = datetime.datetime.now()
        t_past = t_now - datetime.timedelta(seconds=30)

        contract1 = CameraMessageContract(
            device_id="AQUA_FRESH_001", frame_id="frame_dup_01",
            timestamp=t_now.isoformat(), width=224, height=224, channels=3, format="JPEG", image_bytes=raw_jpeg
        )

        # Publish frame 1
        self.mqtt_client.publish("aquatic/AQUA_FRESH_001/camera/raw", contract1.to_mqtt_payload())
        assert receiver.frame_count == 1

        # Publish duplicate frame 1
        self.mqtt_client.publish("aquatic/AQUA_FRESH_001/camera/raw", contract1.to_mqtt_payload())
        assert receiver.frame_count == 1 # Duplicate dropped
        assert receiver.dropped_duplicate_count == 1

        # Publish stale frame with past timestamp
        contract_stale = CameraMessageContract(
            device_id="AQUA_FRESH_001", frame_id="frame_stale_01",
            timestamp=t_past.isoformat(), width=224, height=224, channels=3, format="JPEG", image_bytes=raw_jpeg
        )
        self.mqtt_client.publish("aquatic/AQUA_FRESH_001/camera/raw", contract_stale.to_mqtt_payload())
        assert receiver.frame_count == 1 # Stale dropped
        assert receiver.dropped_stale_count == 1

    def test_09_model_failure_safety_verification(self):
        """
        Step 17 Verification: Verifies missing/corrupt model file produces INFERENCE_FAILURE
        and NEVER silently falls back or produces false NO_BLOOM in production mode.
        """
        model = AquaticBloomCVModel(model_path="invalid/path/non_existent_model.pt")
        # Force model status to OFFLINE to simulate failed loading
        model.status = "OFFLINE"
        
        preproc = ImagePreprocessor()
        valid_frame = CameraFrame(
            frame_id="f1", timestamp=datetime.datetime.now().isoformat(),
            width=224, height=224, channels=3, format="JPEG",
            image_bytes=create_realistic_jpeg_bytes("BLOOM"), quality_valid=True, status="OK"
        )
        pre_img = preproc.process(valid_frame)
        pred = model.predict(pre_img)
        assert pred.status == "MODEL_OFFLINE"

        detector = VisualDetector()
        evidence = detector.evaluate_prediction(pred)
        assert evidence.visual_state == "INFERENCE_FAILURE"
        assert evidence.visual_state != "NO_VISUAL_BLOOM"

    def test_10_v3_8_frozen_source_files_protection(self):
        """Verifies that all 5 frozen V3.8 source files remain completely untouched."""
        import subprocess
        frozen_files = [
            "src/iot/esp32_device.py",
            "src/iot/communication.py",
            "src/iot/scheduler.py",
            "src/iot/hal.py",
            "src/iot/actuators.py"
        ]
        result = subprocess.run(["git", "status", "--porcelain"] + frozen_files, capture_output=True, text=True)
        assert result.stdout.strip() == "", f"Frozen V3.8 files modified: {result.stdout}"
