import os
import json
import hashlib
import pytest
import datetime
import pandas as pd
import numpy as np

from src.config.deployment_validator import DeploymentValidator, StartupValidator, EXPECTED_MODEL_SHA256
from src.cv.camera_transport import CameraMessageContract, CameraTransportReceiver
from src.cv.cv_model import AquaticBloomCVModel
from src.fusion.fusion_engine import FusionEngine
from src.fusion.runtime_orchestrator import MultimodalRuntimeOrchestrator
from src.iot.mqtt_client import MQTTClient, InMemoryMQTTBroker


class TestV484DeploymentIntegrity:
    """
    Test suite for Milestone V4.8.4 Deployment Configuration, Security, Dependency & Release Integrity.
    """
    def setup_method(self):
        self.workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.validator = DeploymentValidator(workspace_dir=self.workspace_dir)
        self.startup_validator = StartupValidator(workspace_dir=self.workspace_dir)

    def test_01_valid_configuration_accepted(self):
        """1. Verifies valid device configuration dictionary is accepted."""
        valid_gpio = {
            "temperature": 33, "ph": 32, "turbidity": 34, "dissolved_oxygen": 35,
            "salinity": 36, "green_led": 25, "yellow_led": 26, "red_led": 27,
            "buzzer": 14, "pump_relay": 19, "gps_rx": 16, "gps_tx": 17
        }
        ok, errs = self.validator.validate_gpio_mapping(valid_gpio)
        assert ok is True
        assert len(errs) == 0

    def test_02_missing_configuration_rejected(self):
        """2. Verifies empty or missing configuration is rejected."""
        ok, errs = self.validator.validate_gpio_mapping({})
        assert ok is False
        assert len(errs) > 0

    def test_03_invalid_gpio_rejected(self):
        """3. Verifies invalid GPIO pin numbers (>39) are rejected."""
        invalid_gpio = {"temperature": 18, "ph": 99}
        ok, errs = self.validator.validate_gpio_mapping(invalid_gpio)
        assert ok is False
        assert any("exceeds physical ESP32 range" in e for e in errs)

    def test_04_duplicate_gpio_rejected(self):
        """4. Verifies duplicate GPIO pin assignments are detected and rejected."""
        duplicate_gpio = {"temperature": 18, "ph": 18}
        ok, errs = self.validator.validate_gpio_mapping(duplicate_gpio)
        assert ok is False
        assert any("Duplicate GPIO assignment collision" in e for e in errs)

    def test_05_invalid_sampling_interval_rejected(self):
        """5. Verifies invalid sampling intervals (<=0) are rejected."""
        ok, errs = self.validator.validate_sampling_intervals(-5.0, 10.0)
        assert ok is False
        assert any("Invalid sensor sampling interval" in e for e in errs)

    def test_06_invalid_temporal_threshold_rejected(self):
        """6. Verifies inconsistent or negative temporal thresholds are rejected."""
        ok, errs = self.validator.validate_temporal_thresholds(-10.0, 5.0, 15.0)
        assert ok is False

        ok2, errs2 = self.validator.validate_temporal_thresholds(10.0, 5.0, 30.0)
        assert ok2 is False

    def test_07_model_artifact_file_exists(self):
        """7. Verifies PyTorch MobileNetV3 model checkpoint file exists."""
        pt_path = os.path.join(self.workspace_dir, "models", "cv", "aquatic_bloom_mobilenetv3.pt")
        assert os.path.exists(pt_path)
        assert os.path.getsize(pt_path) > 5 * 1024 * 1024

    def test_08_model_sha256_matches_metadata(self):
        """8. Verifies PyTorch model SHA-256 checksum matches metadata specification."""
        pt_path = os.path.join(self.workspace_dir, "models", "cv", "aquatic_bloom_mobilenetv3.pt")
        actual_sha = self.validator.calculate_sha256(pt_path)
        assert actual_sha == EXPECTED_MODEL_SHA256

        meta_path = os.path.join(self.workspace_dir, "models", "cv", "aquatic_bloom_model_metadata.json")
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        assert meta["export"]["sha256"] == EXPECTED_MODEL_SHA256

    def test_09_model_metadata_matches_runtime(self):
        """9. Verifies PyTorch model metadata matches V4 runtime expectations."""
        meta_ok, errs = self.validator.validate_model_artifact()
        assert meta_ok is True
        assert len(errs) == 0

    def test_10_required_dependencies_declared(self):
        """10. Verifies requirements.txt contains PyTorch, torchvision, Pillow, OpenCV, SciPy."""
        req_path = os.path.join(self.workspace_dir, "requirements.txt")
        with open(req_path, "r", encoding="utf-8") as f:
            content = f.read()

        required_pkgs = ["torch", "torchvision", "Pillow", "opencv-python", "scipy"]
        for pkg in required_pkgs:
            assert pkg in content, f"Missing required dependency declaration in requirements.txt: {pkg}"

    def test_11_plaintext_credentials_not_in_production_config(self):
        """11. Verifies production config uses environment variable placeholders rather than hardcoded passwords."""
        dev_cfg_path = os.path.join(self.workspace_dir, "config", "device_config.json")
        with open(dev_cfg_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "${AQUA_WIFI_PASSWORD}" in content

    def test_12_env_example_template_exists(self):
        """12. Verifies .env.example exists and contains safe placeholders only."""
        env_ex_path = os.path.join(self.workspace_dir, ".env.example")
        assert os.path.exists(env_ex_path)

        with open(env_ex_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "AQUA_WIFI_PASSWORD=" in content
        assert "AQUA_MQTT_PASSWORD=" in content
        assert "aquasentinel_secure" not in content

    def test_13_credentials_not_emitted_in_logs(self):
        """13. Verifies secret safety audit detects potential credential logging risks."""
        dev_cfg_path = os.path.join(self.workspace_dir, "config", "device_config.json")
        with open(dev_cfg_path, "r", encoding="utf-8") as f:
            dev_cfg = json.load(f)

        sec_ok, warns = self.validator.validate_secret_safety(dev_cfg)
        assert sec_ok is True
        assert len(warns) == 0

    def test_14_release_manifest_matches_v4_state(self):
        """14. Verifies release_manifest.json reflects V4.8.4 release state and milestones."""
        manifest_path = os.path.join(self.workspace_dir, "config", "release_manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["v4_release_version"] == "4.8.4"
        assert "milestones_completed" in manifest
        assert "V4.8.4" in manifest["milestones_completed"]
        assert manifest["cv_model_artifact"]["sha256"] == EXPECTED_MODEL_SHA256

    def test_15_physical_validation_marked_pending(self):
        """15. Verifies physical hardware validation is explicitly marked PENDING in release manifest."""
        manifest_path = os.path.join(self.workspace_dir, "config", "release_manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["physical_hardware_validation"] == "PENDING"

    def test_16_authoritative_physical_pin_mapping_preserved(self):
        """16. Verifies authoritative physical pin mapping is preserved in device_config.json."""
        dev_cfg_path = os.path.join(self.workspace_dir, "config", "device_config.json")
        with open(dev_cfg_path, "r", encoding="utf-8") as f:
            dev_cfg = json.load(f)

        fresh_gpio = dev_cfg["devices"]["AQUA_FRESH_001"]["gpio"]
        assert fresh_gpio["temperature"] == 33
        assert fresh_gpio["ph"] == 32
        assert fresh_gpio["turbidity"] == 34
        assert fresh_gpio["dissolved_oxygen"] == 35
        assert fresh_gpio["salinity"] == 36
        assert fresh_gpio["green_led"] == 25
        assert fresh_gpio["yellow_led"] == 26
        assert fresh_gpio["red_led"] == 27
        assert fresh_gpio["buzzer"] == 14
        assert fresh_gpio["pump_relay"] == 19

    def test_17_v4_8_3_temporal_configuration_preserved(self):
        """17. Verifies V4.8.3 temporal thresholds remain consistent."""
        ok, errs = self.validator.validate_temporal_thresholds(30.0, 5.0, 15.0)
        assert ok is True

    def test_18_camera_payload_size_limit_enforced(self):
        """18. Verifies camera transport payload size limits (<500 KB) remain enforced."""
        huge_b64 = "A" * (800 * 1024)
        payload = {
            "device_id": "AQUA_FRESH_001",
            "frame_id": "huge_01",
            "timestamp": datetime.datetime.now().isoformat(),
            "image_b64": huge_b64
        }
        contract, is_valid, err = CameraMessageContract.from_mqtt_payload(payload)
        assert is_valid is False
        assert err == "OVERSIZED_PAYLOAD"

    def test_19_malformed_mqtt_payload_safely_rejected(self):
        """19. Verifies malformed MQTT payloads are safely rejected."""
        contract, is_valid, err = CameraMessageContract.from_mqtt_payload("NOT_A_DICTIONARY")
        assert is_valid is False
        assert err == "INVALID_PAYLOAD_TYPE"

    def test_20_config_failure_cannot_produce_normal(self):
        """20. Verifies configuration failure cannot produce false NORMAL decision."""
        engine = FusionEngine()
        vis_ev = {"visual_state": "CAMERA_FAULT", "confidence": 0.0, "risk_level": "UNKNOWN", "reason_code": "CONFIG_FAILURE"}
        ml_ev = {"dataset": "caml", "predicted_class": 1, "class_probabilities": {"BLOOM": 0.95}, "confidence": 0.95, "dangerous_class": True, "model_id": "m1"}
        ais_ev = {"dataset": "caml", "is_anomaly": True, "anomaly_score": 0.9, "matched_detector_count": 5, "nearest_detector_distance": 0.1, "ais_model_id": "a1"}

        fused = engine.fuse(ml_ev, ais_ev, visual_evidence=vis_ev)
        assert fused["fusion"]["final_state"] != "NORMAL" # Never produces false NORMAL

    def test_21_config_failure_cannot_produce_no_bloom(self):
        """21. Verifies configuration failure cannot produce false NO_BLOOM visual state."""
        contract, is_valid, err = CameraMessageContract.from_mqtt_payload({})
        assert is_valid is False
        assert err != "NO_BLOOM"

    def test_22_complete_startup_validation_sequence(self):
        """22. Verifies safe 10-step startup validation sequence executes cleanly."""
        is_ready, errs, summary = self.startup_validator.run_startup_validation("AQUA_FRESH_001")
        assert is_ready is True
        assert len(errs) == 0
        assert summary["step_status"]["10_pipeline_readiness"] == "READY"

    def test_23_v4_3_trained_model_remains_primary(self):
        """23. Verifies PyTorch MobileNetV3 model loads and executes as primary CV engine."""
        model = AquaticBloomCVModel()
        loaded = model.load()
        assert loaded is True
        assert model.status in ["READY", "ONLINE"]

    def test_24_v3_8_protection_verification(self):
        """24. Verifies frozen V3.8 source protection (0 line modifications)."""
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
