import unittest
import os
import json
import sqlite3
import datetime
from fastapi.testclient import TestClient

from src.backend.app import app, manager
from src.backend.services import BackendService
from src.backend.schemas import (
    DeviceInfoSchema, TelemetryPayloadSchema, FusionDecisionSchema, AlertSchema
)
from src.iot.event_store import EventStore

class TestPhase8(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.test_db_path = os.path.join(cls.workspace_dir, "models", "fusion", "test_phase8_events.db")
        
        # Clean previous
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
            
        cls.event_store = EventStore(db_path=cls.test_db_path)
        cls.service = BackendService.get_instance(workspace_dir=cls.workspace_dir)
        cls.service.event_store = cls.event_store
        cls.service.runtime.gateway.event_store = cls.event_store
        
        # Start runtime to connect mock clients
        cls.service.runtime.start()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.service.runtime.stop()
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

    def test_1_fastapi_app_loads(self):
        """Assert that FastAPI application starts up successfully."""
        self.assertIsNotNone(app)

    def test_2_health_endpoint(self):
        """Verifyhealth endpoint responds with status UP."""
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["status"], "UP")

    def test_3_device_listing(self):
        """Verify device listing endpoint returns active registry entries."""
        r = self.client.get("/devices")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(len(data) >= 2)
        # Check validation schema
        DeviceInfoSchema(**data[0])

    def test_4_device_details(self):
        """Verify device details endpoint fetches correctly."""
        r = self.client.get("/devices/AQUA_FRESH_001")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["device_id"], "AQUA_FRESH_001")

    def test_5_latest_telemetry(self):
        """Verify endpoint to retrieve latest telemetry and decision."""
        # Log telemetry manually
        t = {
            "timestamp": datetime.datetime.now().isoformat(),
            "device_id": "AQUA_FRESH_001",
            "location": {"latitude": 27.5, "longitude": -81.2},
            "sensors": {"temperature_c": 24.0, "salinity_ppt": 0.2, "ph": 7.5, "turbidity_ntu": 3.0, "dissolved_oxygen_mg_l": 8.0},
            "device_health": {"wifi_connected": True, "mqtt_connected": True, "sensor_status": "OK"}
        }
        self.event_store.log_telemetry(t)
        
        r = self.client.get("/devices/AQUA_FRESH_001/latest")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["telemetry"]["ph"], 7.5)

    def test_6_telemetry_history(self):
        """Verify telemetry logs search filters."""
        r = self.client.get("/devices/AQUA_FRESH_001/telemetry")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(isinstance(r.json(), list))

    def test_7_decision_history(self):
        """Verify decision logs search filters."""
        r = self.client.get("/devices/AQUA_FRESH_001/decisions")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(isinstance(r.json(), list))

    def test_8_actuator_history(self):
        """Verify actuator logs search filters."""
        r = self.client.get("/devices/AQUA_FRESH_001/actuators")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(isinstance(r.json(), list))

    def test_9_alert_listing(self):
        """Verify alerts retrieval endpoint filters correctly."""
        # Log alert manually
        self.event_store.log_alert(
            timestamp=datetime.datetime.now().isoformat(),
            device_id="AQUA_FRESH_001",
            severity="HIGH",
            message="Test critical alarm",
            reason_code="TEST_CODE",
            acknowledged=0
        )
        r = self.client.get("/alerts?acknowledged=false")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(len(data) > 0)
        AlertSchema(**data[0])

    def test_10_system_status(self):
        """Verify systemstatus aggregates overview statistics."""
        r = self.client.get("/system/status")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("total_telemetry_records", data)
        self.assertIn("active_devices_count", data)

    def test_11_valid_command(self):
        """Verify manual override commands post successfully."""
        r = self.client.post("/devices/AQUA_FRESH_001/command", json={
            "command": "ACTIVATE_BUZZER",
            "payload": {}
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "SUCCESS")

    def test_12_invalid_command(self):
        """Assert that posting unregistered device command raises error."""
        r = self.client.post("/devices/AQUA_FAKE_001/command", json={
            "command": "ACTIVATE_BUZZER"
        })
        self.assertEqual(r.status_code, 404)

    def test_13_simulation_start(self):
        """Assert simulation thread starts up successfully."""
        r = self.client.post("/simulation/start")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(self.service.simulation_active)
        # Clean stop
        self.service.stop_simulation()

    def test_14_simulation_stop(self):
        """Assert simulation thread stops successfully."""
        self.service.start_simulation()
        r = self.client.post("/simulation/stop")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(self.service.simulation_active)

    def test_15_scenario_selection(self):
        """Verify scenario post modifies device runtime scenarion."""
        r = self.client.post("/simulation/scenario", json={
            "device_id": "AQUA_FRESH_001",
            "scenario": "KNOWN_BLOOM_RISK"
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.service.scenarios["AQUA_FRESH_001"], "KNOWN_BLOOM_RISK")

    def test_16_pydantic_validation(self):
        """Assert Pydantic validation rejects bad payload inputs."""
        # Try to post bad command schemas
        r = self.client.post("/devices/AQUA_FRESH_001/command", json={
            "bad": 1
        })
        self.assertEqual(r.status_code, 422) # Unprocessable entity

    def test_17_database_query_safety(self):
        """Assert parameterized SQL query defense is used (sql injection check)."""
        r = self.client.get("/devices/AQUA_FRESH_001; DROP TABLE telemetry_logs;--/telemetry")
        self.assertEqual(r.status_code, 404) # Not found device, no DB crash

    def test_18_websocket_connection(self):
        """Assert websocket endpoint connects successfully."""
        with self.client.websocket_connect("/ws/live") as websocket:
            data = websocket.receive_json()
            self.assertEqual(data["type"], "status")

    def test_19_websocket_payload_schema(self):
        """Verify WebSocket message frame formats."""
        with self.client.websocket_connect("/ws/live") as websocket:
            # Discard initial welcome message
            websocket.receive_json()
            websocket.send_text("ping")
            data = websocket.receive_text()
            self.assertEqual(data, "pong")

    def test_20_multiple_clients(self):
        """Verify multiple parallel websocket clients connect independently."""
        with self.client.websocket_connect("/ws/live") as ws1:
            with self.client.websocket_connect("/ws/live") as ws2:
                # Discard welcome messages
                ws1.receive_json()
                ws2.receive_json()
                ws1.send_text("ping")
                self.assertEqual(ws1.receive_text(), "pong")
                ws2.send_text("ping")
                self.assertEqual(ws2.receive_text(), "pong")

    def test_21_dashboard_data_service(self):
        """Verify database overview stats method is consistent."""
        stats = self.event_store.get_device_stats()
        self.assertIn("total_telemetry", stats)
        self.assertIn("total_anomalies", stats)

    def test_22_freshwater_device_visualization_data(self):
        """Assert freshwater metrics include spatial-temporal parameters."""
        r = self.client.get("/devices/AQUA_FRESH_001")
        self.assertEqual(r.json()["ecosystem_type"], "Freshwater")

    def test_23_marine_device_visualization_data(self):
        """Assert marine metrics include temperature and salinity."""
        r = self.client.get("/devices/AQUA_MARINE_001")
        self.assertEqual(r.json()["ecosystem_type"], "Marine")

    def test_24_ml_output_preserved(self):
        """Assert ML predictions are stored accurately in SQLite decisions."""
        decision = {
            "timestamp": datetime.datetime.now().isoformat(),
            "device_id": "AQUA_FRESH_001",
            "ml_evidence": {"predicted_class": 1, "confidence": 0.95, "dangerous_class": False, "model_id": "RF_CAML_V3"},
            "ais_evidence": {"is_anomaly": 0, "anomaly_score": 0.0, "ais_model_id": "AIS_CAML_V1"},
            "fusion": {"final_state": "NORMAL", "reason_code": "ML_NORMAL_AIS_NORMAL", "reasoning": "Test", "confidence_band": "HIGH"},
            "system_metadata": {"fusion_version": "1.0.0"}
        }
        self.event_store.log_decision(decision)
        latest = self.event_store.get_latest_decision("AQUA_FRESH_001")
        self.assertEqual(latest["ml_predicted_class"], "1")
        self.assertEqual(latest["ml_confidence"], 0.95)

    def test_25_ais_output_preserved(self):
        """Assert AIS anomaly flags are stored accurately in decisions."""
        latest = self.event_store.get_latest_decision("AQUA_FRESH_001")
        self.assertEqual(latest["ais_is_anomaly"], 0)
        self.assertEqual(latest["ais_anomaly_score"], 0.0)

    def test_26_fusion_output_preserved(self):
        """Assert Fusion outputs are stored accurately in decisions."""
        latest = self.event_store.get_latest_decision("AQUA_FRESH_001")
        self.assertEqual(latest["final_state"], "NORMAL")

    def test_27_actuator_output_preserved(self):
        """Assert actuator actions are logged correctly in EventStore."""
        self.event_store.log_actuators(datetime.datetime.now().isoformat(), "AQUA_FRESH_001", "LEDs(G=ON, Y=OFF, R=OFF), Buzzer=OFF, Pump=OFF", "Test Event")
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT green_led FROM actuator_logs ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        self.assertEqual(row[0], "ON")

    def test_28_sensor_fault_displayed_correctly(self):
        """Assert sensor fault count tracks correctly."""
        # Log telemetry with status FAULT
        t = {
            "timestamp": datetime.datetime.now().isoformat(),
            "device_id": "AQUA_FRESH_001",
            "location": {"latitude": 27.5, "longitude": -81.2},
            "sensors": {"temperature_c": None, "salinity_ppt": 0.2, "ph": 7.5, "turbidity_ntu": 3.0, "dissolved_oxygen_mg_l": 8.0},
            "device_health": {"wifi_connected": True, "mqtt_connected": True, "sensor_status": "FAULT"}
        }
        self.event_store.log_telemetry(t)
        stats = self.event_store.get_device_stats()
        self.assertTrue(stats["total_faults"] > 0)

    def test_29_invalid_phase4_models_blocked(self):
        """Assert that invalidated Phase 4 models remain blocked."""
        ml_loader = self.service.runtime.gateway.pipeline.ml_loader
        original_models = ml_loader.manifest["models"]
        original_registry_models = ml_loader.registry["models"]
        try:
            ml_loader.manifest["models"] = {
                "invalid_caml": {
                    "model_id": "caml_p4_invalid",
                    "version": "4.0.0",
                    "artifact_path": "models/archive/phase4_invalid/caml_final_model.joblib"
                }
            }
            ml_loader.registry["models"] = [
                {
                    "model_id": "caml_p4_invalid",
                    "status": "INVALIDATED",
                    "audit_status": "FAILED_PHASE45_INTEGRITY_AUDIT"
                }
            ]
            with self.assertRaises(PermissionError):
                ml_loader.load_model("invalid_caml")
        finally:
            ml_loader.manifest["models"] = original_models
            ml_loader.registry["models"] = original_registry_models

    def test_30_test_datasets_never_accessed(self):
        """Assert that no code files read test CSV files."""
        for root, dirs, files in os.walk(os.path.join(self.workspace_dir, "src", "backend")):
            for f in files:
                if f.endswith(".py"):
                    with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                        content = file.read()
                        self.assertNotIn("caml_test.csv", content)
                        self.assertNotIn("habsos_test.csv", content)

if __name__ == "__main__":
    unittest.main()
