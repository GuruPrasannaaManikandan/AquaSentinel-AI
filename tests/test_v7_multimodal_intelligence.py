import datetime
import pytest
import numpy as np
from typing import Dict, Any

from src.fusion.fusion_engine import FusionEngine, MultimodalFusionEngine
from src.fusion.multimodal_alignment import (
    MultimodalEvidenceItem,
    MultimodalSnapshot,
    TemporalAlignmentEngine,
    build_multimodal_snapshot,
    adapt_sensor_evidence,
    adapt_visual_evidence,
    adapt_temporal_evidence,
    adapt_ais_evidence,
    adapt_historical_evidence
)
from src.fusion.multimodal_intelligence import (
    ConcordanceEngine,
    ConflictDetector,
    MultimodalStateEstimator,
    ConcordanceResult,
    ConflictResult,
    MultimodalStateResult
)
from src.fusion.explainability import ExplainabilityEngine, RecoveryHysteresisManager, ExplanationResult


def create_mock_evidence(
    sensor_threat: bool = False,
    sensor_conf: float = 0.95,
    visual_state: str = "NORMAL_WATER",
    visual_conf: float = 0.92,
    q_visual: float = 0.95,
    temporal_state: str = "NORMAL",
    temporal_risk: float = 0.05,
    temporal_window: int = 3,
    ais_anomaly: bool = False,
    ais_score: float = 0.10,
    historical_health: float = 0.95,
    reference_time: datetime.datetime = None
):
    """Utility helper generating standardized multi-modality evidence payloads."""
    if reference_time is None:
        reference_time = datetime.datetime.now(datetime.timezone.utc)
    ts = reference_time.isoformat()

    ml_ev = {
        "dataset": "caml",
        "predicted_class": 4 if sensor_threat else 0,
        "class_probabilities": {0: 0.1, 4: 0.9} if sensor_threat else {0: 0.9, 4: 0.1},
        "confidence": sensor_conf,
        "dangerous_class": sensor_threat,
        "model_id": "RandomForest-v1.0.0",
        "timestamp": ts
    }

    ais_ev = {
        "dataset": "caml",
        "is_anomaly": ais_anomaly,
        "anomaly_score": ais_score,
        "matched_detector_count": 5 if ais_anomaly else 0,
        "nearest_detector_distance": 0.05 if ais_anomaly else 0.85,
        "ais_model_id": "NSA-Adaptive-v1.0",
        "immune_response_type": "PRIMARY_RESPONSE" if ais_anomaly else "SELF_TOLERANT",
        "timestamp": ts
    }

    vis_ev = None
    if visual_state is not None:
        vis_ev = {
            "visual_state": visual_state,
            "class_name": visual_state,
            "confidence": visual_conf,
            "q_visual": q_visual,
            "effective_confidence": visual_conf * q_visual,
            "risk_level": "CRITICAL" if visual_state == "BLOOM_EVIDENCE" and visual_conf > 0.85 else ("HIGH" if visual_state == "BLOOM_EVIDENCE" else "NONE"),
            "evidence_state": visual_state,
            "timestamp": ts,
            "frame_id": "frame_v7_test"
        }

    temp_ev = None
    if temporal_state is not None:
        temp_ev = {
            "temporal_state": temporal_state,
            "trajectory_risk_score": temporal_risk,
            "window_size_evaluated": temporal_window,
            "lead_indicators": [f"Slope divergence in {temporal_state}"] if temporal_state != "NORMAL" else [],
            "timestamp": ts
        }

    hist_ev = None
    if historical_health is not None:
        hist_ev = {
            "ecosystem_health_index": historical_health,
            "total_observations": 25,
            "deviations_from_baseline": {},
            "timestamp": ts
        }

    return ml_ev, ais_ev, vis_ev, temp_ev, hist_ev


