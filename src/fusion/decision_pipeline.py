import os
import pandas as pd
from dataclasses import asdict
from src.models.deployment_loader import DeploymentModelLoader
from src.ais.ais_loader import AISLoader
from src.fusion.fusion_engine import FusionEngine
from src.fusion.decision_adapter import DecisionAdapter

class DecisionPipeline:
    """
    Coordinates end-to-end telemetry evaluation:
    Raw Observation -> ML Output + AIS Output + Optional Visual Evidence -> Fusion Engine -> Decision Adapter -> Final System Decision.
    """
    def __init__(self, workspace_dir=None):
        self.ml_loader = DeploymentModelLoader(workspace_dir)
        self.ais_loader = AISLoader(workspace_dir)
        self.fusion_engine = FusionEngine()
        self.decision_adapter = DecisionAdapter()

    def run_pipeline(self, dataset_key, X, matching_radius=None, sensors=None, visual_evidence=None):
        """
        Executes end-to-end decision pipeline for CAML or HABSOS.
        X: pandas DataFrame containing raw inputs.
        matching_radius: optional custom matching radius for AIS.
        sensors: optional dict or list of dicts of raw sensor readings.
        visual_evidence: optional VisualEvidence object or dictionary for V4.5 multimodal fusion.
        """
        if not isinstance(X, pd.DataFrame):
            raise TypeError("Input X must be a pandas DataFrame.")

        # Run supervised ML champion
        ml_out = self.ml_loader.predict(dataset_key, X)
        
        # Run unsupervised AIS anomaly detection
        ais_out = self.ais_loader.predict_anomaly(dataset_key, X, matching_radius=matching_radius)

        # Standardize evidence format
        is_single = len(X) == 1
        
        if is_single:
            # Loader predict outputs single dict for single row
            ml_evidence = {
                "dataset": dataset_key,
                "predicted_class": ml_out["prediction"],
                "class_probabilities": ml_out["probabilities"],
                "confidence": ml_out["confidence"],
                "dangerous_class": ml_out["dangerous_detected"],
                "model_id": f"{ml_out['model_id']}-v{ml_out['model_version']}"
            }
            ais_evidence = {
                "dataset": dataset_key,
                "is_anomaly": ais_out["is_anomaly"],
                "anomaly_score": ais_out["anomaly_score"],
                "matched_detector_count": ais_out["matched_detector_count"],
                "nearest_detector_distance": ais_out["nearest_detector_distance"],
                "ais_model_id": ais_out["ais_version"]
            }
            # Execute Fusion
            fused_result = self.fusion_engine.fuse(ml_evidence, ais_evidence, sensors=sensors, visual_evidence=visual_evidence)
            
            # Execute V4.6 Decision Adapter Integration
            sys_event = self.decision_adapter.adapt(fused_result)
            fused_result["system_event"] = asdict(sys_event)
            return fused_result
        else:
            # Outputs are lists of dicts
            results = []
            for idx, (m_o, a_o) in enumerate(zip(ml_out, ais_out)):
                ml_evidence = {
                    "dataset": dataset_key,
                    "predicted_class": m_o["prediction"],
                    "class_probabilities": m_o["probabilities"],
                    "confidence": m_o["confidence"],
                    "dangerous_class": m_o["dangerous_detected"],
                    "model_id": f"{m_o['model_id']}-v{m_o['model_version']}"
                }
                ais_evidence = {
                    "dataset": dataset_key,
                    "is_anomaly": a_o["is_anomaly"],
                    "anomaly_score": a_o["anomaly_score"],
                    "matched_detector_count": a_o["matched_detector_count"],
                    "nearest_detector_distance": a_o["nearest_detector_distance"],
                    "ais_model_id": a_o["ais_version"]
                }
                row_sensors = sensors[idx] if isinstance(sensors, list) and idx < len(sensors) else None
                v_ev = visual_evidence[idx] if isinstance(visual_evidence, list) and idx < len(visual_evidence) else visual_evidence
                
                # Execute Fusion
                fused_result = self.fusion_engine.fuse(ml_evidence, ais_evidence, sensors=row_sensors, visual_evidence=v_ev)
                
                # Execute V4.6 Decision Adapter Integration
                sys_event = self.decision_adapter.adapt(fused_result)
                fused_result["system_event"] = asdict(sys_event)
                results.append(fused_result)
            return results
