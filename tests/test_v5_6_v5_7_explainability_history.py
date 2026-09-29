import os
import sys
import pytest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fusion.explainability import ExplainabilityEngine, RecoveryHysteresisManager, ExplanationResult
from src.iot.historical_intelligence import HistoricalIntelligenceEngine, DigitalEcosystemState


class TestV56ExplainabilityAndRecovery:
    """Tests for V5.6 Explainability Engine and Recovery Hysteresis Manager."""

    def setup_method(self):
        self.explainer = ExplainabilityEngine()
        self.recovery = RecoveryHysteresisManager(required_normal_cycles=3)

    def test_01_modality_attribution_sums_to_100(self):
        """Verifies modality attribution percentages sum to 100.0%."""
        fused_decision = {
            "device_id": "AQUA_TEST_001",
            "fusion": {
                "final_state": "CRITICAL",
                "ecological_state": "BLOOM_CONFIRMED",
                "composite_risk_score": 0.88,
                "reason_code": "MULTIMODAL_BLOOM_CONFIRMED",
                "modality_weights": {"sensor": 0.40, "visual": 0.35, "temporal": 0.30, "ais": 0.20}
            },
            "ml_evidence": {"dangerous_class": True, "predicted_class": 4, "confidence": 0.90},
            "ais_evidence": {"is_anomaly": True, "anomaly_score": 0.85, "immune_response_type": "SECONDARY_RESPONSE"},
            "visual_evidence": {"visual_state": "BLOOM_EVIDENCE", "confidence": 0.95, "q_visual": 0.92, "effective_confidence": 0.874},
            "temporal_evidence": {"trajectory_risk_score": 0.80, "lead_indicators": ["Rapid pH climb (+0.45 pH/min)"]}
        }

        res = self.explainer.explain(fused_decision)
        assert isinstance(res, ExplanationResult)
        assert res.state == "BLOOM_CONFIRMED"
        assert res.risk_score == 0.88

        # Check attribution sum
        attrib = res.modality_attribution
        total_pct = sum(attrib.values())
        assert pytest.approx(total_pct, abs=0.1) == 100.0
        assert attrib["sensor_pct"] > 0
        assert attrib["visual_pct"] > 0

        # Check key factors
        assert any("algal bloom scum" in f for f in res.key_factors)
        assert any("SECONDARY IMMUNE RESPONSE" in f for f in res.key_factors)

    def test_02_feature_attribution_sums_to_100(self):
        """Verifies feature-level attribution percentages sum to 100.0%."""
        fused_decision = {
            "device_id": "AQUA_TEST_001",
            "fusion": {"final_state": "WARNING", "ecological_state": "EARLY_WARNING", "composite_risk_score": 0.45},
            "ml_evidence": {"dangerous_class": False, "confidence": 0.60},
            "ais_evidence": {"is_anomaly": False, "anomaly_score": 0.10},
            "visual_evidence": None,
            "temporal_evidence": {
                "trajectory_risk_score": 0.45,
                "metric_trends": {
                    "ph": {"current_value": 8.8, "slope_per_min": 0.12},
                    "turbidity_ntu": {"current_value": 25.0, "slope_per_min": 2.5},
                    "temperature_c": {"current_value": 24.5, "slope_per_min": 0.20},
                    "dissolved_oxygen_mg_l": {"current_value": 9.5, "slope_per_min": 0.15}
                }
            }
        }
        res = self.explainer.explain(fused_decision)
        feat_total = sum(res.feature_attribution.values())
        assert pytest.approx(feat_total, abs=0.1) == 100.0
        assert res.feature_attribution["ph_elevation"] > 0

    def test_03_recovery_hysteresis_enforcement(self):
        """Verifies K=3 consecutive normal observations required before clearing alarm state."""
        dev = "DEV_HYST_01"

        # 1. Enter alarm state
        st1, rec_st1, cnt1 = self.recovery.apply_hysteresis(dev, "HIGH_RISK")
        assert st1 == "HIGH_RISK"
        assert rec_st1 == "STABLE"

        # 2. First normal observation -> Held in recovery
        st2, rec_st2, cnt2 = self.recovery.apply_hysteresis(dev, "NORMAL")
        assert st2 in ["EARLY_WARNING", "WATCH"]
        assert rec_st2 == "RECOVERY_HOLD"
        assert cnt2 == 1

        # 3. Second normal observation -> Still held
        st3, rec_st3, cnt3 = self.recovery.apply_hysteresis(dev, "NORMAL")
        assert rec_st3 == "RECOVERY_HOLD"
        assert cnt3 == 2

        # 4. Third normal observation -> Confirmed recovered
        st4, rec_st4, cnt4 = self.recovery.apply_hysteresis(dev, "NORMAL")
        assert st4 == "NORMAL"
        assert rec_st4 == "RECOVERED"
        assert cnt4 == 3

        # 5. Subsequent normal remains stable NORMAL
        st5, rec_st5, cnt5 = self.recovery.apply_hysteresis(dev, "NORMAL")
        assert st5 == "NORMAL"
        assert rec_st5 == "STABLE"

    def test_04_recovery_interruption_resets_counter(self):
        """Verifies a recurring threat during recovery resets the consecutive normal counter."""
        dev = "DEV_HYST_02"
        self.recovery.apply_hysteresis(dev, "CRITICAL")

        # 2 normals
        self.recovery.apply_hysteresis(dev, "NORMAL")
        self.recovery.apply_hysteresis(dev, "NORMAL")

        # Threat re-emerges
        st, rec_st, cnt = self.recovery.apply_hysteresis(dev, "HIGH_RISK")
        assert st == "HIGH_RISK"

        # Next normal should start back at count 1
        st_next, rec_next, cnt_next = self.recovery.apply_hysteresis(dev, "NORMAL")
        assert cnt_next == 1
        assert rec_next == "RECOVERY_HOLD"


