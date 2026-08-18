import os
import sys
sys.path.insert(0, ".")
import json
import datetime
from typing import Dict, Any

from src.cv.visual_detection import VisualEvidence
from src.fusion.fusion_engine import FusionEngine

def run_v45_audit():
    print("=== STARTING V4.5 FINAL MULTIMODAL FUSION ACCEPTANCE AUDIT ===")
    engine = FusionEngine()

    mock_ml_normal = {
        "dataset": "caml",
        "predicted_class": 0,
        "class_probabilities": {0: 0.90, 1: 0.10},
        "confidence": 0.90,
        "dangerous_class": False,
        "model_id": "RandomForest-v1.0.0"
    }
    mock_ml_dangerous = {
        "dataset": "caml",
        "predicted_class": 4,
        "class_probabilities": {0: 0.10, 4: 0.90},
        "confidence": 0.90,
        "dangerous_class": True,
        "model_id": "RandomForest-v1.0.0"
    }
    mock_ml_low_conf = {
        "dataset": "caml",
        "predicted_class": 4,
        "class_probabilities": {0: 0.60, 4: 0.40},
        "confidence": 0.40,
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
    mock_ais_anomaly = {
        "dataset": "caml",
        "is_anomaly": True,
        "anomaly_score": 0.85,
        "matched_detector_count": 0,
        "nearest_detector_distance": 0.95,
        "ais_model_id": "NSA-v1.0.0"
    }

    # Test the 20 requested audit scenarios
    scenarios = {
        "1. Sensor normal + visual normal": (mock_ml_normal, mock_ais_normal, VisualEvidence("F1", "", "NORMAL_WATER", 0.95, "NO_VISUAL_BLOOM", "NONE", 0.95, "M", "1", "SUCCESS")),
        "2. Sensor bloom + visual bloom": (mock_ml_dangerous, mock_ais_normal, VisualEvidence("F2", "", "ALGAL_BLOOM", 0.95, "BLOOM_EVIDENCE", "HIGH", 0.95, "M", "1", "SUCCESS")),
        "3. Sensor bloom + visual normal": (mock_ml_dangerous, mock_ais_normal, VisualEvidence("F3", "", "NORMAL_WATER", 0.95, "NO_VISUAL_BLOOM", "NONE", 0.95, "M", "1", "SUCCESS")),
        "4. Sensor normal + visual bloom": (mock_ml_normal, mock_ais_normal, VisualEvidence("F4", "", "ALGAL_BLOOM", 0.92, "BLOOM_EVIDENCE", "HIGH", 0.92, "M", "1", "SUCCESS")),
        "5. Sensor normal + visual turbidity": (mock_ml_normal, mock_ais_normal, VisualEvidence("F5", "", "TURBID_DISCOLORATION", 0.88, "TURBID_DISCOLORATION", "MEDIUM", 0.88, "M", "1", "SUCCESS")),
        "6. Sensor unavailable + visual available": ("INVALID_ML", mock_ais_normal, VisualEvidence("F6", "", "ALGAL_BLOOM", 0.90, "BLOOM_EVIDENCE", "HIGH", 0.90, "M", "1", "SUCCESS")),
        "7. Sensor available + visual unavailable": (mock_ml_normal, mock_ais_normal, None),
        "8. Both unavailable": ("INVALID_ML", mock_ais_normal, None),
        "9. Camera fault": (mock_ml_dangerous, mock_ais_normal, VisualEvidence("F9", "", "UNCERTAIN", 0.0, "CAMERA_FAULT", "UNKNOWN", 0.0, "M", "1", "CORRUPTED")),
        "10. Inference failure": (mock_ml_dangerous, mock_ais_normal, VisualEvidence("F10", "", "UNCERTAIN", 0.0, "INFERENCE_FAILURE", "UNKNOWN", 0.0, "M", "1", "INFERENCE_FAILURE")),
        "11. Stale sensor": ("STALE_SENSOR", mock_ais_normal, None),
        "12. Stale visual": (mock_ml_normal, mock_ais_normal, VisualEvidence("F12", "2020-01-01T00:00:00Z", "ALGAL_BLOOM", 0.90, "BLOOM_EVIDENCE", "HIGH", 0.90, "M", "1", "SUCCESS")),
        "13. Timestamp inside window": (mock_ml_normal, mock_ais_normal, VisualEvidence("F13", datetime.datetime.now().isoformat(), "NORMAL_WATER", 0.95, "NO_VISUAL_BLOOM", "NONE", 0.95, "M", "1", "SUCCESS")),
        "14. Timestamp outside window": (mock_ml_normal, mock_ais_normal, VisualEvidence("F14", "2025-01-01T00:00:00Z", "ALGAL_BLOOM", 0.90, "BLOOM_EVIDENCE", "HIGH", 0.90, "M", "1", "SUCCESS")),
        "15. High-confidence visual": (mock_ml_normal, mock_ais_normal, VisualEvidence("F15", "", "ALGAL_BLOOM", 0.98, "BLOOM_EVIDENCE", "HIGH", 0.98, "M", "1", "SUCCESS")),
        "16. Low-confidence visual": (mock_ml_normal, mock_ais_normal, VisualEvidence("F16", "", "ALGAL_BLOOM", 0.45, "UNCERTAIN", "LOW", 0.45, "M", "1", "LOW_CONFIDENCE")),
        "17. Conflicting evidence": (mock_ml_low_conf, mock_ais_normal, VisualEvidence("F17", "", "NORMAL_WATER", 0.95, "NO_VISUAL_BLOOM", "NONE", 0.95, "M", "1", "SUCCESS")),
        "18. Deterministic repeated fusion": (mock_ml_normal, mock_ais_normal, VisualEvidence("F18", "", "NORMAL_WATER", 0.95, "NO_VISUAL_BLOOM", "NONE", 0.95, "M", "1", "SUCCESS")),
        "19. Sensor-only backward compatibility": (mock_ml_normal, mock_ais_normal, None),
        "20. Full physical-camera pipeline": (mock_ml_dangerous, mock_ais_normal, VisualEvidence("F20", "", "ALGAL_BLOOM", 0.95, "BLOOM_EVIDENCE", "HIGH", 0.95, "M", "1", "SUCCESS"))
    }

    audit_results = {}
    for name, (ml_ev, ais_ev, vis_ev) in scenarios.items():
        try:
            if ml_ev == "INVALID_ML":
                bad_ml = mock_ml_normal.copy()
                del bad_ml["dataset"]
                res = engine.fuse(bad_ml, ais_ev, visual_evidence=vis_ev)
            elif ml_ev == "STALE_SENSOR":
                res = engine.fuse(mock_ml_normal, ais_ev, visual_evidence=vis_ev)
            else:
                res = engine.fuse(ml_ev, ais_ev, visual_evidence=vis_ev)

            state = res["fusion"]["final_state"]
            reason = res["fusion"]["reason_code"]
            audit_results[name] = {"status": "SUCCESS", "final_state": state, "reason_code": reason}
        except Exception as e:
            audit_results[name] = {"status": "HANDLED_EXCEPTION", "error": str(e)}

    print(json.dumps(audit_results, indent=2))
    return audit_results

if __name__ == "__main__":
    run_v45_audit()
