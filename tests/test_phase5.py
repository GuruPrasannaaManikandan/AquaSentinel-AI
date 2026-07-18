import unittest
import os
import json
import joblib
import pandas as pd
import numpy as np
from src.models.deployment_loader import DeploymentModelLoader
from src.ais.preprocessing import AISPreprocessor
from src.ais.affinity import euclidean_distance, manhattan_distance
from src.ais.negative_selection import NegativeSelectionAlgorithm
from src.ais.ais_loader import AISLoader
from src.ais.parallel_inference import ParallelInferenceEngine

class TestPhase5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Paths
        cls.registry_path = os.path.join(cls.workspace_dir, "models", "ais", "ais_registry.json")
        cls.caml_artifact_path = os.path.join(cls.workspace_dir, "models", "ais", "caml_nsa.joblib")
        cls.habsos_artifact_path = os.path.join(cls.workspace_dir, "models", "ais", "habsos_nsa.joblib")

    def test_1_recovered_ml_models_remain_loadable(self):
        """Assert that recovered ML champions load correctly."""
        ml_loader = DeploymentModelLoader(self.workspace_dir)
        caml = ml_loader.load_model("caml")
        habsos = ml_loader.load_model("habsos")
        self.assertIsNotNone(caml)
        self.assertIsNotNone(habsos)

    def test_2_invalid_phase4_models_remain_blocked(self):
        """Assert that invalidated Phase 4 models cannot be loaded through loader."""
        ml_loader = DeploymentModelLoader(self.workspace_dir)
        original_manifest_models = ml_loader.manifest["models"]
        try:
            ml_loader.manifest["models"] = {
                "invalid_caml": {
                    "model_id": "caml_phase4_invalid",
                    "version": "3.0.0",
                    "artifact_path": "models/archive/phase4_invalid/caml_final_model.joblib"
                }
            }
            with self.assertRaises(PermissionError):
                ml_loader.load_model("invalid_caml")
        finally:
            ml_loader.manifest["models"] = original_manifest_models

    def test_3_ais_preprocessing_fits_only_self_training_data(self):
        """Assert that preprocessor is fitted correctly and learns properties of self."""
        features = ["val1", "val2"]
        # SELF data has specific bounds [0, 5]
        self_data = pd.DataFrame({"val1": [0.0, 5.0, 2.5], "val2": [5.0, 0.0, 2.5]})
        preprocessor = AISPreprocessor(features)
        preprocessor.fit(self_data)
        
        # Transformed data must be scaled within [0, 1] based strictly on self_data bounds
        transformed = preprocessor.transform(self_data)
        self.assertAlmostEqual(transformed.loc[0, "val1"], 0.0)
        self.assertAlmostEqual(transformed.loc[1, "val1"], 1.0)

    def test_4_ais_preprocessing_produces_finite_values(self):
        """Assert that preprocessor output contains only finite values."""
        features = ["val1", "val2"]
        data = pd.DataFrame({"val1": [1.0, np.nan, 3.0], "val2": [np.nan, 2.0, 4.0]})
        preprocessor = AISPreprocessor(features)
        preprocessor.fit(data) # medians will be 2.0 and 3.0
        transformed = preprocessor.transform(data)
        self.assertTrue(np.all(np.isfinite(transformed)))

    def test_5_affinity_calculations_are_mathematically_correct(self):
        """Assert distance calculations match mathematical expectations."""
        u = np.array([0.0, 0.0])
        v = np.array([3.0, 4.0])
        self.assertAlmostEqual(euclidean_distance(u, v), 5.0)
        self.assertAlmostEqual(manhattan_distance(u, v), 7.0)

    def test_6_candidate_detectors_matching_self_are_rejected(self):
        """Assert candidate detectors close to SELF are rejected."""
        # SELF is at [0.5, 0.5]
        X_self = np.array([[0.5, 0.5]])
        # Setup NSA with radius 0.2 and seed
        nsa = NegativeSelectionAlgorithm(num_detectors=1, self_radius=0.2, random_seed=42)
        nsa.fit(X_self)
        # Verify all accepted detectors are indeed outside radius 0.2
        for det in nsa.detectors_:
            dist = np.linalg.norm(det - X_self[0])
            self.assertGreater(dist, 0.2)

    def test_7_valid_non_self_detectors_are_accepted(self):
        """Assert candidate detectors far from SELF are accepted."""
        X_self = np.array([[0.0, 0.0]])
        # Target detector at [0.9, 0.9], which is > 0.5 distance
        nsa = NegativeSelectionAlgorithm(num_detectors=5, self_radius=0.1, max_attempts=10, random_seed=42)
        nsa.fit(X_self)
        self.assertEqual(len(nsa.detectors_), 5)

    def test_8_detector_generation_is_reproducible(self):
        """Assert that two NSA training runs with the same seed yield identical detectors."""
        X_self = np.random.uniform(0.1, 0.9, size=(50, 4))
        nsa1 = NegativeSelectionAlgorithm(num_detectors=20, self_radius=0.1, random_seed=123)
        nsa1.fit(X_self)
        
        nsa2 = NegativeSelectionAlgorithm(num_detectors=20, self_radius=0.1, random_seed=123)
        nsa2.fit(X_self)
        
        np.testing.assert_array_equal(nsa1.detectors_, nsa2.detectors_)

    def test_9_ais_output_shape_is_correct(self):
        """Assert predict returns correct output shapes."""
        X_self = np.array([[0.1, 0.1], [0.1, 0.2]])
        nsa = NegativeSelectionAlgorithm(num_detectors=5, self_radius=0.05)
        nsa.fit(X_self)
        
        X_test = np.array([[0.1, 0.1], [0.9, 0.9]])
        is_anomaly, anomaly_scores, matched_counts, min_dists = nsa.predict_anomaly(X_test)
        
        self.assertEqual(len(is_anomaly), 2)
        self.assertEqual(len(anomaly_scores), 2)
        self.assertEqual(len(matched_counts), 2)
        self.assertEqual(len(min_dists), 2)

    def test_10_ais_anomaly_scores_are_within_range(self):
        """Assert anomaly scores reside strictly in [0.0, 1.0]."""
        X_self = np.random.uniform(0.0, 0.5, size=(100, 3))
        nsa = NegativeSelectionAlgorithm(num_detectors=10, self_radius=0.2)
        nsa.fit(X_self)
        
        X_test = np.random.uniform(0.0, 1.0, size=(50, 3))
        _, scores, _, _ = nsa.predict_anomaly(X_test)
        
        self.assertTrue(np.all(scores >= 0.0))
        self.assertTrue(np.all(scores <= 1.0))

    def test_11_ais_serialization_preserves_predictions(self):
        """Assert that saving and reloading preserves predictions."""
        import tempfile
        X_self = np.random.uniform(0.0, 0.5, size=(100, 3))
        nsa = NegativeSelectionAlgorithm(num_detectors=10, self_radius=0.2, random_seed=42)
        nsa.fit(X_self)
        
        X_test = np.random.uniform(0.0, 1.0, size=(10, 3))
        pred1 = nsa.predict(X_test)
        scores1 = nsa.decision_function(X_test)
        
        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            joblib.dump(nsa, tmp_path)
            loaded_nsa = joblib.load(tmp_path)
            pred2 = loaded_nsa.predict(X_test)
            scores2 = loaded_nsa.decision_function(X_test)
            
            np.testing.assert_array_equal(pred1, pred2)
            np.testing.assert_array_almost_equal(scores1, scores2)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_12_ais_registry_is_valid(self):
        """Assert that the AIS registry file exists and has correct schema."""
        self.assertTrue(os.path.exists(self.registry_path))
        with open(self.registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)
        
        self.assertIn("models", registry)
        for model in registry["models"]:
            self.assertIn("ais_model_id", model)
            self.assertIn("dataset", model)
            self.assertIn("algorithm", model)
            self.assertIn("version", model)
            self.assertIn("self_definition", model)
            self.assertIn("feature_schema", model)
            self.assertIn("preprocessing", model)
            self.assertIn("affinity_metric", model)
            self.assertIn("detector_count", model)
            self.assertIn("self_radius", model)
            self.assertIn("validation_metrics", model)
            self.assertIn("artifact_path", model)

    def test_13_ais_loader_rejects_wrong_feature_schemas(self):
        """Assert that AISLoader raises error when wrong feature schemas are passed."""
        loader = AISLoader(self.workspace_dir)
        loader.load_model("caml")
        
        # Missing features
        wrong_input = pd.DataFrame({"lat": [27.5], "lon": [-81.2]})
        with self.assertRaises(ValueError):
            loader.predict_anomaly("caml", wrong_input)

    def test_14_caml_ais_loads(self):
        """Assert that CAML active AIS model loads successfully."""
        loader = AISLoader(self.workspace_dir)
        model = loader.load_model("caml")
        self.assertIsNotNone(model)

    def test_15_habsos_ais_loads(self):
        """Assert that HABSOS active AIS model loads successfully."""
        loader = AISLoader(self.workspace_dir)
        model = loader.load_model("habsos")
        self.assertIsNotNone(model)

    def test_16_parallel_ml_plus_ais_inference_works(self):
        """Assert that ParallelInferenceEngine integrates both runs correctly."""
        engine = ParallelInferenceEngine(self.workspace_dir)
        caml_input = pd.DataFrame([{
            'lat': 27.5, 'lon': -81.2, 'distance_to_water_m': 120.5,
            'region': 'FL', 'Season': 'Summer', 'Year': 2020,
            'Month_sin': 0.5, 'Month_cos': -0.866,
            'DayOfYear_sin': 0.3, 'DayOfYear_cos': -0.95
        }])
        res = engine.run_inference("caml", caml_input)
        self.assertIn("ml", res)
        self.assertIn("ais", res)
        
        # Verify content
        self.assertEqual(res["ml"]["model_id"], "caml_phase3_champion")
        self.assertEqual(res["ais"]["ais_version"], "NSA-CAML-v1")

    def test_17_final_fusion_not_accidentally_implemented(self):
        """Assert that no combined alert logic or final threat fusion is present."""
        engine = ParallelInferenceEngine(self.workspace_dir)
        caml_input = pd.DataFrame([{
            'lat': 27.5, 'lon': -81.2, 'distance_to_water_m': 120.5,
            'region': 'FL', 'Season': 'Summer', 'Year': 2020,
            'Month_sin': 0.5, 'Month_cos': -0.866,
            'DayOfYear_sin': 0.3, 'DayOfYear_cos': -0.95
        }])
        res = engine.run_inference("caml", caml_input)
        # Verify keys
        self.assertNotIn("final_threat_level", res)
        self.assertNotIn("risk_factor", res)

    def test_18_test_data_excluded_from_ais_parameters(self):
        """Assert that no test split files were referenced during training."""
        # Read run_phase5.py code and check that test files were never read
        run_file_path = os.path.join(self.workspace_dir, "run_phase5.py")
        self.assertTrue(os.path.exists(run_file_path))
        with open(run_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("caml_test.csv", content)
        self.assertNotIn("habsos_test.csv", content)

if __name__ == "__main__":
    unittest.main()