class TestV7MultimodalIntelligence:
    """
    Authoritative test suite verifying V7 Multimodal Intelligence.
    Contains all 20 required verification scenarios.
    """

    @pytest.fixture
    def engines(self):
        return {
            "fusion": FusionEngine(),
            "concordance": ConcordanceEngine(),
            "conflict": ConflictDetector(),
            "estimator": MultimodalStateEstimator(),
            "aligner": TemporalAlignmentEngine(),
            "explainer": ExplainabilityEngine(),
            "hysteresis": RecoveryHysteresisManager()
        }

    # -------------------------------------------------------------------------
    # Scenario 1: All normal -> NORMAL
    # -------------------------------------------------------------------------
    def test_scenario_01_all_normal_concordance(self, engines):
        """Scenario 1: All active modalities normal -> High concordance, NORMAL state."""
        ml_ev, ais_ev, vis_ev, temp_ev, hist_ev = create_mock_evidence(
            sensor_threat=False, visual_state="NORMAL_WATER", temporal_state="NORMAL"
        )
        fused = engines["fusion"].fuse(
            ml_ev, ais_ev, visual_evidence=vis_ev, temporal_evidence=temp_ev, historical_evidence=hist_ev
        )

        assert fused["fusion"]["ecological_state"] == "NORMAL"
        assert fused["concordance"]["concordance_state"] == "CONCORDANT"
        assert fused["conflict"]["conflict_detected"] is False
        assert fused["multimodal_state"]["dominance_prevented"] is False

    # -------------------------------------------------------------------------
    # Scenario 2: Sensor + Vision agreement -> strong bloom
    # -------------------------------------------------------------------------
    def test_scenario_02_sensor_vision_agreement(self, engines):
        """Scenario 2: Water chemistry sensor and visual camera agree on bloom -> Elevates to bloom."""
        ml_ev, ais_ev, vis_ev, temp_ev, _ = create_mock_evidence(
            sensor_threat=True, sensor_conf=0.92, visual_state="BLOOM_EVIDENCE", visual_conf=0.94
        )
        fused = engines["fusion"].fuse(ml_ev, ais_ev, visual_evidence=vis_ev)

        assert fused["fusion"]["final_state"] == "CRITICAL"
        assert fused["fusion"]["ecological_state"] == "BLOOM_CONFIRMED"
        assert fused["fusion"]["reason_code"] == "MULTIMODAL_BLOOM_CONFIRMED"
        assert fused["concordance"]["concordance_state"] in ["CONCORDANT", "PARTIALLY_CONCORDANT"]

    # -------------------------------------------------------------------------
    # Scenario 3: Sensor + Temporal agreement -> escalating warning
    # -------------------------------------------------------------------------
    def test_scenario_03_sensor_temporal_agreement(self, engines):
        """Scenario 3: Sensor threat corroborated by temporal worsening slope -> Escalates warning."""
        ml_ev, ais_ev, _, temp_ev, _ = create_mock_evidence(
            sensor_threat=True, sensor_conf=0.88, visual_state=None, temporal_state="HIGH_RISK", temporal_risk=0.75
        )
        fused = engines["fusion"].fuse(ml_ev, ais_ev, temporal_evidence=temp_ev)

        assert fused["fusion"]["ecological_state"] in ["HIGH_RISK", "BLOOM_CONFIRMED"]
        assert "TEMPORAL" in fused["multimodal_snapshot"]["available_modalities"]
        assert fused["conflict"]["conflict_detected"] is False

    # -------------------------------------------------------------------------
    # Scenario 4: Vision + Temporal agreement -> persistent visual warning
    # -------------------------------------------------------------------------
    def test_scenario_04_vision_temporal_agreement(self, engines):
        """Scenario 4: Camera bloom + temporal trajectory confirm bloom -> Persistent early warning."""
        ml_ev, ais_ev, vis_ev, temp_ev, _ = create_mock_evidence(
            sensor_threat=False, visual_state="BLOOM_EVIDENCE", visual_conf=0.90, temporal_state="EARLY_WARNING", temporal_risk=0.55
        )
        fused = engines["fusion"].fuse(ml_ev, ais_ev, visual_evidence=vis_ev, temporal_evidence=temp_ev)

        assert fused["fusion"]["ecological_state"] in ["EARLY_WARNING", "HIGH_RISK"]
        assert fused["fusion"]["reason_code"] in ["VISUAL_EARLY_WARNING", "MULTIMODAL_CONCORDANT"]

    # -------------------------------------------------------------------------
    # Scenario 5: Sensor + Vision + Temporal agreement -> strong multimodal confirmation
    # -------------------------------------------------------------------------
    def test_scenario_05_three_way_agreement(self, engines):
        """Scenario 5: Sensor + Camera + Temporal trends all confirm bloom -> BLOOM_CONFIRMED."""
        ml_ev, ais_ev, vis_ev, temp_ev, hist_ev = create_mock_evidence(
            sensor_threat=True, visual_state="BLOOM_EVIDENCE", visual_conf=0.95,
            temporal_state="BLOOM_CONFIRMED", temporal_risk=0.88, historical_health=0.30
        )
        fused = engines["fusion"].fuse(
            ml_ev, ais_ev, visual_evidence=vis_ev, temporal_evidence=temp_ev, historical_evidence=hist_ev
        )

        assert fused["fusion"]["ecological_state"] == "BLOOM_CONFIRMED"
        assert fused["concordance"]["concordance_state"] == "CONCORDANT"
        assert fused["concordance"]["agreement_score"] >= 0.70

    # -------------------------------------------------------------------------
    # Scenario 6: Sensor alarm + normal vision -> conflict detected, emergency suppressed
    # -------------------------------------------------------------------------
    def test_scenario_06_sensor_alarm_vision_normal_suppression(self, engines):
        """Scenario 6: Sensor alarm while camera clearly shows normal water -> Suppress emergency."""
        ml_ev, ais_ev, vis_ev, _, _ = create_mock_evidence(
            sensor_threat=True, sensor_conf=0.65, visual_state="NORMAL_WATER", visual_conf=0.95
        )
        fused = engines["fusion"].fuse(ml_ev, ais_ev, visual_evidence=vis_ev)

        # Conflict is detected
        assert fused["conflict"]["conflict_detected"] is True
        assert fused["conflict"]["conflict_type"] == "SENSOR_VS_VISION"
        assert fused["conflict"]["prescriptive_action"] == "SUPPRESS_EMERGENCY"
        # Emergency lockout suppressed: final_state is not CRITICAL
        assert fused["fusion"]["final_state"] != "CRITICAL"

    # -------------------------------------------------------------------------
    # Scenario 7: Sensor normal + bloom vision -> conflict detected, conservative hold
    # -------------------------------------------------------------------------
    def test_scenario_07_sensor_normal_vision_bloom_conservative_hold(self, engines):
        """Scenario 7: Sensor normal while camera detects surface bloom -> Conservative hold / early warning."""
        ml_ev, ais_ev, vis_ev, _, _ = create_mock_evidence(
            sensor_threat=False, visual_state="BLOOM_EVIDENCE", visual_conf=0.88
        )
        fused = engines["fusion"].fuse(ml_ev, ais_ev, visual_evidence=vis_ev)

        assert fused["conflict"]["conflict_detected"] is True
        assert fused["conflict"]["conflict_type"] == "SENSOR_VS_VISION"
        assert fused["conflict"]["prescriptive_action"] == "CONSERVATIVE_HOLD"
        assert fused["fusion"]["final_state"] in ["WARNING", "EARLY_WARNING"]

    # -------------------------------------------------------------------------
    # Scenario 8: Turbidity sensor + turbid vision -> sediment turbidity mitigated
    # -------------------------------------------------------------------------
    def test_scenario_08_sediment_turbidity_mitigation(self, engines):
        """Scenario 8: Elevated turbidity with turbid visual discoloration -> Mitigated (not bloom)."""
        ml_ev, ais_ev, vis_ev, _, _ = create_mock_evidence(
            sensor_threat=False, visual_state="TURBID_DISCOLORATION", visual_conf=0.90
        )
        fused = engines["fusion"].fuse(ml_ev, ais_ev, visual_evidence=vis_ev)

        assert fused["fusion"]["reason_code"] == "VISUAL_TURBIDITY_MITIGATED"
        assert fused["fusion"]["final_state"] == "NORMAL"

    # -------------------------------------------------------------------------
    # Scenario 9: Camera missing -> operational fallback
    # -------------------------------------------------------------------------
    def test_scenario_09_camera_missing_fallback(self, engines):
        """Scenario 9: Camera modality is offline/None -> Fallback operates gracefully on sensors."""
        ml_ev, ais_ev, _, temp_ev, _ = create_mock_evidence(
            sensor_threat=False, visual_state=None, temporal_state="NORMAL"
        )
        fused = engines["fusion"].fuse(ml_ev, ais_ev, visual_evidence=None, temporal_evidence=temp_ev)

        assert "VISION" in fused["multimodal_snapshot"]["missing_modalities"]
        assert fused["fusion"]["ecological_state"] == "NORMAL"
        assert fused["multimodal_intelligence"]["snapshot_summary"]["available_modalities"] is not None

    # -------------------------------------------------------------------------
    # Scenario 10: Sensor channel missing -> degraded but operational
    # -------------------------------------------------------------------------
    def test_scenario_10_sensor_channel_degraded_fallback(self, engines):
        """Scenario 10: Sensor probe quality degraded -> Weight deweighted, still operational."""
        ml_ev, ais_ev, vis_ev, _, _ = create_mock_evidence(
            sensor_threat=False, visual_state="NORMAL_WATER"
        )
        degraded_q = {"q_sensor": 0.35, "quality_state": "DEGRADED", "fault_detected": True}
        fused = engines["fusion"].fuse(
            ml_ev, ais_ev, visual_evidence=vis_ev, sensor_quality=degraded_q
        )

        assert "SENSOR" in fused["multimodal_snapshot"]["degraded_modalities"]
        assert fused["fusion"]["modality_weights"]["sensor"] < 0.40

    # -------------------------------------------------------------------------
    # Scenario 11: AIS missing -> operational fallback
    # -------------------------------------------------------------------------
    def test_scenario_11_ais_missing_fallback(self, engines):
        """Scenario 11: AIS model unavailable -> Gracefully omitted from snapshot without exception."""
        snapshot = build_multimodal_snapshot(
            device_id="AQUA_TEST_01",
            sensor_item=adapt_sensor_evidence({"dataset": "caml", "predicted_class": 0, "confidence": 0.90, "dangerous_class": False}),
            ais_item=None
        )
        assert "AIS" in snapshot.missing_modalities
        res = engines["estimator"].estimate_state(snapshot, engines["concordance"].evaluate(snapshot), engines["conflict"].detect(snapshot))
        assert res.ecological_state == "NORMAL"

    # -------------------------------------------------------------------------
    # Scenario 12: Historical missing -> operational fallback
    # -------------------------------------------------------------------------
    def test_scenario_12_historical_missing_fallback(self, engines):
        """Scenario 12: Historical baseline missing during cold start -> Handled gracefully."""
        snapshot = build_multimodal_snapshot(
            device_id="AQUA_TEST_01",
            sensor_item=adapt_sensor_evidence({"dataset": "caml", "predicted_class": 0, "confidence": 0.90, "dangerous_class": False}),
            historical_item=None
        )
        assert "HISTORICAL" in snapshot.missing_modalities
        assert snapshot.alignment_quality > 0.0

    # -------------------------------------------------------------------------
    # Scenario 13: Stale visual evidence -> deweighted/excluded
    # -------------------------------------------------------------------------
    def test_scenario_13_stale_visual_evidence_deweighting(self, engines):
        """Scenario 13: Frame timestamp is >30 seconds old -> Flagged STALE and deweighted."""
        old_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=45)).isoformat()
        vis_stale = {
            "visual_state": "BLOOM_EVIDENCE",
            "confidence": 0.95,
            "q_visual": 0.90,
            "effective_confidence": 0.855,
            "timestamp": old_time
        }
        item = adapt_visual_evidence(vis_stale, reference_time=datetime.datetime.now(datetime.timezone.utc))
        assert item.freshness_state == "STALE"
        assert item.reliability < 0.15

    # -------------------------------------------------------------------------
    # Scenario 14: Stale sensor evidence -> deweighted/excluded
    # -------------------------------------------------------------------------
    def test_scenario_14_stale_sensor_evidence(self, engines):
        """Scenario 14: Sensor telemetry timestamp is >30 seconds old -> Flagged STALE."""
        old_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=50)).isoformat()
        s_ev = {
            "dataset": "caml",
            "predicted_class": 4,
            "confidence": 0.90,
            "dangerous_class": True,
            "timestamp": old_time
        }
        item = adapt_sensor_evidence(s_ev, reference_time=datetime.datetime.now(datetime.timezone.utc))
        assert item.freshness_state == "STALE"
        assert item.valid is False

    # -------------------------------------------------------------------------
    # Scenario 15: Multiple conflicting modalities -> UNCERTAIN / conservative
    # -------------------------------------------------------------------------
    def test_scenario_15_multiple_conflicts_uncertainty(self, engines):
        """Scenario 15: Multimodal discordance across 3+ feeds -> Flags MULTIPLE_CONFLICTS, high uncertainty."""
        ref = datetime.datetime.now(datetime.timezone.utc)
        # SENSOR: Threat, VISION: Normal, AIS: Anomaly, TEMPORAL: Normal
        s_item = adapt_sensor_evidence({"dataset": "caml", "predicted_class": 4, "confidence": 0.85, "dangerous_class": True, "timestamp": ref.isoformat()})
        v_item = adapt_visual_evidence({"visual_state": "NORMAL_WATER", "confidence": 0.90, "timestamp": ref.isoformat()})
        t_item = adapt_temporal_evidence({"temporal_state": "NORMAL", "trajectory_risk_score": 0.05, "window_size_evaluated": 3, "timestamp": ref.isoformat()})
        a_item = adapt_ais_evidence({"dataset": "caml", "is_anomaly": True, "anomaly_score": 0.80, "timestamp": ref.isoformat()})

        snapshot = build_multimodal_snapshot(sensor_item=s_item, vision_item=v_item, temporal_item=t_item, ais_item=a_item)
        conflict = engines["conflict"].detect(snapshot)
        state_res = engines["estimator"].estimate_state(snapshot, engines["concordance"].evaluate(snapshot), conflict)

        assert conflict.conflict_detected is True
        assert state_res.uncertainty >= 0.25

    # -------------------------------------------------------------------------
    # Scenario 16: Full bloom confirmation (Sensor+Vision+Temporal+AIS) -> BLOOM_CONFIRMED
    # -------------------------------------------------------------------------
    def test_scenario_16_full_bloom_confirmation(self, engines):
        """Scenario 16: All 4 real-time modalities confirm bloom -> High confidence BLOOM_CONFIRMED."""
        ref = datetime.datetime.now(datetime.timezone.utc)
        ml_ev, ais_ev, vis_ev, temp_ev, _ = create_mock_evidence(
            sensor_threat=True, sensor_conf=0.96, visual_state="BLOOM_EVIDENCE", visual_conf=0.96,
            temporal_state="BLOOM_CONFIRMED", temporal_risk=0.90, ais_anomaly=True, ais_score=0.88,
            reference_time=ref
        )
        fused = engines["fusion"].fuse(
            ml_ev, ais_ev, visual_evidence=vis_ev, temporal_evidence=temp_ev
        )

        assert fused["fusion"]["ecological_state"] == "BLOOM_CONFIRMED"
        assert fused["fusion"]["final_state"] == "CRITICAL"
        assert fused["concordance"]["concordance_state"] == "CONCORDANT"

    # -------------------------------------------------------------------------
    # Scenario 17: Recovery hysteresis respected (K=3)
    # -------------------------------------------------------------------------
    def test_scenario_17_recovery_hysteresis_respected(self, engines):
        """Scenario 17: Elevated state requires 3 consecutive normal cycles to clear."""
        hyst = engines["hysteresis"]
        dev_id = "AQUA_HYST_01"

        # 1. Trigger alarm
        st1, rec_st1, cnt1 = hyst.apply_hysteresis(dev_id, "BLOOM_CONFIRMED")
        assert st1 == "BLOOM_CONFIRMED"
        assert rec_st1 == "STABLE"

        # 2. First normal reading -> Held in RECOVERY_HOLD
        st2, rec_st2, cnt2 = hyst.apply_hysteresis(dev_id, "NORMAL")
        assert st2 != "NORMAL"
        assert rec_st2 == "RECOVERY_HOLD"
        assert cnt2 == 1

        # 3. Second normal reading -> Still held
        st3, rec_st3, cnt3 = hyst.apply_hysteresis(dev_id, "NORMAL")
        assert rec_st3 == "RECOVERY_HOLD"
        assert cnt3 == 2

        # 4. Third consecutive normal reading -> Cleared to NORMAL
        st4, rec_st4, cnt4 = hyst.apply_hysteresis(dev_id, "NORMAL")
        assert st4 == "NORMAL"
        assert rec_st4 == "RECOVERED"
        assert cnt4 == 3

    # -------------------------------------------------------------------------
    # Scenario 18: Single noisy sensor -> dominance prevented, no false emergency
    # -------------------------------------------------------------------------
    def test_scenario_18_single_sensor_dominance_prevented(self, engines):
        """Scenario 18: Single noisy probe cannot trigger false emergency shutoff."""
        ref = datetime.datetime.now(datetime.timezone.utc)
        # Sensor reports threat with low quality / noisy condition
        s_item = adapt_sensor_evidence(
            {"dataset": "caml", "predicted_class": 4, "confidence": 0.85, "dangerous_class": True, "timestamp": ref.isoformat()},
            sensor_quality={"q_sensor": 0.50, "quality_state": "NOISY"}
        )
        # All other modalities are normal
        v_item = adapt_visual_evidence({"visual_state": "NORMAL_WATER", "confidence": 0.95, "timestamp": ref.isoformat()})
        t_item = adapt_temporal_evidence({"temporal_state": "NORMAL", "trajectory_risk_score": 0.05, "timestamp": ref.isoformat()})
        a_item = adapt_ais_evidence({"dataset": "caml", "is_anomaly": False, "anomaly_score": 0.10, "timestamp": ref.isoformat()})

        snapshot = build_multimodal_snapshot(sensor_item=s_item, vision_item=v_item, temporal_item=t_item, ais_item=a_item)
        conflict = engines["conflict"].detect(snapshot)
        state_res = engines["estimator"].estimate_state(snapshot, engines["concordance"].evaluate(snapshot), conflict)

        assert state_res.dominance_prevented is True
        assert state_res.ecological_state in ["EARLY_WARNING", "WATCH", "NORMAL"]
        assert state_res.ecological_state != "BLOOM_CONFIRMED"

    # -------------------------------------------------------------------------
    # Scenario 19: Low quality camera -> visual mass discounted
    # -------------------------------------------------------------------------
    def test_scenario_19_low_quality_camera_discounted(self, engines):
        """Scenario 19: Degraded camera optical quality (e.g. lens fog) discounts visual mass."""
        ref = datetime.datetime.now(datetime.timezone.utc)
        vis_fog = {
            "visual_state": "BLOOM_EVIDENCE",
            "confidence": 0.88,
            "q_visual": 0.30,  # heavily degraded
            "effective_confidence": 0.264,
            "timestamp": ref.isoformat()
        }
        item = adapt_visual_evidence(vis_fog)
        assert item.valid is False
        assert "Optical quality severely degraded" in (item.degradation_reason or "")
        assert item.reliability < 0.15

    # -------------------------------------------------------------------------
    # Scenario 20: Historical context -> contextual baseline explanation included
    # -------------------------------------------------------------------------
    def test_scenario_20_historical_context_explanation(self, engines):
        """Scenario 20: Historical digital baseline contextualizes explanation in XAI output."""
        ml_ev, ais_ev, vis_ev, temp_ev, hist_ev = create_mock_evidence(
            sensor_threat=False, visual_state="NORMAL_WATER", historical_health=0.85
        )
        fused = engines["fusion"].fuse(
            ml_ev, ais_ev, visual_evidence=vis_ev, temporal_evidence=temp_ev, historical_evidence=hist_ev
        )
        expl_res = engines["explainer"].explain(fused, device_id="AQUA_TEST_01")

        assert isinstance(expl_res, ExplanationResult)
        assert expl_res.concordance_state == "CONCORDANT"
        assert any("Multimodal Concordance" in k for k in expl_res.key_factors)
        assert expl_res.conflict_detected is False
