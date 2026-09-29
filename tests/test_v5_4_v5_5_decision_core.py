import os
import sys
import pytest
import numpy as np

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ais.adaptive_ais import AdaptiveAIS, MemoryCell
from src.ais.negative_selection import NegativeSelectionAlgorithm
from src.fusion.fusion_engine import FusionEngine
from src.cv.visual_detection import VisualEvidence


class TestV54AdaptiveAIS:
    """Tests for V5.4 Adaptive AIS with immunological memory and secondary response."""

    def setup_method(self):
        # Create a small synthetic NSA
        self.nsa = NegativeSelectionAlgorithm(num_detectors=10, self_radius=0.15, random_seed=42)
        # Train on synthetic SELF points centered at (0.2, 0.2)
        self_data = np.array([[0.20, 0.20], [0.22, 0.18], [0.18, 0.22], [0.21, 0.21]], dtype=np.float32)
        self.nsa.fit(self_data)
        self.adaptive = AdaptiveAIS(base_nsa=self.nsa, dataset_key="caml", memory_formation_threshold=2)

    def test_01_primary_immune_response_without_memory(self):
        """Verifies initial non-self antigen matches base detectors as a PRIMARY_RESPONSE."""
        non_self_antigen = np.array([[0.85, 0.85]], dtype=np.float32)
        results = self.adaptive.predict_adaptive(non_self_antigen)
        assert len(results) == 1
        res = results[0]
        # Should be an anomaly or self-tolerant, but initially zero memory cells
        assert res.active_memory_cells_count == 0
        assert res.memory_cell_matches == 0
        if res.is_anomaly:
            assert res.immune_response_type == "PRIMARY_RESPONSE"

    def test_02_memory_cell_formation_on_repeated_exposure(self):
        """Verifies repeated exposure to non-self antigen promotes it to a MemoryCell."""
        # Create a detector point in non-self space
        det_point = self.nsa.detectors_[0]
        antigen = det_point.reshape(1, -1)

        # First exposure -> candidate tracked
        r1 = self.adaptive.predict_adaptive(antigen)[0]
        assert r1.is_anomaly is True
        assert r1.immune_response_type == "PRIMARY_RESPONSE"

        # Second exposure -> hits threshold (2) and creates MemoryCell
        r2 = self.adaptive.predict_adaptive(antigen)[0]
        assert len(self.adaptive.memory_cells) >= 1
        assert self.adaptive.memory_cells[0].encounter_count >= 2

        # Third exposure -> matches MemoryCell triggering SECONDARY_RESPONSE
        r3 = self.adaptive.predict_adaptive(antigen)[0]
        assert r3.immune_response_type == "SECONDARY_RESPONSE"
        assert r3.memory_cell_matches >= 1
        assert r3.anomaly_score >= 0.85

    def test_03_memory_clearing(self):
        """Verifies clearing memory resets active memory cells while keeping base NSA intact."""
        antigen = self.nsa.detectors_[0].reshape(1, -1)
        self.adaptive.predict_adaptive(antigen)
        self.adaptive.predict_adaptive(antigen)
        assert len(self.adaptive.memory_cells) >= 1

        self.adaptive.clear_memory()
        assert len(self.adaptive.memory_cells) == 0
        assert len(self.adaptive.candidate_antigens) == 0
        # Base NSA still has all detectors
        assert len(self.nsa.detectors_) == 10


