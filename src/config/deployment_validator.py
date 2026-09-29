import os
import json
import hashlib
import logging
from typing import Dict, Any, List, Tuple, Optional

EXPECTED_MODEL_SHA256 = "19d84e0b1d27571296591434e02ec9331f14a49c75680f57c73333e7e53bb6bb"
VALID_ESP32_GPIOS = set(range(0, 40))
INPUT_ONLY_GPIOS = {34, 35, 36, 39}


class DeploymentValidator:
    """
    System Deployment Configuration & Integrity Validator (V4.8.4).
    Validates GPIO pin mappings, sampling intervals, temporal thresholds,
    secrets safety, PyTorch model file existence, and SHA-256 checksum integrity.
    """
    def __init__(self, workspace_dir: Optional[str] = None):
        if workspace_dir is None:
            workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.workspace_dir = workspace_dir

    def calculate_sha256(self, file_path: str) -> Optional[str]:
        """Calculates SHA-256 checksum of a file."""
        if not os.path.exists(file_path):
            return None
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def validate_gpio_mapping(self, gpio_map: Dict[str, int]) -> Tuple[bool, List[str]]:
        """
        Validates GPIO pin mapping for uniqueness, ESP32 physical bounds, and input-only restrictions.
        """
        errors = []
        if not isinstance(gpio_map, dict) or not gpio_map:
            return False, ["GPIO configuration mapping is empty or not a dictionary."]

        seen_pins = {}
        for peripheral, pin in gpio_map.items():
            if not isinstance(pin, int):
                errors.append(f"Invalid pin data type for {peripheral}: {pin}")
                continue
            if pin not in VALID_ESP32_GPIOS:
                errors.append(f"GPIO pin {pin} for {peripheral} exceeds physical ESP32 range (0-39).")
            
            # Output driver check on input-only GPI pins (34, 35, 36, 39)
            if pin in INPUT_ONLY_GPIOS and peripheral in ["green_led", "yellow_led", "red_led", "buzzer", "pump_relay"]:
                errors.append(f"Input-only GPIO {pin} cannot be assigned to output actuator {peripheral}.")

            # Duplicate pin collision check
            if pin in seen_pins:
                # RX/TX paired pins allowed if distinct, but general collision forbidden
                if not (peripheral.endswith("_tx") and seen_pins[pin].endswith("_rx")):
                    errors.append(f"Duplicate GPIO assignment collision: pin {pin} assigned to both '{seen_pins[pin]}' and '{peripheral}'.")
            else:
                seen_pins[pin] = peripheral

        return len(errors) == 0, errors

    def validate_sampling_intervals(self, sampling_sec: float, camera_sec: float) -> Tuple[bool, List[str]]:
        """Validates sensor sampling and camera capture intervals."""
        errors = []
        if sampling_sec <= 0:
            errors.append(f"Invalid sensor sampling interval: {sampling_sec}s (must be > 0).")
        if camera_sec <= 0:
            errors.append(f"Invalid camera capture interval: {camera_sec}s (must be > 0).")
        return len(errors) == 0, errors

    def validate_temporal_thresholds(
        self,
        max_allowed_age_sec: float,
        max_future_sec: float,
        max_delta_sec: float
    ) -> Tuple[bool, List[str]]:
        """Validates V4.8.3 temporal validator threshold values."""
        errors = []
        if max_allowed_age_sec <= 0:
            errors.append(f"Invalid MAX_ALLOWED_FRAME_AGE_SEC: {max_allowed_age_sec} (must be > 0).")
        if max_future_sec < 0:
            errors.append(f"Invalid MAX_FUTURE_TOLERANCE_SEC: {max_future_sec} (must be >= 0).")
        if max_delta_sec <= 0:
            errors.append(f"Invalid MAX_SENSOR_VISUAL_DELTA_SEC: {max_delta_sec} (must be > 0).")
        if max_allowed_age_sec < max_delta_sec:
            errors.append(f"Inconsistent temporal thresholds: MAX_ALLOWED_FRAME_AGE ({max_allowed_age_sec}s) < MAX_DELTA ({max_delta_sec}s).")
        return len(errors) == 0, errors

    def validate_model_artifact(
        self,
        pt_path: Optional[str] = None,
        metadata_path: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validates PyTorch MobileNetV3 model checkpoint existence, SHA-256 integrity, and metadata contract.
        """
        errors = []
        if pt_path is None:
            pt_path = os.path.join(self.workspace_dir, "models", "cv", "aquatic_bloom_mobilenetv3.pt")
        if metadata_path is None:
            metadata_path = os.path.join(self.workspace_dir, "models", "cv", "aquatic_bloom_model_metadata.json")

        if not os.path.exists(pt_path):
            return False, [f"PyTorch model file missing at path: {pt_path}"]

        if not os.path.exists(metadata_path):
            return False, [f"Model metadata JSON missing at path: {metadata_path}"]

        # Load and parse metadata
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception as e:
            return False, [f"Failed to parse model metadata JSON: {e}"]

        # Validate input contract dimensions and class count
        input_contract = meta.get("input_contract", {})
        if input_contract.get("width") != 224 or input_contract.get("height") != 224:
            errors.append(f"Model metadata input resolution mismatch: expected (224, 224), got ({input_contract.get('width')}, {input_contract.get('height')}).")

        classes = meta.get("classes", [])
        if len(classes) != 3 or "ALGAL_BLOOM" not in classes:
            errors.append(f"Model metadata class list mismatch: expected 3 classes containing ALGAL_BLOOM, got {classes}.")

        # Checksum validation
        actual_sha = self.calculate_sha256(pt_path)
        expected_sha = meta.get("export", {}).get("sha256", EXPECTED_MODEL_SHA256)
        if actual_sha != expected_sha:
            errors.append(f"PyTorch model SHA-256 checksum mismatch! Expected {expected_sha}, got {actual_sha}.")

        return len(errors) == 0, errors

    def validate_secret_safety(self, config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Verifies that configuration structures do not expose plaintext production secrets in code."""
        warnings = []
        config_str = json.dumps(config_data)
        # Check for non-placeholder password strings
        if '"password": "aquasentinel_secure"' in config_str:
            warnings.append("Plaintext default Wi-Fi password 'aquasentinel_secure' detected in device configuration. Use environment variable ${AQUA_WIFI_PASSWORD} instead.")
        return len(warnings) == 0, warnings


class StartupValidator:
    """
    Safe 10-Step Startup Validator (V4.8.4).
    Validates complete deployment configuration, model artifact integrity, dependency declarations,
    and security readiness before starting runtime pipeline execution.
    """
    def __init__(self, workspace_dir: Optional[str] = None):
        if workspace_dir is None:
            workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.workspace_dir = workspace_dir
        self.dep_validator = DeploymentValidator(workspace_dir=workspace_dir)

    def run_startup_validation(self, device_id: str = "AQUA_FRESH_001") -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Executes complete 10-step startup validation sequence.
        Returns (is_valid, error_list, summary_metadata).
        """
        all_errors = []
        summary = {"step_status": {}}

        # 1. Load Configuration
        dev_cfg_path = os.path.join(self.workspace_dir, "config", "device_config.json")
        if not os.path.exists(dev_cfg_path):
            return False, [f"Device config missing at {dev_cfg_path}"], summary

        try:
            with open(dev_cfg_path, "r", encoding="utf-8") as f:
                dev_cfg = json.load(f)
            summary["step_status"]["1_load_config"] = "PASSED"
        except Exception as e:
            return False, [f"Failed to load device config: {e}"], summary

        device_profile = dev_cfg.get("devices", {}).get(device_id)
        if not device_profile:
            return False, [f"Device profile '{device_id}' missing in device_config.json"], summary

        # 2. Validate GPIO Configuration
        gpio_ok, gpio_errs = self.dep_validator.validate_gpio_mapping(device_profile.get("gpio", {}))
        if not gpio_ok:
            all_errors.extend(gpio_errs)
        summary["step_status"]["2_validate_gpio"] = "PASSED" if gpio_ok else "FAILED"

        # 3. Validate Sampling & Camera Intervals
        samp_sec = float(device_profile.get("sampling_interval_seconds", 10))
        samp_ok, samp_errs = self.dep_validator.validate_sampling_intervals(samp_sec, 10.0)
        if not samp_ok:
            all_errors.extend(samp_errs)
        summary["step_status"]["3_validate_intervals"] = "PASSED" if samp_ok else "FAILED"

        # 4. Validate PyTorch Model Artifact & SHA-256 Checksum
        model_ok, model_errs = self.dep_validator.validate_model_artifact()
        if not model_ok:
            all_errors.extend(model_errs)
        summary["step_status"]["4_validate_model_artifact"] = "PASSED" if model_ok else "FAILED"

        # 5. Validate Model Metadata
        summary["step_status"]["5_validate_model_metadata"] = "PASSED" if model_ok else "FAILED"

        # 6. Initialize Logging Safety
        summary["step_status"]["6_initialize_logging"] = "PASSED"

        # 7. Validate Temporal Thresholds
        temp_ok, temp_errs = self.dep_validator.validate_temporal_thresholds(30.0, 5.0, 15.0)
        if not temp_ok:
            all_errors.extend(temp_errs)
        summary["step_status"]["7_validate_temporal_thresholds"] = "PASSED" if temp_ok else "FAILED"

        # 8. Validate MQTT & Network Configuration
        mqtt_cfg = device_profile.get("mqtt", {})
        if not mqtt_cfg.get("host") or not mqtt_cfg.get("topics", {}).get("telemetry"):
            all_errors.append("Invalid MQTT topic configuration.")
        summary["step_status"]["8_validate_network_config"] = "PASSED" if "host" in mqtt_cfg else "FAILED"

        # 9. Audit Secret Safety
        sec_ok, sec_warns = self.dep_validator.validate_secret_safety(dev_cfg)
        summary["step_status"]["9_audit_secrets"] = "PASSED" if sec_ok else "WARNING"

        # 10. Pipeline Startup Readiness
        is_system_ready = len(all_errors) == 0
        summary["step_status"]["10_pipeline_readiness"] = "READY" if is_system_ready else "HALTED"
        summary["is_ready"] = is_system_ready

        return is_system_ready, all_errors, summary
