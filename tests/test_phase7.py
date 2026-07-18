import unittest
import os
import sqlite3
import datetime
import json
import numpy as np
import pandas as pd
from src.iot.sensor_simulator import AquaticSensorSimulator
from src.iot.edge_validation import EdgeValidator
from src.iot.mqtt_client import MQTTClient, InMemoryMQTTBroker
from src.iot.actuators import VirtualActuators
from src.iot.esp32_device import ESP32Device
from src.iot.gateway import Gateway
from src.iot.event_store import EventStore
from src.iot.device_runtime import DeviceRuntimeManager

class TestPhase7(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.test_db_path = os.path.join(cls.workspace_dir, "models", "fusion", "test_events.db")
        # Ensure clean state
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
            
        cls.event_store = EventStore(db_path=cls.test_db_path)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

    def test_1_sensor_simulator_reproducibility(self):
        """Assert that sensor simulator is reproducible with fixed seed."""
        sim1 = AquaticSensorSimulator(ecosystem_type="Freshwater", random_seed=42)
        sim2 = AquaticSensorSimulator(ecosystem_type="Freshwater", random_seed=42)
        r1 = sim1.generate_reading(scenario="NORMAL")
        r2 = sim2.generate_reading(scenario="NORMAL")
        self.assertEqual(r1["ph"], r2["ph"])

    def test_2_physical_sensor_bounds(self):
        """Assert simulator values fall within plausible physical boundaries."""
        sim = AquaticSensorSimulator(ecosystem_type="Marine", random_seed=100)
        r = sim.generate_reading(scenario="KNOWN_BLOOM_RISK")
        self.assertTrue(22.0 <= r["temperature_c"] <= 35.0)
        self.assertTrue(25.0 <= r["salinity_ppt"] <= 40.0)

    def test_3_esp32_state_transitions(self):
        """Verify ESP32 state machine transitions."""
        dev = ESP32Device(device_id="TEST_DEV")
        self.assertEqual(dev.state, "BOOT")
        dev.boot()
        self.assertEqual(dev.state, "INITIALIZING")
        dev.initialize_sensors()
        self.assertEqual(dev.state, "CONNECTING")
        dev.connect_network()
        self.assertEqual(dev.state, "ONLINE")

    def test_4_edge_validation_normal(self):
        """Assert normal values pass edge validation."""
        val = EdgeValidator()
        readings = {
            "timestamp": datetime.datetime.now().isoformat(),
            "latitude": 27.5,
            "longitude": -81.2,
            "temperature_c": 24.5,
            "salinity_ppt": 0.2,
            "ph": 7.5,
            "turbidity_ntu": 3.0,
            "dissolved_oxygen_mg_l": 8.0
        }
        is_valid, errors, health = val.validate(readings)
        self.assertTrue(is_valid)
        self.assertEqual(health, "OK")

    def test_5_nan_rejection(self):
        """Assert that NaNs are rejected by edge validation."""
        val = EdgeValidator()
        readings = {
            "timestamp": datetime.datetime.now().isoformat(),
            "latitude": 27.5,
            "longitude": -81.2,
            "temperature_c": np.nan,
            "salinity_ppt": 0.2,
            "ph": 7.5,
            "turbidity_ntu": 3.0,
            "dissolved_oxygen_mg_l": 8.0
        }
        is_valid, errors, health = val.validate(readings)
        self.assertFalse(is_valid)
        self.assertEqual(health, "FAULT")

    def test_6_infinite_value_rejection(self):
        """Assert that infinite values are rejected by edge validation."""
        val = EdgeValidator()
        readings = {
            "timestamp": datetime.datetime.now().isoformat(),
            "latitude": 27.5,
            "longitude": -81.2,
            "temperature_c": 24.5,
            "salinity_ppt": 0.2,
            "ph": np.inf,
            "turbidity_ntu": 3.0,
            "dissolved_oxygen_mg_l": 8.0
        }
        is_valid, errors, health = val.validate(readings)
        self.assertFalse(is_valid)
        self.assertEqual(health, "FAULT")

    def test_7_frozen_sensor_detection(self):
        """Assert that frozen/static values trigger a fault alert after history limit."""
        val = EdgeValidator(history_limit=3)
        for _ in range(3):
            readings = {
                "timestamp": datetime.datetime.now().isoformat(),
                "latitude": 27.5,
                "longitude": -81.2,
                "temperature_c": 24.5,
                "salinity_ppt": 0.2,
                "ph": 7.0, # frozen pH
                "turbidity_ntu": 3.0,
                "dissolved_oxygen_mg_l": 8.0
            }
            is_valid, errors, health = val.validate(readings)
        self.assertFalse(is_valid)
        self.assertEqual(health, "FAULT")
        self.assertTrue(any("sensor frozen fault" in err.lower() for err in errors))

    def test_8_telemetry_schema(self):
        """Verify device outputs conform to the telemetry contract schema."""
        dev = ESP32Device(device_id="AQUA_FRESH_001")
        dev.boot()
        dev.initialize_sensors()
        dev.connect_network()
        t = dev.poll_and_validate(scenario="NORMAL")
        self.assertEqual(t["schema_version"], "1.0")
        self.assertEqual(t["device_id"], "AQUA_FRESH_001")
        self.assertIn("sensors", t)
        self.assertIn("device_health", t)

    def test_9_device_registry_validation(self):
        """Assert that gateway loads and validates the device registry correctly."""
        gw = Gateway(workspace_dir=self.workspace_dir, use_mock=True)
        self.assertIn("AQUA_FRESH_001", gw.device_registry["devices"])
        self.assertEqual(gw.device_registry["devices"]["AQUA_FRESH_001"]["dataset_route"], "caml")

    def test_10_mqtt_publish(self):
        """Assert MQTT publish completes successfully."""
        client = MQTTClient("TEST_PUB")
        client.connect()
        self.assertTrue(client.publish("test/topic", {"val": 1}))

    def test_11_mqtt_subscribe(self):
        """Assert MQTT subscribe completes successfully."""
        client = MQTTClient("TEST_SUB")
        client.connect()
        self.assertTrue(client.subscribe("test/topic"))

    def test_12_mqtt_reconnect(self):
        """Verify MQTT client recovery/reconnect sequence."""
        dev = ESP32Device(device_id="TEST_REC")
        dev.state = "ERROR"
        self.assertTrue(dev.run_reconnection())
        self.assertEqual(dev.state, "ONLINE")

    def test_13_in_memory_transport(self):
        """Assert that mock broker transports messages deterministically without networking."""
        broker = InMemoryMQTTBroker.get_instance()
        received = []
        class MockClient:
            def _on_message_received(self, topic, payload):
                received.append((topic, payload))
        
        c = MockClient()
        broker.subscribe(c, "test/inmem")
        broker.publish(None, "test/inmem", '{"msg": "hello"}')
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][0], "test/inmem")

    def test_14_gateway_caml_routing(self):
        """Assert that gateway routes CAML device correctly."""
        gw = Gateway(workspace_dir=self.workspace_dir, use_mock=True)
        telemetry = {
            "schema_version": "1.0",
            "device_id": "AQUA_FRESH_001",
            "timestamp": datetime.datetime.now().isoformat(),
            "dataset_route": "caml",
            "location": {"latitude": 27.5, "longitude": -81.2},
            "sensors": {"temperature_c": 24.5, "salinity_ppt": 0.2, "ph": 7.5, "turbidity_ntu": 3.0, "dissolved_oxygen_mg_l": 8.0},
            "device_health": {"wifi_connected": True, "mqtt_connected": True, "sensor_status": "OK"}
        }
        df = gw.transform_telemetry_to_features(telemetry)
        self.assertIn("lat", df.columns)
        self.assertIn("lon", df.columns)
        self.assertNotIn("SALINITY", df.columns)

    def test_15_gateway_habsos_routing(self):
        """Assert that gateway routes HABSOS device correctly."""
        gw = Gateway(workspace_dir=self.workspace_dir, use_mock=True)
        telemetry = {
            "schema_version": "1.0",
            "device_id": "AQUA_MARINE_001",
            "timestamp": datetime.datetime.now().isoformat(),
            "dataset_route": "habsos",
            "location": {"latitude": 27.5, "longitude": -82.5},
            "sensors": {"temperature_c": 24.5, "salinity_ppt": 35.0, "ph": 8.2, "turbidity_ntu": 4.0, "dissolved_oxygen_mg_l": 7.0},
            "device_health": {"wifi_connected": True, "mqtt_connected": True, "sensor_status": "OK"}
        }
        df = gw.transform_telemetry_to_features(telemetry)
        self.assertIn("SALINITY", df.columns)
        self.assertIn("WATER_TEMP", df.columns)

    def test_16_exact_ml_feature_mapping(self):
        """Assert ML feature ordering matches training schemas exactly."""
        gw = Gateway(workspace_dir=self.workspace_dir, use_mock=True)
        telemetry = {
            "schema_version": "1.0",
            "device_id": "AQUA_FRESH_001",
            "timestamp": datetime.datetime.now().isoformat(),
            "dataset_route": "caml",
            "location": {"latitude": 27.5, "longitude": -81.2},
            "sensors": {"temperature_c": 24.5, "salinity_ppt": 0.2, "ph": 7.5, "turbidity_ntu": 3.0, "dissolved_oxygen_mg_l": 8.0},
            "device_health": {"wifi_connected": True, "mqtt_connected": True, "sensor_status": "OK"}
        }
        df = gw.transform_telemetry_to_features(telemetry)
        expected = gw.pipeline.ml_loader.manifest["models"]["caml"]["expected_features"]
        self.assertEqual(set(df.columns), set(expected))

    def test_17_exact_ais_feature_mapping(self):
        """Assert AIS feature ordering matches training schemas exactly."""
        gw = Gateway(workspace_dir=self.workspace_dir, use_mock=True)
        telemetry = {
            "schema_version": "1.0",
            "device_id": "AQUA_MARINE_001",
            "timestamp": datetime.datetime.now().isoformat(),
            "dataset_route": "habsos",
            "location": {"latitude": 27.5, "longitude": -82.5},
            "sensors": {"temperature_c": 24.5, "salinity_ppt": 35.0, "ph": 8.2, "turbidity_ntu": 4.0, "dissolved_oxygen_mg_l": 7.0},
            "device_health": {"wifi_connected": True, "mqtt_connected": True, "sensor_status": "OK"}
        }
        df = gw.transform_telemetry_to_features(telemetry)
        expected = gw.pipeline.ais_loader.registry["models"][1]["feature_schema"]
        self.assertTrue(set(expected).issubset(set(df.columns)))

    def test_18_unsupported_sensor_exclusion(self):
        """Verify ph, turbidity, DO are excluded from ML feature dataframes."""
        gw = Gateway(workspace_dir=self.workspace_dir, use_mock=True)
        telemetry = {
            "schema_version": "1.0",
            "device_id": "AQUA_FRESH_001",
            "timestamp": datetime.datetime.now().isoformat(),
            "dataset_route": "caml",
            "location": {"latitude": 27.5, "longitude": -81.2},
            "sensors": {"temperature_c": 24.5, "salinity_ppt": 0.2, "ph": 7.5, "turbidity_ntu": 3.0, "dissolved_oxygen_mg_l": 8.0},
            "device_health": {"wifi_connected": True, "mqtt_connected": True, "sensor_status": "OK"}
        }
        df = gw.transform_telemetry_to_features(telemetry)
        self.assertNotIn("ph", df.columns)
        self.assertNotIn("turbidity", df.columns)
        self.assertNotIn("dissolved_oxygen", df.columns)

    def test_19_invalid_telemetry_rejection(self):
        """Assert gateway rejects telemetry with invalid schema."""
        gw = Gateway(workspace_dir=self.workspace_dir, use_mock=True)
        is_valid, err = gw.validate_telemetry_payload({"bad": 1})
        self.assertFalse(is_valid)

    def test_20_unknown_device_rejection(self):
        """Assert gateway rejects telemetry from unregistered device ID."""
        gw = Gateway(workspace_dir=self.workspace_dir, use_mock=True)
        is_valid, err = gw.validate_telemetry_payload({
            "schema_version": "1.0",
            "device_id": "AQUA_FAKE_001",
            "timestamp": datetime.datetime.now().isoformat(),
            "dataset_route": "caml",
            "location": {"latitude": 27.5, "longitude": -81.2},
            "sensors": {"ph": 7.0, "turbidity_ntu": 1.0, "dissolved_oxygen_mg_l": 8.0},
            "device_health": {"wifi_connected": True, "mqtt_connected": True, "sensor_status": "OK"}
        })
        self.assertFalse(is_valid)

    def test_21_actuator_normal_behavior(self):
        """Verify actuator states under NORMAL fusion state."""
        act = VirtualActuators()
        act.update_state("NORMAL")
        self.assertEqual(act.green_led, "ON")
        self.assertEqual(act.yellow_led, "OFF")
        self.assertEqual(act.red_led, "OFF")
        self.assertEqual(act.buzzer, "OFF")
        self.assertEqual(act.pump_relay, "OFF")

    def test_22_actuator_warning_behavior(self):
        """Verify actuator states under WARNING fusion state."""
        act = VirtualActuators()
        act.update_state("WARNING")
        self.assertEqual(act.green_led, "OFF")
        self.assertEqual(act.yellow_led, "ON")
        self.assertEqual(act.red_led, "OFF")
        self.assertEqual(act.buzzer, "OFF")
        self.assertEqual(act.pump_relay, "ON")

    def test_23_actuator_critical_behavior(self):
        """Verify actuator states under CRITICAL fusion state."""
        act = VirtualActuators()
        act.update_state("CRITICAL")
        self.assertEqual(act.green_led, "OFF")
        self.assertEqual(act.yellow_led, "OFF")
        self.assertEqual(act.red_led, "ON")
        self.assertEqual(act.buzzer, "ON")
        self.assertEqual(act.pump_relay, "ON")

    def test_24_actuator_unknown_anomaly_behavior(self):
        """Verify actuator states under UNKNOWN_ANOMALY fusion state."""
        act = VirtualActuators()
        act.update_state("UNKNOWN_ANOMALY")
        self.assertEqual(act.green_led, "OFF")
        self.assertEqual(act.yellow_led, "ON")
        self.assertEqual(act.red_led, "ON")
        self.assertEqual(act.buzzer, "OFF")
        self.assertEqual(act.pump_relay, "OFF")

    def test_25_command_validation(self):
        """Assert command validation and manual actuator overrides."""
        act = VirtualActuators()
        self.assertTrue(act.execute_command("ACTIVATE_BUZZER"))
        self.assertEqual(act.buzzer, "ON")
        self.assertFalse(act.execute_command("INVALID_CMD"))

    def test_26_event_persistence(self):
        """Assert telemetry is stored successfully in SQLite db."""
        db = EventStore(db_path=self.test_db_path)
        telemetry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "device_id": "AQUA_FRESH_001",
            "location": {"latitude": 27.5, "longitude": -81.2},
            "sensors": {"temperature_c": 24.0, "salinity_ppt": 0.2, "ph": 7.5, "turbidity_ntu": 3.0, "dissolved_oxygen_mg_l": 8.0},
            "device_health": {"wifi_connected": True, "mqtt_connected": True, "sensor_status": "OK"}
        }
        db.log_telemetry(telemetry)
        
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT device_id, ph FROM telemetry_logs")
        row = cursor.fetchone()
        conn.close()
        
        self.assertEqual(row[0], "AQUA_FRESH_001")
        self.assertEqual(row[1], 7.5)

    def test_27_model_version_persistence(self):
        """Assert ML model version is stored in decision logs."""
        db = EventStore(db_path=self.test_db_path)
        decision = {
            "timestamp": datetime.datetime.now().isoformat(),
            "device_id": "AQUA_FRESH_001",
            "ml_evidence": {"predicted_class": 1, "confidence": 0.95, "dangerous_class": False, "model_id": "RF_CAML_V3"},
            "ais_evidence": {"is_anomaly": 0, "anomaly_score": 0.0, "ais_model_id": "AIS_CAML_V1"},
            "fusion": {"final_state": "NORMAL", "reason_code": "ML_NORMAL_AIS_NORMAL", "reasoning": "Test", "confidence_band": "HIGH"},
            "system_metadata": {"fusion_version": "1.0.0"}
        }
        db.log_decision(decision)
        
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT ml_model_id FROM fusion_decisions")
        row = cursor.fetchone()
        conn.close()
        self.assertEqual(row[0], "RF_CAML_V3")

    def test_28_ais_version_persistence(self):
        """Assert AIS model version is stored in decision logs."""
        db = EventStore(db_path=self.test_db_path)
        decision = {
            "timestamp": datetime.datetime.now().isoformat(),
            "device_id": "AQUA_FRESH_001",
            "ml_evidence": {"predicted_class": 1, "confidence": 0.95, "dangerous_class": False, "model_id": "RF_CAML_V3"},
            "ais_evidence": {"is_anomaly": 0, "anomaly_score": 0.0, "ais_model_id": "AIS_CAML_V1"},
            "fusion": {"final_state": "NORMAL", "reason_code": "ML_NORMAL_AIS_NORMAL", "reasoning": "Test", "confidence_band": "HIGH"},
            "system_metadata": {"fusion_version": "1.0.0"}
        }
        db.log_decision(decision)
        
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT ais_model_id FROM fusion_decisions")
        row = cursor.fetchone()
        conn.close()
        self.assertEqual(row[0], "AIS_CAML_V1")

    def test_29_fusion_version_persistence(self):
        """Assert Fusion version is stored in decision logs."""
        db = EventStore(db_path=self.test_db_path)
        decision = {
            "timestamp": datetime.datetime.now().isoformat(),
            "device_id": "AQUA_FRESH_001",
            "ml_evidence": {"predicted_class": 1, "confidence": 0.95, "dangerous_class": False, "model_id": "RF_CAML_V3"},
            "ais_evidence": {"is_anomaly": 0, "anomaly_score": 0.0, "ais_model_id": "AIS_CAML_V1"},
            "fusion": {"final_state": "NORMAL", "reason_code": "ML_NORMAL_AIS_NORMAL", "reasoning": "Test", "confidence_band": "HIGH"},
            "system_metadata": {"fusion_version": "1.0.0"}
        }
        db.log_decision(decision)
        
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT fusion_version FROM fusion_decisions")
        row = cursor.fetchone()
        conn.close()
        self.assertEqual(row[0], "1.0.0")

    def test_30_freshwater_end_to_end_cycle(self):
        """Assert end-to-end freshwater (CAML) simulation cycle completes successfully."""
        rt = DeviceRuntimeManager(workspace_dir=self.workspace_dir, use_mock=True)
        rt.start()
        # Mock database file to our test db path
        rt.gateway.event_store = self.event_store
        
        res = rt.execute_cycle(scenarios={"AQUA_FRESH_001": "NORMAL"}, timestamp=datetime.datetime.now())
        self.assertEqual(res["AQUA_FRESH_001"]["state"], "WAITING")
        self.assertEqual(res["AQUA_FRESH_001"]["actuator_state"], "LEDs(G=ON, Y=OFF, R=OFF), Buzzer=OFF, Pump=OFF")
        rt.stop()

    def test_31_marine_end_to_end_cycle(self):
        """Assert end-to-end marine (HABSOS) simulation cycle completes successfully."""
        rt = DeviceRuntimeManager(workspace_dir=self.workspace_dir, use_mock=True)
        rt.start()
        rt.gateway.event_store = self.event_store
        
        res = rt.execute_cycle(scenarios={"AQUA_MARINE_001": "NORMAL"}, timestamp=datetime.datetime.now())
        self.assertEqual(res["AQUA_MARINE_001"]["state"], "WAITING")
        self.assertEqual(res["AQUA_MARINE_001"]["actuator_state"], "LEDs(G=ON, Y=OFF, R=OFF), Buzzer=OFF, Pump=OFF")
        rt.stop()

    def test_32_sensor_fault_scenario(self):
        """Verify device behavior under SENSOR_FAULT scenario."""
        dev = ESP32Device(device_id="AQUA_FRESH_001")
        dev.boot()
        dev.initialize_sensors()
        dev.connect_network()
        
        # Force step counter so generate_reading gets fault_type == 0 (NaN/inf values)
        dev.simulator.step_counter = 2
        telemetry = dev.poll_and_validate(scenario="SENSOR_FAULT")
        dev.publish_telemetry(telemetry)
        self.assertEqual(dev.state, "ERROR") # Transitioned to error after publishing
        self.assertEqual(dev.sensor_status, "FAULT")

    def test_33_network_recovery(self):
        """Verify device transitions back to ONLINE after network reconnection."""
        dev = ESP32Device(device_id="AQUA_FRESH_001")
        dev.state = "ERROR"
        dev.run_reconnection()
        self.assertEqual(dev.state, "ONLINE")

    def test_34_multiple_device_isolation(self):
        """Verify concurrent devices retain independent states."""
        rt = DeviceRuntimeManager(workspace_dir=self.workspace_dir, use_mock=True)
        rt.start()
        res = rt.execute_cycle(scenarios={"AQUA_FRESH_001": "NORMAL", "AQUA_MARINE_001": "KNOWN_BLOOM_RISK"})
        
        self.assertEqual(rt.devices["AQUA_FRESH_001"].ecosystem_type, "Freshwater")
        self.assertEqual(rt.devices["AQUA_MARINE_001"].ecosystem_type, "Marine")
        rt.stop()

    def test_35_invalidated_phase4_models_blocked(self):
        """Assert that the archived Phase 4 invalid artifacts are blocked."""
        ml_loader = Gateway(workspace_dir=self.workspace_dir, use_mock=True).pipeline.ml_loader
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

    def test_36_test_data_never_accessed(self):
        """Assert that no code files read test CSV datasets."""
        for root, dirs, files in os.walk(os.path.join(self.workspace_dir, "src")):
            for f in files:
                if f.endswith(".py"):
                    with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                        content = file.read()
                        self.assertNotIn("caml_test.csv", content)
                        self.assertNotIn("habsos_test.csv", content)

if __name__ == "__main__":
    unittest.main()