class TestV55EvidentialFusion:
    """Tests for V5.5 Reliability-Weighted Evidential Multimodal Fusion."""

    def setup_method(self):
        self.fusion = FusionEngine()
        self.ml_normal = {
            "dataset": "caml",
            "predicted_class": 0,
            "class_probabilities": {0: 0.92, 1: 0.08},
            "confidence": 0.92,
            "dangerous_class": False,
            "model_id": "RF-v1"
        }
        self.ml_dangerous = {
            "dataset": "caml",
            "predicted_class": 4,
            "class_probabilities": {0: 0.10, 4: 0.90},
            "confidence": 0.90,
            "dangerous_class": True,
            "model_id": "RF-v1"
        }
        self.ais_normal = {
            "dataset": "caml",
            "is_anomaly": False,
            "anomaly_score": 0.08,
            "matched_detector_count": 0,
            "nearest_detector_distance": 0.80,
            "ais_model_id": "NSA-v1"
        }
        self.ais_anomaly = {
            "dataset": "caml",
            "is_anomaly": True,
            "anomaly_score": 0.88,
            "matched_detector_count": 3,
            "nearest_detector_distance": 0.04,
            "ais_model_id": "NSA-v1"
        }

    def test_01_sensor_quality_weighting(self):
        """Verifies low Q_sensor down-weights sensor contribution in composite risk."""
        sq_good = {"q_sensor": 1.0, "quality_state": "EXCELLENT"}
        sq_poor = {"q_sensor": 0.20, "quality_state": "DEGRADED"}

        res_good = self.fusion.fuse(self.ml_dangerous, self.ais_anomaly, sensor_quality=sq_good)
        res_poor = self.fusion.fuse(self.ml_dangerous, self.ais_anomaly, sensor_quality=sq_poor)

        assert res_poor["fusion"]["modality_weights"]["sensor"] < res_good["fusion"]["modality_weights"]["sensor"]

    def test_02_optical_quality_weighting(self):
        """Verifies degraded camera (Q_visual = 0.25) down-weights visual evidence."""
        vis_good = {
            "visual_state": "BLOOM_EVIDENCE", "confidence": 0.90, "q_visual": 1.0,
            "effective_confidence": 0.90, "risk_level": "HIGH"
        }
        vis_poor = {
            "visual_state": "BLOOM_EVIDENCE", "confidence": 0.90, "q_visual": 0.25,
            "effective_confidence": 0.225, "risk_level": "HIGH"
        }

        res_good = self.fusion.fuse(self.ml_normal, self.ais_normal, visual_evidence=vis_good)
        res_poor = self.fusion.fuse(self.ml_normal, self.ais_normal, visual_evidence=vis_poor)

        assert res_poor["fusion"]["modality_weights"]["visual"] < res_good["fusion"]["modality_weights"]["visual"]
        assert res_poor["fusion"]["composite_risk_score"] < res_good["fusion"]["composite_risk_score"]

    def test_03_temporal_evidence_incorporation(self):
        """Verifies temporal trajectory risk score elevates composite risk and sets ecological_state."""
        temp_ev = {
            "temporal_state": "HIGH_RISK",
            "trajectory_risk_score": 0.75,
            "persistence_cycles": 3,
            "window_size_evaluated": 6
        }
        res = self.fusion.fuse(self.ml_normal, self.ais_normal, temporal_evidence=temp_ev)
        assert res["fusion"]["modality_weights"]["temporal"] > 0.0
        assert res["fusion"]["composite_risk_score"] > 0.20
        assert res["temporal_evidence"] is not None

    def test_04_multi_tier_ecological_state_classification(self):
        """Verifies ecological_state emits 5 tiers: NORMAL, WATCH, EARLY_WARNING, HIGH_RISK, BLOOM_CONFIRMED."""
        # 1. Normal baseline
        res_norm = self.fusion.fuse(self.ml_normal, self.ais_normal)
        assert res_norm["fusion"]["ecological_state"] == "NORMAL"

        # 2. Watch (early precursors)
        temp_watch = {"temporal_state": "WATCH", "trajectory_risk_score": 0.25, "window_size_evaluated": 4}
        res_watch = self.fusion.fuse(self.ml_normal, self.ais_normal, temporal_evidence=temp_watch)
        assert res_watch["fusion"]["ecological_state"] in ["WATCH", "EARLY_WARNING"]

        # 3. Early Warning (visual early warning)
        vis_bloom = {"visual_state": "BLOOM_EVIDENCE", "confidence": 0.92, "q_visual": 0.95, "risk_level": "HIGH"}
        res_ew = self.fusion.fuse(self.ml_normal, self.ais_normal, visual_evidence=vis_bloom)
        assert res_ew["fusion"]["ecological_state"] == "EARLY_WARNING"
        assert res_ew["fusion"]["reason_code"] == "VISUAL_EARLY_WARNING"

        # 4. Bloom Confirmed (multimodal confirmation)
        res_conf = self.fusion.fuse(self.ml_dangerous, self.ais_anomaly, visual_evidence=vis_bloom)
        assert res_conf["fusion"]["final_state"] == "CRITICAL"
        assert res_conf["fusion"]["ecological_state"] == "BLOOM_CONFIRMED"
        assert res_conf["fusion"]["reason_code"] == "MULTIMODAL_BLOOM_CONFIRMED"