class TestV57HistoricalIntelligence:
    """Tests for V5.7 / V5.8 Historical Intelligence Engine and Digital Ecosystem State."""

    def setup_method(self):
        self.hist = HistoricalIntelligenceEngine(max_history_points=50)
        self.device_id = "AQUA_HIST_001"

    def test_01_baseline_accumulation(self):
        """Verifies repeated observations accumulate statistical mean, std, and median."""
        for i in range(10):
            telemetry = {
                "timestamp": f"2026-09-20T12:{i:02d}:00Z",
                "temperature_c": 20.0 + (i % 3) * 0.5,
                "ph": 7.2 + (i % 2) * 0.1,
                "turbidity_ntu": 4.0 + (i % 2) * 0.5,
                "dissolved_oxygen_mg_l": 8.0,
                "salinity_ppt": 0.2
            }
            state = self.hist.update_and_evaluate(self.device_id, telemetry)

        assert isinstance(state, DigitalEcosystemState)
        assert state.total_observations == 10
        ph_base = state.baselines["ph"]
        assert ph_base["sample_count"] == 10
        assert 7.2 <= ph_base["mean"] <= 7.3
        assert state.ecosystem_health_index >= 0.85

    def test_02_anomalous_zscore_detection(self):
        """Verifies a sudden out-of-baseline reading produces high Z-score and decreases health index."""
        # 10 baseline readings around pH 7.2
        for i in range(10):
            self.hist.update_and_evaluate(self.device_id, {
                "temperature_c": 20.0, "ph": 7.2, "turbidity_ntu": 5.0, "dissolved_oxygen_mg_l": 8.0, "salinity_ppt": 0.2
            })

        # Sudden jump to pH 9.5
        spike_state = self.hist.update_and_evaluate(self.device_id, {
            "temperature_c": 20.0, "ph": 9.5, "turbidity_ntu": 5.0, "dissolved_oxygen_mg_l": 8.0, "salinity_ppt": 0.2
        })

        assert spike_state.deviations_from_baseline["ph_zscore"] > 3.0
        assert spike_state.ecosystem_health_index < 1.0

    def test_03_event_logging(self):
        """Verifies significant non-normal decisions are recorded in recent_events buffer."""
        telemetry = {"temperature_c": 22.0, "ph": 8.5, "turbidity_ntu": 15.0, "dissolved_oxygen_mg_l": 8.0, "salinity_ppt": 0.2}
        decision = {
            "fusion": {"final_state": "WARNING", "ecological_state": "EARLY_WARNING", "reason_code": "VISUAL_EARLY_WARNING", "composite_risk_score": 0.65}
        }
        state = self.hist.update_and_evaluate(self.device_id, telemetry, decision=decision)
        assert len(state.recent_events) >= 1
        assert state.recent_events[-1]["state"] == "EARLY_WARNING"
