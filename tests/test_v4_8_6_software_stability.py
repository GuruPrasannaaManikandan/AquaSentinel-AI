import os
import sys
import json
import pytest
import datetime
import subprocess

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from src.backend.app import app
from src.backend.services import BackendService
from src.config.deployment_validator import DeploymentValidator, StartupValidator
from src.cv.camera_transport import CameraMessageContract
from src.cv.temporal_validator import TemporalValidator
from src.fusion.fusion_engine import FusionEngine
from src.fusion.runtime_orchestrator import MultimodalRuntimeOrchestrator


class TestV486SoftwareStability:
    """
    Final Acceptance Test Suite for Milestone V4.8.6 Software Stabilization & Error Elimination.
    """
    def setup_method(self):
        self.workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.service = BackendService.get_instance(self.workspace_dir)
        self.client = TestClient(app)

    def test_01_backend_health(self):
        """1. Verifies /health endpoint returns HTTP 200 OK and valid status."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["UP", "HEALTHY", "DEGRADED", "ONLINE"]

    def test_02_device_discovery(self):
        """2. Verifies /devices endpoint lists active registered devices."""
        response = self.client.get("/devices")
        assert response.status_code == 200
        devices = response.json()
        assert isinstance(devices, list)
        assert len(devices) >= 2
        device_ids = [d["device_id"] for d in devices]
        assert "AQUA_FRESH_001" in device_ids
        assert "AQUA_MARINE_001" in device_ids

    def test_03_scenario_discovery(self):
        """3. Verifies /simulation/scenarios lists valid device scenario states."""
        response = self.client.get("/simulation/scenarios")
        assert response.status_code == 200
        scenarios = response.json()
        assert "AQUA_FRESH_001" in scenarios
        assert "AQUA_MARINE_001" in scenarios

    def test_04_scenario_application(self):
        """4. Verifies POST /simulation/scenario updates device environmental scenario."""
        payload = {"device_id": "AQUA_FRESH_001", "scenario": "KNOWN_BLOOM_RISK"}
        response = self.client.post("/simulation/scenario", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"

    def test_05_single_step_cycle_execution_200_ok(self):
        """5. Verifies POST /simulation/cycle executes synchronously when stopped and returns HTTP 200 OK."""
        self.service.stop_simulation()
        response = self.client.post("/simulation/cycle")
        assert response.status_code == 200, f"Expected 200 OK when stopped, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert "results" in data

    def test_06_device_telemetry_retrieval(self):
        """6. Verifies GET /devices/{id}/telemetry returns historical telemetry records."""
        response = self.client.get("/devices/AQUA_FRESH_001/telemetry")
        assert response.status_code == 200
        records = response.json()
        assert isinstance(records, list)

    def test_07_device_latest_state(self):
        """7. Verifies GET /devices/{id}/latest returns latest telemetry reading."""
        response = self.client.get("/devices/AQUA_FRESH_001/latest")
        assert response.status_code == 200
        data = response.json()
        assert "device_id" in data

    def test_08_device_decisions_retrieval(self):
        """8. Verifies GET /devices/{id}/decisions returns historical fused decision logs."""
        response = self.client.get("/devices/AQUA_FRESH_001/decisions")
        assert response.status_code == 200
        decisions = response.json()
        assert isinstance(decisions, list)

    def test_09_system_status_kpis(self):
        """9. Verifies GET /system/status returns active KPI metrics."""
        response = self.client.get("/system/status")
        assert response.status_code == 200
        stats = response.json()
        assert "active_devices_count" in stats
        assert "total_telemetry_records" in stats

    def test_10_alerts_retrieval(self):
        """10. Verifies GET /alerts returns unacknowledged alerts list."""
        response = self.client.get("/alerts?acknowledged=false")
        assert response.status_code == 200
        alerts = response.json()
        assert isinstance(alerts, list)

    def test_11_ml_and_ais_and_fusion_integration(self):
        """11. Verifies ML, AIS, and Multimodal Fusion engine execute integrated decision pipeline."""
        engine = FusionEngine()
        vis_ev = {"visual_state": "NO_VISUAL_BLOOM", "confidence": 0.9, "risk_level": "LOW", "reason_code": "OK"}
        ml_ev = {"dataset": "caml", "predicted_class": 0, "class_probabilities": {"NORMAL": 0.95}, "confidence": 0.95, "dangerous_class": False, "model_id": "m1"}
        ais_ev = {"dataset": "caml", "is_anomaly": False, "anomaly_score": 0.1, "matched_detector_count": 0, "nearest_detector_distance": 0.8, "ais_model_id": "a1"}

        fused = engine.fuse(ml_ev, ais_ev, visual_evidence=vis_ev)
        assert fused["fusion"]["final_state"] == "NORMAL"
        assert fused["fusion"]["confidence_band"] in ["HIGH", "MEDIUM", "LOW"]

    def test_12_camera_transport_schema(self):
        """12. Verifies ESP32-CAM MQTT Schema 1.1 transport contract parsing."""
        raw_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        payload = {
            "schema_version": "1.1",
            "device_id": "AQUA_FRESH_001",
            "frame_id": "stab_test_01",
            "timestamp": datetime.datetime.now().isoformat(),
            "time_sync_status": "SYNCED",
            "clock_source": "NTP",
            "width": 224,
            "height": 224,
            "channels": 3,
            "format": "PNG",
            "image_b64": raw_b64
        }
        contract, is_valid, err = CameraMessageContract.from_mqtt_payload(payload)
        assert is_valid is True
        assert err == "OK"
        assert contract.frame_id == "stab_test_01"

    def test_13_temporal_validator_thresholds(self):
        """13. Verifies Gateway TemporalValidator threshold enforcement."""
        validator = TemporalValidator()
        now_iso = datetime.datetime.now().isoformat()
        res = validator.validate_camera_frame_temporal(
            capture_ts_str=now_iso,
            time_sync_status="SYNCED",
            clock_source="NTP",
            gateway_receive_ts_str=now_iso
        )
        assert res.temporal_valid is True
        assert res.reason_code == "OK"

    def test_14_deployment_validator_startup(self):
        """14. Verifies safe 10-step startup deployment validator."""
        startup = StartupValidator(workspace_dir=self.workspace_dir)
        is_ready, errs, summary = startup.run_startup_validation("AQUA_FRESH_001")
        assert is_ready is True
        assert len(errs) == 0

    def test_15_v3_8_frozen_source_files_protection(self):
        """15. Verifies all 5 frozen V3.8 source files contain ZERO line modifications."""
        frozen_files = [
            "src/iot/esp32_device.py",
            "src/iot/communication.py",
            "src/iot/scheduler.py",
            "src/iot/hal.py",
            "src/iot/actuators.py"
        ]
        result = subprocess.run(["git", "status", "--porcelain"] + frozen_files, capture_output=True, text=True)
        assert result.stdout.strip() == "", f"Frozen V3.8 files were modified! Output: {result.stdout}"
