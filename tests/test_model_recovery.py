import unittest
import os
import json
import joblib
import pandas as pd
import numpy as np
from src.models.deployment_loader import DeploymentModelLoader

class TestModelRecovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.loader = DeploymentModelLoader(cls.workspace_dir)

    def test_1_caml_champion_loads(self):
        """Assert that CAML champion loads successfully."""
        model = self.loader.load_model("caml")
        self.assertIsNotNone(model)

    def test_2_habsos_champion_loads(self):
        """Assert that HABSOS champion loads successfully."""
        model = self.loader.load_model("habsos")
        self.assertIsNotNone(model)

    def test_3_invalid_phase4_models_cannot_be_loaded(self):
        """Assert that invalidated models (from registry) raise PermissionError if loaded."""
        # Inject an invalid model entry into the manifest and assert load fails
        original_manifest_models = self.loader.manifest["models"]
        
        try:
            self.loader.manifest["models"] = {
                "invalid_caml": {
                    "model_id": "caml_phase4_invalid",
                    "version": "3.0.0",
                    "artifact_path": "models/archive/phase4_invalid/caml_final_model.joblib"
                }
            }
            with self.assertRaises(PermissionError):
                self.loader.load_model("invalid_caml")
        finally:
            self.loader.manifest["models"] = original_manifest_models

    def test_4_manifest_paths_exist(self):
        """Assert that all artifact paths in the manifest exist on disk."""
        for key, info in self.loader.manifest["models"].items():
            path = os.path.join(self.workspace_dir, info["artifact_path"])
            self.assertTrue(os.path.exists(path), f"Artifact path for {key} does not exist: {path}")

    def test_5_registry_and_manifest_agree(self):
        """Assert that the manifest active models exist in the registry with DEPLOYMENT_CANDIDATE status."""
        for key, info in self.loader.manifest["models"].items():
            model_id = info["model_id"]
            found = False
            for reg_entry in self.loader.registry["models"]:
                if reg_entry["model_id"] == model_id:
                    found = True
                    self.assertEqual(reg_entry["status"], "DEPLOYMENT_CANDIDATE")
                    self.assertEqual(reg_entry["audit_status"], "VERIFIED_AFTER_PHASE45")
                    break
            self.assertTrue(found, f"Model ID {model_id} from manifest not found in registry")

    def test_6_feature_schemas_match(self):
        """Assert that manifest expected features match registry feature schemas."""
        for key, info in self.loader.manifest["models"].items():
            model_id = info["model_id"]
            manifest_feats = info["expected_features"]
            for reg_entry in self.loader.registry["models"]:
                if reg_entry["model_id"] == model_id:
                    self.assertEqual(reg_entry["feature_schema"], manifest_feats)
                    break

    def test_7_target_mappings_match(self):
        """Assert that target mappings in manifest and registry agree."""
        for key, info in self.loader.manifest["models"].items():
            model_id = info["model_id"]
            manifest_mapping = info["target_mapping"]
            for reg_entry in self.loader.registry["models"]:
                if reg_entry["model_id"] == model_id:
                    self.assertEqual(reg_entry["target_mapping"], manifest_mapping)
                    break

    def test_8_model_classes_matches_probability_ordering(self):
        """Assert that model.classes_ matches predict_proba output columns."""
        # 1. CAML
        caml_model = self.loader.load_model("caml")
        caml_input = pd.DataFrame([{
            'lat': 27.5, 'lon': -81.2, 'distance_to_water_m': 120.5,
            'region': 'FL', 'Season': 'Summer', 'Year': 2020,
            'Month_sin': 0.5, 'Month_cos': -0.866,
            'DayOfYear_sin': 0.3, 'DayOfYear_cos': -0.95
        }])
        payload_caml = self.loader.predict("caml", caml_input)
        # Convert classes_ to int if numeric, else string to match the loaded dictionary keys
        expected_caml_keys = [int(cls) if isinstance(cls, (int, np.integer)) else str(cls) for cls in caml_model.classes_]
        self.assertEqual(list(payload_caml["probabilities"].keys()), expected_caml_keys)

        # 2. HABSOS
        habsos_model = self.loader.load_model("habsos")
        habsos_input = pd.DataFrame([{
            'LATITUDE': 27.5, 'LONGITUDE': -82.5, 'STATE_ID': 'FL',
            'SAMPLE_DEPTH': 0.5, 'SALINITY': 32.0, 'WATER_TEMP': 24.0,
            'Season': 'Summer', 'Year': 2020, 'Month': 7.0,
            'Month_sin': -0.5, 'Month_cos': -0.866,
            'DayOfYear_sin': -0.3, 'DayOfYear_cos': -0.95
        }])
        payload_habsos = self.loader.predict("habsos", habsos_input)
        expected_habsos_keys = [int(cls) if isinstance(cls, (int, np.integer)) else str(cls) for cls in habsos_model.classes_]
        self.assertEqual(list(payload_habsos["probabilities"].keys()), expected_habsos_keys)

    def test_9_dangerous_class_definitions_valid(self):
        """Assert that dangerous-class definitions match specification."""
        caml_dangerous = self.loader.manifest["models"]["caml"]["dangerous_classes"]
        self.assertEqual(caml_dangerous, [4, 5])

        habsos_dangerous = self.loader.manifest["models"]["habsos"]["dangerous_classes"]
        self.assertEqual(habsos_dangerous, ["warning", "critical"])

    def test_10_predictions_survive_serialization(self):
        """Assert that predictions of reloaded models match those before reload/re-serialization."""
        import tempfile
        
        caml_input = pd.DataFrame([{
            'lat': 27.5, 'lon': -81.2, 'distance_to_water_m': 120.5,
            'region': 'FL', 'Season': 'Summer', 'Year': 2020,
            'Month_sin': 0.5, 'Month_cos': -0.866,
            'DayOfYear_sin': 0.3, 'DayOfYear_cos': -0.95
        }])
        
        model1 = self.loader.load_model("caml")
        pred1 = model1.predict(caml_input)
        probs1 = model1.predict_proba(caml_input)
        
        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            joblib.dump(model1, tmp_path)
            model2 = joblib.load(tmp_path)
            pred2 = model2.predict(caml_input)
            probs2 = model2.predict_proba(caml_input)
            
            self.assertEqual(pred1[0], pred2[0])
            np.testing.assert_almost_equal(probs1[0], probs2[0], decimal=5)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_11_probability_outputs_sum_to_1(self):
        """Assert that probability outputs sum to 1.0 (or very close)."""
        caml_input = pd.DataFrame([{
            'lat': 27.5, 'lon': -81.2, 'distance_to_water_m': 120.5,
            'region': 'FL', 'Season': 'Summer', 'Year': 2020,
            'Month_sin': 0.5, 'Month_cos': -0.866,
            'DayOfYear_sin': 0.3, 'DayOfYear_cos': -0.95
        }])
        payload_caml = self.loader.predict("caml", caml_input)
        self.assertAlmostEqual(sum(payload_caml["probabilities"].values()), 1.0, places=4)

        habsos_input = pd.DataFrame([{
            'LATITUDE': 27.5, 'LONGITUDE': -82.5, 'STATE_ID': 'FL',
            'SAMPLE_DEPTH': 0.5, 'SALINITY': 32.0, 'WATER_TEMP': 24.0,
            'Season': 'Summer', 'Year': 2020, 'Month': 7.0,
            'Month_sin': -0.5, 'Month_cos': -0.866,
            'DayOfYear_sin': -0.3, 'DayOfYear_cos': -0.95
        }])
        payload_habsos = self.loader.predict("habsos", habsos_input)
        self.assertAlmostEqual(sum(payload_habsos["probabilities"].values()), 1.0, places=4)

    def test_12_repeated_predictions_are_reproducible(self):
        """Assert that repeated calls yield identical results."""
        caml_input = pd.DataFrame([{
            'lat': 27.5, 'lon': -81.2, 'distance_to_water_m': 120.5,
            'region': 'FL', 'Season': 'Summer', 'Year': 2020,
            'Month_sin': 0.5, 'Month_cos': -0.866,
            'DayOfYear_sin': 0.3, 'DayOfYear_cos': -0.95
        }])
        payload1 = self.loader.predict("caml", caml_input)
        payload2 = self.loader.predict("caml", caml_input)
        self.assertEqual(payload1["prediction"], payload2["prediction"])
        for k in payload1["probabilities"]:
            self.assertAlmostEqual(payload1["probabilities"][k], payload2["probabilities"][k], places=6)

    def test_13_ais_payload_schema_is_valid(self):
        """Assert that the returned payload conforms to the expected schema layout."""
        caml_input = pd.DataFrame([{
            'lat': 27.5, 'lon': -81.2, 'distance_to_water_m': 120.5,
            'region': 'FL', 'Season': 'Summer', 'Year': 2020,
            'Month_sin': 0.5, 'Month_cos': -0.866,
            'DayOfYear_sin': 0.3, 'DayOfYear_cos': -0.95
        }])
        payload = self.loader.predict("caml", caml_input)
        
        expected_keys = ["model_id", "model_version", "prediction", "probabilities", "confidence", "dangerous_detected"]
        for key in expected_keys:
            self.assertIn(key, payload)
        
        self.assertIsInstance(payload["model_id"], str)
        self.assertIsInstance(payload["model_version"], str)
        self.assertIsInstance(payload["prediction"], int)
        self.assertIsInstance(payload["probabilities"], dict)
        self.assertIsInstance(payload["confidence"], float)
        self.assertIsInstance(payload["dangerous_detected"], bool)

if __name__ == "__main__":
    unittest.main()
