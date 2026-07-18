import os
import pandas as pd
from src.models.deployment_loader import DeploymentModelLoader
from src.ais.ais_loader import AISLoader

class ParallelInferenceEngine:
    """
    Coordinates execution of supervised ML and unsupervised AIS anomaly detection
    in parallel, returning independent outputs.
    """
    def __init__(self, workspace_dir=None):
        self.ml_loader = DeploymentModelLoader(workspace_dir)
        self.ais_loader = AISLoader(workspace_dir)

    def run_inference(self, dataset_key, X, matching_radius=None):
        """
        Executes parallel prediction.
        dataset_key: 'caml' or 'habsos'
        X: pandas DataFrame containing raw inputs.
        """
        if not isinstance(X, pd.DataFrame):
            raise TypeError("Input X must be a pandas DataFrame.")

        # Execute ML prediction (supervised threat classification)
        ml_payload = self.ml_loader.predict(dataset_key, X)

        # Execute AIS prediction (unsupervised negative selection anomaly detection)
        ais_payload = self.ais_loader.predict_anomaly(dataset_key, X, matching_radius=matching_radius)

        # Pack parallel outputs independently
        return {
            "ml": ml_payload,
            "ais": ais_payload
        }
