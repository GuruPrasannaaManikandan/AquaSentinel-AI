import unittest
import os
import tempfile
import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from src.models.evaluate import calculate_classification_metrics, analyze_dangerous_false_negatives
from src.models.train import get_classifier, train_model_pipeline

class TestPhase3(unittest.TestCase):
    def test_metrics_calculation(self):
        """Assert metrics calculator correctly identifies F1, Cohen's Kappa, and per-class metrics."""
        y_true = [0, 0, 1, 1, 2, 2]
        y_pred = [0, 0, 1, 2, 2, 1]  # some misclassifications
        
        metrics = calculate_classification_metrics(y_true, y_pred)
        
        self.assertIn('accuracy', metrics)
        self.assertIn('f1_macro', metrics)
        self.assertIn('cohen_kappa', metrics)
        self.assertIn('per_class', metrics)
        
        # Per class check
        self.assertIn('0', metrics['per_class'])
        self.assertIn('1', metrics['per_class'])
        self.assertIn('2', metrics['per_class'])
        
        # Class 0 has perfect recall: 2 / 2 = 1.0
        self.assertEqual(metrics['per_class']['0']['recall'], 1.0)

    def test_dangerous_false_negatives(self):
        """Assert dangerous false negative auditor correctly flags missed blooms."""
        # 0 = normal, 1 = warning, 2 = critical
        # Dangerous classes: [1, 2], normal: [0]
        y_true = [0, 1, 2, 0, 1, 2]
        y_pred = [0, 0, 0, 0, 1, 2] # Two true dangerous samples (1, 2) predicted as 0 (normal)
        
        dfn_stats = analyze_dangerous_false_negatives(
            y_true, y_pred, dangerous_classes=[1, 2], normal_classes=[0]
        )
        
        self.assertEqual(dfn_stats['total_dangerous'], 4)
        self.assertEqual(dfn_stats['predicted_as_normal'], 2)
        # Recall: TP (2) / Total (4) = 0.5
        self.assertEqual(dfn_stats['dangerous_recall'], 0.5)
        # FNR = 1 - 0.5 = 0.5
        self.assertEqual(dfn_stats['dangerous_fnr'], 0.5)

    def test_pipeline_fit_and_serialization(self):
        """Assert fitting a pipeline works and joblib serializes it correctly."""
        # Mock data
        X_train = pd.DataFrame({'val': [1.0, 2.0, 3.0, 4.0, 5.0]})
        y_train = np.array([0, 0, 1, 1, 1])
        X_val = pd.DataFrame({'val': [1.5, 3.5]})
        y_val = np.array([0, 1])
        
        preprocessor = ColumnTransformer([('scaler', StandardScaler(), ['val'])])
        classifier = get_classifier("dummy", {}, seed=42)
        
        pipeline, metrics = train_model_pipeline(
            "test_dummy", classifier, preprocessor, X_train, y_train, X_val, y_val
        )
        
        self.assertIn('accuracy', metrics['val_metrics'])
        self.assertEqual(len(pipeline.predict(X_val)), 2)

        # Test joblib serialization and reload consistency
        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
            tmp_path = tmp.name
            
        try:
            joblib.dump(pipeline, tmp_path)
            loaded_pipeline = joblib.load(tmp_path)
            
            # Predict
            pred1 = pipeline.predict(X_val)
            pred2 = loaded_pipeline.predict(X_val)
            
            np.testing.assert_array_equal(pred1, pred2)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == "__main__":
    unittest.main()
