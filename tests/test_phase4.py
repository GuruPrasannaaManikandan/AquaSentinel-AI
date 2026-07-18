import unittest
import os
import joblib
import json
import numpy as np
import pandas as pd
from src.utils.config import Config

@unittest.skip("Phase 4 models have been officially invalidated after the Phase 4.5 integrity audit")
class TestPhase4(unittest.TestCase):
    def test_model_files_exist(self):
        """Assert final serialized pipeline files exist in models folder."""
        workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caml_path = os.path.join(workspace_dir, "models", "caml_final_model.joblib")
        habsos_path = os.path.join(workspace_dir, "models", "habsos_final_model.joblib")
        
        self.assertTrue(os.path.exists(caml_path), "CAML final model is missing.")
        self.assertTrue(os.path.exists(habsos_path), "HABSOS final model is missing.")

    def test_model_inference_and_calibration(self):
        """Assert reloaded pipelines can predict class and predict valid calibrated probabilities."""
        workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 1. CAML Test
        caml_path = os.path.join(workspace_dir, "models", "caml_final_model.joblib")
        caml_model = joblib.load(caml_path)
        
        caml_input = pd.DataFrame([{
            'lat': 27.5,
            'lon': -81.2,
            'distance_to_water_m': 120.5,
            'region': 'FL',
            'Season': 'Summer',
            'Year': 2020,
            'Month_sin': 0.5,
            'Month_cos': -0.866,
            'DayOfYear_sin': 0.3,
            'DayOfYear_cos': -0.95
        }])
        
        pred_caml = caml_model.predict(caml_input)[0]
        self.assertIn(pred_caml, [1, 2, 3, 4, 5])
        
        probs_caml = caml_model.predict_proba(caml_input)[0]
        self.assertEqual(len(probs_caml), 5)
        np.testing.assert_almost_equal(np.sum(probs_caml), 1.0, decimal=4)
        
        # 2. HABSOS Test
        habsos_path = os.path.join(workspace_dir, "models", "habsos_final_model.joblib")
        habsos_model = joblib.load(habsos_path)
        
        habsos_input = pd.DataFrame([{
            'LATITUDE': 27.5,
            'LONGITUDE': -82.5,
            'STATE_ID': 'FL',
            'SAMPLE_DEPTH': 0.5,
            'SALINITY': 32.0,
            'WATER_TEMP': 24.0,
            'Season': 'Summer',
            'Year': 2020,
            'Month': 7.0,
            'Month_sin': -0.5,
            'Month_cos': -0.866,
            'DayOfYear_sin': -0.3,
            'DayOfYear_cos': -0.95,
            'SALINITY_is_missing': 0.0,
            'WATER_TEMP_is_missing': 0.0
        }])
        
        pred_habsos = habsos_model.predict(habsos_input)[0]
        self.assertIn(pred_habsos, ['normal', 'warning', 'critical'])
        
        probs_habsos = habsos_model.predict_proba(habsos_input)[0]
        self.assertEqual(len(probs_habsos), 3)
        np.testing.assert_almost_equal(np.sum(probs_habsos), 1.0, decimal=4)

    def test_model_registry_schema(self):
        """Assert models/model_registry.json contains final model entries."""
        workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        registry_path = os.path.join(workspace_dir, "models", "model_registry.json")
        
        self.assertTrue(os.path.exists(registry_path), "Registry file is missing.")
        
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
            
        self.assertIn('models', registry)
        self.assertIn('caml', registry['models'])
        self.assertIn('habsos', registry['models'])

if __name__ == "__main__":
    unittest.main()
