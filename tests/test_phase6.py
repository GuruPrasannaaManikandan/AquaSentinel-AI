import unittest
import os
import json
import pandas as pd
import numpy as np
from src.models.deployment_loader import DeploymentModelLoader
from src.ais.ais_loader import AISLoader
from src.fusion.fusion_engine import FusionEngine
from src.fusion.decision_pipeline import DecisionPipeline

class TestPhase6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.policy_path = os.path.join(cls.workspace_dir, "config", "fusion_policy.json")
        cls.registry_path = os.path.join(cls.workspace_dir, "models", "fusion", "fusion_registry.json")
        
        cls.engine = FusionEngine(cls.policy_path)
        cls.pipeline = DecisionPipeline(cls.workspace_dir)

    def test_1_active_ml_models_load(self):
        """Assert that active ML deployment models are loadable."""
        self.assertIsNotNone(self.pipeline.ml_loader.load_model("caml"))
        self.assertIsNotNone(self.pipeline.ml_loader.load_model("habsos"))

    def test_2_active_ais_models_load(self):
        """Assert that active AIS Negative Selection models are loadable."""
        self.assertIsNotNone(self.pipeline.ais_loader.load_model("caml"))
        self.assertIsNotNone(self.pipeline.ais_loader.load_model("habsos"))

    def test_3_invalid_phase4_models_remain_blocked(self):
        """Assert that invalidated Phase 4 models remain blocked from loading."""
        ml_loader = self.pipeline.ml_loader
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

    def test_4_fusion_policy_loads(self):
        """Assert that the fusion policy config file loads successfully and contains expected keys."""
        self.assertTrue(os.path.exists(self.policy_path))
        with open(self.policy_path, "r", encoding="utf-8") as f:
            policy = json.load(f)
        self.assertIn("fusion_version", policy)
        self.assertIn("confidence_thresholds", policy)
        self.assertIn("dangerous_classes", policy)
        self.assertIn("dataset_reliability", policy)

    def test_5_fusion_registry_loads(self):
        """Assert that the fusion registry metadata loads and contains expected attributes."""
        self.assertTrue(os.path.exists(self.registry_path))
        with open(self.registry_path, "r", encoding="utf-8") as f:
            reg = json.load(f)
        self.assertEqual(reg["fusion_id"], "fusion_nsa_ml_v1")
        self.assertEqual(reg["status"], "DEPLOYED")

    def test_6_dataset_mismatch_rejected(self):
        """Assert that passing mismatched datasets raises ValueError."""
        ml = {"dataset": "caml", "predicted_class": 1, "class_probabilities": {1: 1.0}, "confidence": 1.0, "dangerous_class": False, "model_id": "M1"}
        ais = {"dataset": "habsos", "is_anomaly": False, "anomaly_score": 0.0, "matched_detector_count": 0, "nearest_detector_distance": 0.5, "ais_model_id": "A1"}
        with self.assertRaises(ValueError):
            self.engine.fuse(ml, ais)

    def test_7_missing_ml_fields_rejected(self):
        """Assert that missing required ML fields raises ValueError."""
        ml = {"dataset": "caml", "predicted_class": 1} # missing confidence, etc.
        ais = {"dataset": "caml", "is_anomaly": False, "anomaly_score": 0.0, "matched_detector_count": 0, "nearest_detector_distance": 0.5, "ais_model_id": "A1"}
        with self.assertRaises(ValueError):
            self.engine.fuse(ml, ais)

    def test_8_missing_ais_fields_rejected(self):
        """Assert that missing required AIS fields raises ValueError."""
        ml = {"dataset": "caml", "predicted_class": 1, "class_probabilities": {1: 1.0}, "confidence": 1.0, "dangerous_class": False, "model_id": "M1"}
        ais = {"dataset": "caml", "is_anomaly": False} # missing score, etc.
        with self.assertRaises(ValueError):
            self.engine.fuse(ml, ais)

    def test_9_invalid_probabilities_rejected(self):
        """Assert that invalid type for class probabilities raises TypeError."""
        ml = {"dataset": "caml", "predicted_class": 1, "class_probabilities": [1.0], "confidence": 1.0, "dangerous_class": False, "model_id": "M1"}
        ais = {"dataset": "caml", "is_anomaly": False, "anomaly_score": 0.0, "matched_detector_count": 0, "nearest_detector_distance": 0.5, "ais_model_id": "A1"}
        with self.assertRaises(TypeError):
            self.engine.fuse(ml, ais)

    def test_10_invalid_anomaly_score_rejected(self):
        """Assert that invalid range for anomaly_score raises ValueError."""
        ml = {"dataset": "caml", "predicted_class": 1, "class_probabilities": {1: 1.0}, "confidence": 1.0, "dangerous_class": False, "model_id": "M1"}
        ais = {"dataset": "caml", "is_anomaly": False, "anomaly_score": 5.0, "matched_detector_count": 0, "nearest_detector_distance": 0.5, "ais_model_id": "A1"}
        with self.assertRaises(ValueError):
            self.engine.fuse(ml, ais)

    def test_11_all_decision_table_branches_execute(self):
        """Verify decision logic execution for core table conditions."""
        # Case ML Normal + AIS Normal
        ml1 = {"dataset": "caml", "predicted_class": 1, "class_probabilities": {1: 0.9}, "confidence": 0.9, "dangerous_class": False, "model_id": "M1"}
        ais1 = {"dataset": "caml", "is_anomaly": False, "anomaly_score": 0.0, "matched_detector_count": 0, "nearest_detector_distance": 0.8, "ais_model_id": "A1"}
        res1 = self.engine.fuse(ml1, ais1)
        self.assertEqual(res1["fusion"]["final_state"], "NORMAL")
        self.assertEqual(res1["fusion"]["reason_code"], "ML_NORMAL_AIS_NORMAL")

        # Case ML suspect dangerous (critical/warning)
        ml2 = {"dataset": "caml", "predicted_class": 4, "class_probabilities": {1: 0.1, 4: 0.9}, "confidence": 0.9, "dangerous_class": True, "model_id": "M1"}
        res2 = self.engine.fuse(ml2, ais1)
        self.assertEqual(res2["fusion"]["final_state"], "WARNING")
        self.assertEqual(res2["fusion"]["reason_code"], "ML_DANGEROUS")

    def test_12_caml_ais_reliability_policy_applied(self):
        """Assert that CAML normal prediction with AIS anomaly is escalated to UNKNOWN_ANOMALY."""
        ml = {"dataset": "caml", "predicted_class": 1, "class_probabilities": {1: 0.75}, "confidence": 0.75, "dangerous_class": False, "model_id": "M1"}
        ais = {"dataset": "caml", "is_anomaly": True, "anomaly_score": 0.25, "matched_detector_count": 5, "nearest_detector_distance": 0.4, "ais_model_id": "A1"}
        res = self.engine.fuse(ml, ais)
        self.assertEqual(res["fusion"]["final_state"], "UNKNOWN_ANOMALY")
        self.assertEqual(res["fusion"]["reason_code"], "ML_NORMAL_AIS_ANOMALY")

    def test_13_habsos_ais_limitation_applied(self):
        """Assert HABSOS normal prediction with AIS anomaly remains NORMAL due to limited validation reliability."""
        ml = {"dataset": "habsos", "predicted_class": "normal", "class_probabilities": {"normal": 0.8}, "confidence": 0.8, "dangerous_class": False, "model_id": "M2"}
        ais = {"dataset": "habsos", "is_anomaly": True, "anomaly_score": 0.45, "matched_detector_count": 10, "nearest_detector_distance": 0.15, "ais_model_id": "A2"}
        res = self.engine.fuse(ml, ais)
        self.assertEqual(res["fusion"]["final_state"], "NORMAL")
        self.assertEqual(res["fusion"]["reason_code"], "HABSOS_AIS_LIMITED_RELIABILITY")

    def test_14_ml_dangerous_prediction_never_silently_erased(self):
        """Verify that ML warnings/critical alerts always raise states to WARNING/CRITICAL even if AIS is normal."""
        ml = {"dataset": "caml", "predicted_class": 4, "class_probabilities": {1: 0.1, 4: 0.9}, "confidence": 0.9, "dangerous_class": True, "model_id": "M1"}
        ais = {"dataset": "caml", "is_anomaly": False, "anomaly_score": 0.0, "matched_detector_count": 0, "nearest_detector_distance": 0.8, "ais_model_id": "A1"}
        res = self.engine.fuse(ml, ais)
        self.assertEqual(res["fusion"]["final_state"], "WARNING")

    def test_15_ais_anomaly_evidence_preserved(self):
        """Verify that the payload preserves the original anomaly indicators."""
        ml = {"dataset": "caml", "predicted_class": 1, "class_probabilities": {1: 0.9}, "confidence": 0.9, "dangerous_class": False, "model_id": "M1"}
        ais = {"dataset": "caml", "is_anomaly": True, "anomaly_score": 0.3, "matched_detector_count": 3, "nearest_detector_distance": 0.45, "ais_model_id": "A1"}
        res = self.engine.fuse(ml, ais)
        self.assertEqual(res["ais_evidence"]["is_anomaly"], True)
        self.assertEqual(res["ais_evidence"]["anomaly_score"], 0.3)

    def test_16_unknown_anomaly_emitted_correctly(self):
        """Verify that UNKNOWN_ANOMALY is emitted for OOD detections on CAML."""
        ml = {"dataset": "caml", "predicted_class": 1, "class_probabilities": {1: 0.9}, "confidence": 0.9, "dangerous_class": False, "model_id": "M1"}
        ais = {"dataset": "caml", "is_anomaly": True, "anomaly_score": 0.25, "matched_detector_count": 1, "nearest_detector_distance": 0.5, "ais_model_id": "A1"}
        res = self.engine.fuse(ml, ais)
        self.assertEqual(res["fusion"]["final_state"], "UNKNOWN_ANOMALY")

    def test_17_reason_codes_are_deterministic(self):
        """Assert that reason codes are mapped deterministically."""
        ml = {"dataset": "caml", "predicted_class": 1, "class_probabilities": {1: 0.9}, "confidence": 0.9, "dangerous_class": False, "model_id": "M1"}
        ais = {"dataset": "caml", "is_anomaly": False, "anomaly_score": 0.0, "matched_detector_count": 0, "nearest_detector_distance": 0.8, "ais_model_id": "A1"}
        res1 = self.engine.fuse(ml, ais)
        res2 = self.engine.fuse(ml, ais)
        self.assertEqual(res1["fusion"]["reason_code"], res2["fusion"]["reason_code"])

    def test_18_same_input_produces_same_output(self):
        """Assert no hidden state exists; identical inputs yield identical outputs."""
        ml = {"dataset": "caml", "predicted_class": 1, "class_probabilities": {1: 0.9}, "confidence": 0.9, "dangerous_class": False, "model_id": "M1"}
        ais = {"dataset": "caml", "is_anomaly": True, "anomaly_score": 0.3, "matched_detector_count": 2, "nearest_detector_distance": 0.42, "ais_model_id": "A1"}
        res1 = self.engine.fuse(ml, ais)
        res2 = self.engine.fuse(ml, ais)
        self.assertEqual(res1, res2)

    def test_19_final_payload_is_json_serializable(self):
        """Assert the final payload is completely JSON serializable."""
        ml = {"dataset": "caml", "predicted_class": 1, "class_probabilities": {1: 0.9}, "confidence": 0.9, "dangerous_class": False, "model_id": "M1"}
        ais = {"dataset": "caml", "is_anomaly": False, "anomaly_score": 0.0, "matched_detector_count": 0, "nearest_detector_distance": 0.8, "ais_model_id": "A1"}
        res = self.engine.fuse(ml, ais)
        serialized = json.dumps(res)
        self.assertTrue(isinstance(serialized, str))

    def test_20_decision_pipeline_supports_caml(self):
        """Assert that DecisionPipeline runs end-to-end on CAML observation."""
        caml_row = pd.DataFrame([{
            'lat': 27.5, 'lon': -81.2, 'distance_to_water_m': 120.0,
            'region': 'FL', 'Season': 'Summer', 'Year': 2020,
            'Month_sin': 0.5, 'Month_cos': -0.866,
            'DayOfYear_sin': 0.3, 'DayOfYear_cos': -0.95
        }])
        res = self.pipeline.run_pipeline("caml", caml_row)
        self.assertEqual(res["dataset"], "caml")
        self.assertIn("fusion", res)

    def test_21_decision_pipeline_supports_habsos(self):
        """Assert that DecisionPipeline runs end-to-end on HABSOS observation."""
        habsos_row = pd.DataFrame([{
            'LATITUDE': 27.5, 'LONGITUDE': -82.5, 'STATE_ID': 'FL',
            'SAMPLE_DEPTH': 5.0, 'SALINITY': 35.0, 'WATER_TEMP': 26.0,
            'Season': 'Summer', 'Year': 2020, 'Month': 7.0,
            'Month_sin': -0.5, 'Month_cos': -0.866,
            'DayOfYear_sin': -0.3, 'DayOfYear_cos': -0.95
        }])
        res = self.pipeline.run_pipeline("habsos", habsos_row)
        self.assertEqual(res["dataset"], "habsos")
        self.assertIn("fusion", res)

    def test_22_final_fusion_does_not_access_test_data(self):
        """Assert that run_phase6.py and fusion do not read test CSV splits."""
        run_file = os.path.join(self.workspace_dir, "run_phase6.py")
        self.assertTrue(os.path.exists(run_file))
        with open(run_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("caml_test.csv", content)
        self.assertNotIn("habsos_test.csv", content)

    def test_23_invalidated_model_artifacts_never_loaded(self):
        """Assert that the archived Phase 4 invalid artifacts are never read in the pipeline."""
        pipeline_file = os.path.join(self.workspace_dir, "src", "fusion", "decision_pipeline.py")
        self.assertTrue(os.path.exists(pipeline_file))
        with open(pipeline_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("models/archive/phase4_invalid", content)

if __name__ == "__main__":
    unittest.main()
