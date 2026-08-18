import os
import sys
sys.path.insert(0, ".")

from src.cv.visual_detection import VisualEvidence
from src.fusion.fusion_engine import FusionEngine

def test_diag():
    engine = FusionEngine()

    mock_ml_dangerous = {
        "dataset": "caml",
        "predicted_class": 4,
        "class_probabilities": {0: 0.10, 4: 0.90},
        "confidence": 0.90,
        "dangerous_class": True,
        "model_id": "RandomForest-v1.0.0"
    }
    mock_ais_normal = {
        "dataset": "caml",
        "is_anomaly": False,
        "anomaly_score": 0.10,
        "matched_detector_count": 5,
        "nearest_detector_distance": 0.05,
        "ais_model_id": "NSA-v1.0.0"
    }
    visual_ev = VisualEvidence(
        frame_id="F001",
        timestamp="2026-08-17T22:00:00Z",
        predicted_visual_class="ALGAL_BLOOM",
        confidence=0.95,
        visual_state="BLOOM_EVIDENCE",
        risk_level="HIGH",
        evidence_strength=0.95,
        model_name="MobileNetV3",
        model_version="1.0.0",
        inference_status="SUCCESS"
    )

    res = engine.fuse(mock_ml_dangerous, mock_ais_normal, visual_evidence=visual_ev)
    print("FUSED RESULT:")
    print(res["fusion"])

if __name__ == "__main__":
    test_diag()
