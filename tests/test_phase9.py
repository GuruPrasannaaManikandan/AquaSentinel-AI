import unittest
import os
import json
import sqlite3
import datetime
from fastapi.testclient import TestClient

from src.backend.app import app
from src.backend.services import BackendService
from src.iot.event_store import EventStore

class TestPhase9(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.test_db_path = os.path.join(cls.workspace_dir, "models", "fusion", "test_phase9_events.db")
        
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
            
        cls.event_store = EventStore(db_path=cls.test_db_path)
        cls.service = BackendService.get_instance(workspace_dir=cls.workspace_dir)
        cls.service.event_store = cls.event_store
        cls.service.runtime.gateway.event_store = cls.event_store
        
        # Start runtime to hook clients
        cls.service.runtime.start()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.service.runtime.stop()
        BackendService.reset_instance()
        from src.iot.mqtt_client import InMemoryMQTTBroker
        InMemoryMQTTBroker.reset_instance()
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

    def setUp(self):
        self.service.runtime.start()

    def test_1_release_manifest_validity(self):
        """Assert release manifest exists and contains valid JSON."""
        manifest_path = os.path.join(self.workspace_dir, "config", "release_manifest.json")
        self.assertTrue(os.path.exists(manifest_path))
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["release_version"], "1.0.0")

    def test_2_final_metric_source_validity(self):
        """Assert final verified metrics JSON exists and has correct format."""
        metrics_path = os.path.join(self.workspace_dir, "reports", "phase9", "final_verified_metrics.json")
        self.assertTrue(os.path.exists(metrics_path))
        with open(metrics_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertIn("models", data)

    def test_3_active_ml_artifacts_load(self):
        """Verify deployed ML models load successfully."""
        ml_loader = self.service.runtime.gateway.pipeline.ml_loader
        caml_model = ml_loader.load_model("caml")
        self.assertIsNotNone(caml_model)
        habsos_model = ml_loader.load_model("habsos")
        self.assertIsNotNone(habsos_model)

    def test_4_active_ais_artifacts_load(self):
        """Verify deployed AIS models load successfully."""
        ais_loader = self.service.runtime.gateway.pipeline.ais_loader
        caml_nsa = ais_loader.load_model("caml")
        self.assertIsNotNone(caml_nsa)
        habsos_nsa = ais_loader.load_model("habsos")
        self.assertIsNotNone(habsos_nsa)

    def test_5_fusion_policy_loads(self):
        """Assert that fusion policy JSON config loads cleanly."""
        policy_path = os.path.join(self.workspace_dir, "config", "fusion_policy.json")
        self.assertTrue(os.path.exists(policy_path))
        with open(policy_path, "r", encoding="utf-8") as f:
            policy = json.load(f)
            self.assertIn("confidence_thresholds", policy)

    def test_6_device_registry_loads(self):
        """Assert that device registry config loads cleanly."""
        reg_path = os.path.join(self.workspace_dir, "config", "device_registry.json")
        self.assertTrue(os.path.exists(reg_path))
        with open(reg_path, "r", encoding="utf-8") as f:
            reg = json.load(f)
            self.assertIn("devices", reg)

    def test_7_sensor_mapping_loads(self):
        """Assert that sensor-feature mapping configuration loads cleanly."""
        map_path = os.path.join(self.workspace_dir, "config", "sensor_feature_mapping.json")
        self.assertTrue(os.path.exists(map_path))
        with open(map_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)
            self.assertIn("mappings", mapping)
            self.assertIn("gps_latitude", mapping["mappings"])
            self.assertIn("water_temp", mapping["mappings"])

    def test_8_fastapi_loads(self):
        """Verify FastAPI app is initialized and starts."""
        self.assertIsNotNone(app)
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)

    def test_9_dashboard_module_loads(self):
        """Verify Streamlit dashboard file is present."""
        dash_path = os.path.join(self.workspace_dir, "dashboard", "app.py")
        self.assertTrue(os.path.exists(dash_path))

    def test_10_sqlite_schema_exists(self):
        """Verify event store database schemas exist."""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        conn.close()
        self.assertIn("telemetry_logs", tables)
        self.assertIn("fusion_decisions", tables)

    def test_11_freshwater_e2e_cycle(self):
        """Verify full loop execution on the Freshwater device node."""
        self.service.set_scenario("AQUA_FRESH_001", "NORMAL")
        res = self.service.run_single_cycle()
        self.assertIn("AQUA_FRESH_001", res)
        # Check logged
        dec = self.event_store.get_latest_decision("AQUA_FRESH_001")
        self.assertIsNotNone(dec)

    def test_12_marine_e2e_cycle(self):
        """Verify full loop execution on the Marine device node."""
        self.service.set_scenario("AQUA_MARINE_001", "NORMAL")
        res = self.service.run_single_cycle()
        self.assertIn("AQUA_MARINE_001", res)
        # Check logged
        dec = self.event_store.get_latest_decision("AQUA_MARINE_001")
        self.assertIsNotNone(dec)

    def test_13_sensor_fault_handling(self):
        """Verify edge validator fault detection and gateway bypass."""
        self.service.set_scenario("AQUA_FRESH_001", "SENSOR_FAULT")
        # Force step counter so generate_reading gets fault_type == 0 (NaN/inf values)
        self.service.runtime.devices["AQUA_FRESH_001"].simulator.step_counter = 2
        self.service.run_single_cycle()
        dec = self.event_store.get_latest_decision("AQUA_FRESH_001")
        self.assertEqual(dec["final_state"], "SENSOR_FAULT")
        self.assertEqual(dec["reason_code"], "SENSOR_FAULT_BYPASS")

    def test_14_network_recovery(self):
        """Verify FSM disconnect and recover routines."""
        dev = self.service.runtime.devices["AQUA_FRESH_001"]
        dev.client.disconnect()
        dev.state = "ERROR" # Simulate transitioned network error state
        self.assertEqual(dev.state, "ERROR")
        dev.run_reconnection()
        self.assertEqual(dev.state, "ONLINE")

    def test_15_invalid_model_blocked(self):
        """Assert gateway model loader blocks invalid models."""
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

    def test_16_invalid_ais_artifact_blocked(self):
        """Assert gateway AIS loader blocks invalid AIS models."""
        ais_loader = self.service.runtime.gateway.pipeline.ais_loader
        original_registry_models = ais_loader.registry["models"]
        try:
            ais_loader.registry["models"] = [
                {
                    "model_id": "invalid_caml",
                    "dataset": "caml_p4_invalid",
                    "status": "INVALIDATED",
                    "audit_status": "FAILED_PHASE45_INTEGRITY_AUDIT",
                    "artifact_path": "models/archive/phase4_invalid/caml_nsa_invalid.joblib"
                }
            ]
            with self.assertRaises(PermissionError):
                ais_loader.load_model("invalid_caml")
        finally:
            ais_loader.registry["models"] = original_registry_models

    def test_17_phase4_artifacts_remain_inactive(self):
        """Assert that no Phase 4 model is in the deployment manifest."""
        manifest_path = os.path.join(self.workspace_dir, "models", "deployment", "model_manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            for key, val in manifest["models"].items():
                self.assertNotIn("phase4", val["artifact_path"])

    def test_18_no_test_dataset_accessed_by_runtime(self):
        """Verify test CSV files are not loaded by active code modules."""
        for root, dirs, files in os.walk(os.path.join(self.workspace_dir, "src")):
            for f in files:
                if f.endswith(".py"):
                    with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                        content = file.read()
                        self.assertNotIn("caml_test.csv", content)
                        self.assertNotIn("habsos_test.csv", content)

    def test_19_final_demo_scenarios_reproducible(self):
        """Assert demo configurations contain the required six scenarios."""
        demo_path = os.path.join(self.workspace_dir, "config", "final_demo_scenarios.json")
        self.assertTrue(os.path.exists(demo_path))
        with open(demo_path, "r", encoding="utf-8") as f:
            scenarios = json.load(f)["scenarios"]
            self.assertEqual(len(scenarios), 6)

    def test_20_final_output_json_serializable(self):
        """Verify that telemetry and decision queries return JSON serializable values."""
        telemetry = self.event_store.get_latest_telemetry("AQUA_FRESH_001")
        self.assertIsNotNone(json.dumps(telemetry))

    def test_21_metric_source_matches_active_lineage(self):
        """Verify locked metrics match champion baseline accuracies."""
        metrics_path = os.path.join(self.workspace_dir, "reports", "phase9", "final_verified_metrics.json")
        with open(metrics_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["models"]["caml"]["validation_metrics"]["accuracy"], 0.6323)
            self.assertEqual(data["models"]["habsos"]["validation_metrics"]["accuracy"], 0.6758)

    def test_22_release_manifest_versions_resolve(self):
        """Verify release manifest contains active model names."""
        manifest_path = os.path.join(self.workspace_dir, "config", "release_manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["active_ml_models"]["caml"], "caml_phase3_champion")

    def test_23_no_critical_active_path_missing(self):
        """Assert active source files are present."""
        path = os.path.join(self.workspace_dir, "src", "backend", "app.py")
        self.assertTrue(os.path.exists(path))

    def test_24_full_system_starts_and_stops_cleanly(self):
        """Assert background simulation loops start and stop successfully."""
        started = self.service.start_simulation()
        self.assertTrue(started or self.service.simulation_active)
        stopped = self.service.stop_simulation()
        self.assertTrue(stopped or not self.service.simulation_active)

    def test_25_sensor_fault_regression_validation_and_fsm(self):
        """Verify sensor fault produces invalid telemetry, edge validation detects it, and FSM enters ERROR state."""
        dev = self.service.runtime.devices["AQUA_MARINE_001"]
        # Force missing sensors (step_counter = 4 -> fault_type = 2 None values)
        dev.simulator.step_counter = 4
        telemetry = dev.poll_and_validate(scenario="SENSOR_FAULT")
        
        # 1. Telemetry is invalid
        self.assertIsNone(telemetry["sensors"]["temperature_c"])
        self.assertIsNone(telemetry["sensors"]["salinity_ppt"])
        
        # 2. Edge validation detects it (sensor_status = FAULT)
        self.assertEqual(telemetry["device_health"]["sensor_status"], "FAULT")
        
        # 3. FSM enters correct ERROR state
        dev.publish_telemetry(telemetry)
        self.assertEqual(dev.state, "ERROR")
        
        # Recover device state
        dev.state = "ONLINE"
        dev.sensor_status = "OK"

    def test_26_sensor_fault_regression_intelligence_and_fusion(self):
        """Verify ML/AIS do not emit misleading predictions and Fusion resolves to SENSOR_FAULT."""
        self.service.set_scenario("AQUA_MARINE_001", "SENSOR_FAULT")
        self.service.runtime.devices["AQUA_MARINE_001"].simulator.step_counter = 4
        self.service.run_single_cycle()
        
        dec = self.event_store.get_latest_decision("AQUA_MARINE_001")
        # 4. ML does not emit a misleading valid prediction (is UNAVAILABLE)
        self.assertEqual(dec["ml_predicted_class"], "UNAVAILABLE")
        # 5. AIS does not emit a misleading SELF result (is UNAVAILABLE)
        self.assertEqual(dec["ais_model_id"], "UNAVAILABLE")
        # 6. Fusion does not emit NORMAL (resolves to SENSOR_FAULT)
        self.assertEqual(dec["final_state"], "SENSOR_FAULT")
        self.assertEqual(dec["reason_code"], "SENSOR_FAULT_BYPASS")

    def test_27_sensor_fault_regression_persistence_and_api(self):
        """Verify that sensor fault cycles are persisted and API response is correct."""
        self.service.set_scenario("AQUA_MARINE_001", "SENSOR_FAULT")
        self.service.runtime.devices["AQUA_MARINE_001"].simulator.step_counter = 4
        self.service.run_single_cycle()
        
        # 7. Database persistence is correct
        dec = self.event_store.get_latest_decision("AQUA_MARINE_001")
        self.assertIsNotNone(dec)
        
        # 8. API response is correct
        r = self.client.get("/devices/AQUA_MARINE_001/latest")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["decision"]["final_state"], "SENSOR_FAULT")
        self.assertEqual(data["decision"]["ml_predicted_class"], "UNAVAILABLE")

    def test_28_normal_and_bloom_behavior_unchanged(self):
        """Verify that NORMAL and KNOWN_BLOOM_RISK behaviors remain correct and unchanged on both routes."""
        # 10. NORMAL behavior remains unchanged (Freshwater)
        self.service.set_scenario("AQUA_FRESH_001", "NORMAL")
        self.service.run_single_cycle()
        dec = self.event_store.get_latest_decision("AQUA_FRESH_001")
        self.assertEqual(dec["final_state"], "NORMAL")
        
        # 11. KNOWN_BLOOM_RISK behavior remains unchanged (Freshwater)
        self.service.set_scenario("AQUA_FRESH_001", "KNOWN_BLOOM_RISK")
        self.service.run_single_cycle()
        dec = self.event_store.get_latest_decision("AQUA_FRESH_001")
        self.assertEqual(dec["final_state"], "WARNING")
        
        # 12. Freshwater NORMAL -> WARNING -> NORMAL recovery still passes
        self.service.set_scenario("AQUA_FRESH_001", "NORMAL")
        self.service.run_single_cycle()
        dec = self.event_store.get_latest_decision("AQUA_FRESH_001")
        self.assertEqual(dec["final_state"], "NORMAL")
        
        # 13. Marine NORMAL -> WARNING -> NORMAL recovery still passes
        self.service.set_scenario("AQUA_MARINE_001", "NORMAL")
        self.service.run_single_cycle()
        dec = self.event_store.get_latest_decision("AQUA_MARINE_001")
        self.assertEqual(dec["final_state"], "NORMAL")
        
        self.service.set_scenario("AQUA_MARINE_001", "KNOWN_BLOOM_RISK")
        self.service.run_single_cycle()
        dec = self.event_store.get_latest_decision("AQUA_MARINE_001")
        self.assertEqual(dec["final_state"], "WARNING")
        
        self.service.set_scenario("AQUA_MARINE_001", "NORMAL")
        self.service.run_single_cycle()
        dec = self.event_store.get_latest_decision("AQUA_MARINE_001")
        self.assertEqual(dec["final_state"], "NORMAL")

    def test_29_marine_bloom_provenance_and_feature_mapping(self):
        """Verify HABSOS Row 964 provenance, feature mapping, and runtime execution."""
        # 1. Start cycle under KNOWN_BLOOM_RISK
        self.service.set_scenario("AQUA_MARINE_001", "KNOWN_BLOOM_RISK")
        self.service.run_single_cycle()
        
        tel = self.event_store.get_latest_telemetry("AQUA_MARINE_001")
        dec = self.event_store.get_latest_decision("AQUA_MARINE_001")
        
        # 2. Check provenance values in telemetry
        self.assertEqual(tel["latitude"], 24.66587)
        self.assertEqual(tel["longitude"], -81.36588)
        self.assertEqual(tel["temperature_c"], 23.0)
        self.assertEqual(tel["salinity_ppt"], 31.9)
        self.assertEqual(tel["provenance_timestamp"], "2023-12-18T12:00:00")
        
        # Verify operational timestamp is close to now
        op_time = datetime.datetime.fromisoformat(tel["timestamp"])
        now = datetime.datetime.now()
        self.assertTrue(abs((now - op_time).total_seconds()) < 60.0)
        
        # 3. Check model inference output & fusion state
        self.assertEqual(dec["ml_predicted_class"], "warning")
        self.assertEqual(dec["ais_model_id"], "NSA-HABSOS-v1")
        self.assertEqual(dec["final_state"], "WARNING")
        self.assertEqual(dec["reason_code"], "ML_LOW_CONFIDENCE")

    def test_30_dual_timestamp_contract(self):
        """Verify that every cycle has one operational timestamp that correlates all tables."""
        self.service.set_scenario("AQUA_FRESH_001", "NORMAL")
        self.service.run_single_cycle()
        
        tel = self.event_store.get_latest_telemetry("AQUA_FRESH_001")
        dec = self.event_store.get_latest_decision("AQUA_FRESH_001")
        act = self.event_store.get_actuators_by_timestamp("AQUA_FRESH_001", tel["timestamp"])
        
        # Telemetry, Decision, and Actuator must have the exact same operational timestamp
        self.assertIsNotNone(tel)
        self.assertIsNotNone(dec)
        self.assertIsNotNone(act)
        self.assertEqual(tel["timestamp"], dec["timestamp"])
        self.assertEqual(tel["timestamp"], act["timestamp"])
        
        # Provenance timestamp must be the historical date
        self.assertEqual(tel["provenance_timestamp"], "2021-04-28T12:00:00")
        
        # Gateway must derive ML features from the provenance timestamp
        gateway = self.service.runtime.gateway
        tel_payload = self.service.runtime.devices["AQUA_FRESH_001"].published_telemetry[-1]
        features = gateway.transform_telemetry_to_features(tel_payload)
        self.assertEqual(features.loc[0, "Year"], 2021)
        self.assertEqual(features.loc[0, "Season"], "Spring")

    def test_31_temporal_provenance_scenarios(self):
        """Verify all dataset-backed scenarios preserve the exact scientific temporal context."""
        # 1. Freshwater KNOWN_BLOOM_RISK
        self.service.set_scenario("AQUA_FRESH_001", "KNOWN_BLOOM_RISK")
        self.service.run_single_cycle()
        tel = self.event_store.get_latest_telemetry("AQUA_FRESH_001")
        self.assertEqual(tel["provenance_timestamp"], "2021-07-14T12:00:00")
        tel_payload = self.service.runtime.devices["AQUA_FRESH_001"].published_telemetry[-1]
        features = self.service.runtime.gateway.transform_telemetry_to_features(tel_payload)
        self.assertEqual(features.loc[0, "Year"], 2021)
        self.assertEqual(features.loc[0, "Season"], "Summer")
        
        # 2. Marine NORMAL
        self.service.set_scenario("AQUA_MARINE_001", "NORMAL")
        self.service.run_single_cycle()
        tel = self.event_store.get_latest_telemetry("AQUA_MARINE_001")
        self.assertEqual(tel["provenance_timestamp"], "1993-01-20T12:00:00")
        tel_payload = self.service.runtime.devices["AQUA_MARINE_001"].published_telemetry[-1]
        features = self.service.runtime.gateway.transform_telemetry_to_features(tel_payload)
        self.assertEqual(features.loc[0, "Year"], 1993)
        self.assertEqual(features.loc[0, "Season"], "Winter")
        
        # 3. Marine KNOWN_BLOOM_RISK
        self.service.set_scenario("AQUA_MARINE_001", "KNOWN_BLOOM_RISK")
        self.service.run_single_cycle()
        tel = self.event_store.get_latest_telemetry("AQUA_MARINE_001")
        self.assertEqual(tel["provenance_timestamp"], "2023-12-18T12:00:00")
        tel_payload = self.service.runtime.devices["AQUA_MARINE_001"].published_telemetry[-1]
        features = self.service.runtime.gateway.transform_telemetry_to_features(tel_payload)
        self.assertEqual(features.loc[0, "Year"], 2023)
        self.assertEqual(features.loc[0, "Season"], "Winter")

    def test_32_chronological_ordering_and_trends(self):
        """Verify scenario switching creates monotonically ordered operational events and doesn't reorder them."""
        # Run sequence
        seq = ["NORMAL", "KNOWN_BLOOM_RISK", "NORMAL", "SENSOR_FAULT", "NORMAL"]
        timestamps = []
        
        for scenario in seq:
            self.service.set_scenario("AQUA_MARINE_001", scenario)
            # Force step counter for SENSOR_FAULT to trigger FAULT state
            if scenario == "SENSOR_FAULT":
                self.service.runtime.devices["AQUA_MARINE_001"].simulator.step_counter = 2
            self.service.run_single_cycle()
            tel = self.event_store.get_latest_telemetry("AQUA_MARINE_001")
            timestamps.append(tel["timestamp"])
            
        # Verify operational timestamps are strictly monotonic / increasing
        for i in range(len(timestamps) - 1):
            t1 = datetime.datetime.fromisoformat(timestamps[i])
            t2 = datetime.datetime.fromisoformat(timestamps[i+1])
            self.assertTrue(t2 >= t1)
            
        # Verify SENSOR_FAULT and recovery actuator states correlate correctly
        # The 4th cycle was SENSOR_FAULT. Check its actuator status.
        db_telemetries = self.event_store.get_historical_telemetry("AQUA_MARINE_001")
        last_5 = db_telemetries[-5:]
        self.assertEqual(last_5[3]["sensor_status"], "FAULT")
        dec = self.event_store.get_decision_by_timestamp("AQUA_MARINE_001", last_5[3]["timestamp"])
        self.assertEqual(dec["final_state"], "SENSOR_FAULT")
        self.assertEqual(dec["reason_code"], "SENSOR_FAULT_BYPASS")
        
        act = self.event_store.get_actuators_by_timestamp("AQUA_MARINE_001", last_5[3]["timestamp"])
        self.assertIn("G=OFF", act["summary"])
        self.assertIn("Y=ON", act["summary"])
        self.assertIn("R=ON", act["summary"])
        self.assertIn("Buzzer=ON", act["summary"])
        self.assertIn("Pump=OFF", act["summary"])
        
        # The 5th cycle is recovery back to NORMAL
        self.assertEqual(last_5[4]["sensor_status"], "OK")
        dec5 = self.event_store.get_decision_by_timestamp("AQUA_MARINE_001", last_5[4]["timestamp"])
        self.assertEqual(dec5["final_state"], "NORMAL")
        act5 = self.event_store.get_actuators_by_timestamp("AQUA_MARINE_001", last_5[4]["timestamp"])
        self.assertIn("G=ON", act5["summary"])
        self.assertIn("Y=OFF", act5["summary"])
        self.assertIn("R=OFF", act5["summary"])
        self.assertIn("Buzzer=OFF", act5["summary"])
        self.assertIn("Pump=OFF", act5["summary"])

    def test_33_alert_policy_and_acknowledgement(self):
        """Verify alert policy, duplicate suppression, state transition checks, and acknowledgement flow."""
        import time
        # Clear database to isolate test_33
        conn = sqlite3.connect(self.test_db_path)
        c = conn.cursor()
        c.execute("DELETE FROM alerts")
        c.execute("DELETE FROM fusion_decisions")
        c.execute("DELETE FROM telemetry_logs")
        conn.commit()
        conn.close()
        
        initial_alerts = self.event_store.get_alerts("AQUA_FRESH_001")
        
        # 2. Trigger NORMAL -> no warning alert should exist
        self.service.set_scenario("AQUA_FRESH_001", "NORMAL")
        self.service.run_single_cycle()
        
        alerts_n = self.event_store.get_alerts("AQUA_FRESH_001")
        self.assertEqual(len(alerts_n), len(initial_alerts))
        
        # 3. Transition to KNOWN_BLOOM_RISK -> should trigger alert
        self.service.set_scenario("AQUA_FRESH_001", "KNOWN_BLOOM_RISK")
        self.service.run_single_cycle()
        
        alerts_bloom1 = self.event_store.get_alerts("AQUA_FRESH_001")
        self.assertEqual(len(alerts_bloom1), len(alerts_n) + 1)
        new_alert = alerts_bloom1[0]
        self.assertEqual(new_alert["severity"], "MEDIUM")
        self.assertEqual(new_alert["acknowledged"], 0)
        self.assertEqual(new_alert["device_id"], "AQUA_FRESH_001")
        
        # 4. Repeat KNOWN_BLOOM_RISK -> should suppress duplicates
        self.service.run_single_cycle()
        alerts_bloom2 = self.event_store.get_alerts("AQUA_FRESH_001")
        self.assertEqual(len(alerts_bloom2), len(alerts_bloom1)) # suppressed!
        
        # 5. Transition to SENSOR_FAULT -> should trigger sensor fault alert
        self.service.set_scenario("AQUA_FRESH_001", "SENSOR_FAULT")
        self.service.runtime.devices["AQUA_FRESH_001"].simulator.step_counter = 2
        self.service.run_single_cycle()
        
        alerts_fault1 = self.event_store.get_alerts("AQUA_FRESH_001")
        self.assertEqual(len(alerts_fault1), len(alerts_bloom2) + 1)
        fault_alert = alerts_fault1[0]
        self.assertEqual(fault_alert["severity"], "HIGH")
        self.assertEqual(fault_alert["reason_code"], "SENSOR_FAULT_ALERT")
        
        # 6. Repeat SENSOR_FAULT -> should suppress duplicates
        self.service.run_single_cycle()
        alerts_fault2 = self.event_store.get_alerts("AQUA_FRESH_001")
        self.assertEqual(len(alerts_fault2), len(alerts_fault1)) # suppressed!
        
        # 7. Test Acknowledgement
        alert_id = new_alert["id"]
        # Unacknowledged lists
        unack = self.event_store.get_alerts("AQUA_FRESH_001", acknowledged=False)
        self.assertTrue(any(a["id"] == alert_id for a in unack))
        
        # Acknowledge
        self.event_store.acknowledge_alert(alert_id)
        
        # Verify acknowledged in database
        unack_post = self.event_store.get_alerts("AQUA_FRESH_001", acknowledged=False)
        self.assertFalse(any(a["id"] == alert_id for a in unack_post))
        
        ack_post = self.event_store.get_alerts("AQUA_FRESH_001", acknowledged=True)
        self.assertTrue(any(a["id"] == alert_id for a in ack_post))
        
        # Safe re-acknowledgement
        self.event_store.acknowledge_alert(alert_id)
        
        # Safe invalid ID
        self.event_store.acknowledge_alert(-999)

    def test_34_background_simulation_concurrency_and_lifecycle(self):
        """Verify thread safety, duplicate prevention, and clean stop/restart lifecycle."""
        # Ensure simulation is stopped initially
        self.service.stop_simulation()
        
        # Start simulation
        started_1 = self.service.start_simulation()
        self.assertTrue(started_1)
        self.assertTrue(self.service.simulation_active)
        self.assertTrue(self.service.simulation_thread.is_alive())
        
        thread_1 = self.service.simulation_thread
        
        # Start simulation again -> should be rejected and not spawn duplicate thread
        started_2 = self.service.start_simulation()
        self.assertFalse(started_2)
        self.assertEqual(self.service.simulation_thread, thread_1)
        
        # Verify single-step is rejected while simulation is running
        with self.assertRaises(ValueError):
            self.service.run_single_cycle()
            
        # Stop simulation -> should terminate thread cleanly
        stopped = self.service.stop_simulation()
        self.assertTrue(stopped)
        self.assertFalse(self.service.simulation_active)
        
        # Wait up to 3 seconds for thread to join
        thread_1.join(timeout=3.0)
        self.assertFalse(thread_1.is_alive())
        
        # Restart simulation -> should spawn a fresh thread and work correctly
        started_3 = self.service.start_simulation()
        self.assertTrue(started_3)
        self.assertTrue(self.service.simulation_active)
        self.assertTrue(self.service.simulation_thread.is_alive())
        self.assertNotEqual(self.service.simulation_thread, thread_1)
        
        # Cleanup
        self.service.stop_simulation()

    def test_35_singleton_state_leakage_and_event_store_replacement(self):
        """Verify singleton instance reset and dynamic propagation of replacement EventStores."""
        # Create a new custom temporary EventStore
        import tempfile
        temp_db_fd, temp_db_path = tempfile.mkstemp()
        os.close(temp_db_fd)
        
        try:
            custom_store = EventStore(db_path=temp_db_path)
            
            # Replace the service event store
            self.service.event_store = custom_store
            
            # Verify self.service.event_store updated
            self.assertEqual(self.service.event_store, custom_store)
            
            # Verify gateway event_store automatically updated via setter
            self.assertEqual(self.service.runtime.gateway.event_store, custom_store)
            
            # Reset instance and verify it cleared
            BackendService.reset_instance()
            self.assertIsNone(BackendService._instance)
            
        finally:
            if os.path.exists(temp_db_path):
                try:
                    os.remove(temp_db_path)
                except OSError:
                    pass
            
            # Restore original test event store for subsequent tests
            # Re-get fresh BackendService instance
            BackendService.reset_instance()
            new_service = BackendService.get_instance(workspace_dir=self.workspace_dir)
            new_service.event_store = self.event_store
            new_service.runtime.gateway.event_store = self.event_store

    def test_36_fusion_dynamic_ais_reliability(self):
        """Verify that Fusion Engine dynamically respects the configured ais_reliable policy."""
        fusion_engine = self.service.runtime.gateway.pipeline.fusion_engine
        
        # Capture original policy
        original_policy = json.loads(json.dumps(fusion_engine.policy))
        
        try:
            # 1. Contradiction input payload
            ml_evidence = {
                "dataset": "caml",
                "predicted_class": 1,
                "class_probabilities": {"1": 0.9, "2": 0.05, "3": 0.05, "4": 0.0, "5": 0.0},
                "confidence": 0.9,
                "dangerous_class": False,
                "model_id": "test_model-v1.0.0"
            }
            ais_evidence = {
                "dataset": "caml",
                "is_anomaly": True,
                "anomaly_score": 0.8,
                "matched_detector_count": 5,
                "nearest_detector_distance": 0.1,
                "ais_model_id": "test_ais-v1.0"
            }
            
            # Default policy: CAML AIS is reliable (ais_reliable = True)
            # Expected fusion: UNKNOWN_ANOMALY
            res_default = fusion_engine.fuse(ml_evidence, ais_evidence)
            self.assertEqual(res_default["fusion"]["final_state"], "UNKNOWN_ANOMALY")
            self.assertEqual(res_default["fusion"]["reason_code"], "ML_NORMAL_AIS_ANOMALY")
            
            # 2. Modify policy: set CAML ais_reliable = False
            fusion_engine.policy["dataset_reliability"]["caml"]["ais_reliable"] = False
            
            # Expected fusion: NORMAL, HABSOS_AIS_LIMITED_RELIABILITY (disregard anomaly)
            res_modified = fusion_engine.fuse(ml_evidence, ais_evidence)
            self.assertEqual(res_modified["fusion"]["final_state"], "NORMAL")
            self.assertEqual(res_modified["fusion"]["reason_code"], "HABSOS_AIS_LIMITED_RELIABILITY")
            
        finally:
            # Restore original policy
            fusion_engine.policy = original_policy

if __name__ == "__main__":
    unittest.main()
