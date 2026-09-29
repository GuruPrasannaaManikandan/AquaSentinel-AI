import os
import sys
import pytest
import datetime

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fusion.fusion_engine import FusionEngine
from src.fusion.temporal_intelligence import TemporalEnvironmentalEngine
from src.fusion.explainability import ExplainabilityEngine, RecoveryHysteresisManager
from src.cv.visual_detection import VisualEvidence
from src.iot.sensor_quality import SensorQualityEvaluator


class TestV510EndToEndScenarioMatrix:
    """
    V5.10 Final End-to-End Scenario Verification Suite.
    Validates the complete 7-scenario ecological threat matrix across
    Sensors, Optical Vision, Adaptive AIS, Temporal Intelligence, and Recovery Hysteresis.
    """

    def setup_method(self):
        self.fusion = FusionEngine()
        self.temporal = TemporalEnvironmentalEngine(window_size=12)
        self.quality = SensorQualityEvaluator()
        self.explainer = ExplainabilityEngine()
        self.hysteresis = RecoveryHysteresisManager(required_normal_cycles=3)
        self.device_id = "AQUA_E2E_001"

    # --- SCENARIO 1: Normal Ecosystem ---
    def test_scenario_1_normal_ecosystem(self):
        """Scenario 1: Normal ecosystem (Good sensors, normal vision, AIS normal, stable temporal -> NORMAL)."""
        sensors = {"temperature_c": 21.5, "ph": 7.35, "turbidity_ntu": 4.5, "dissolved_oxygen_mg_l": 8.2, "salinity_ppt": 0.2}
        sq = self.quality.evaluate(sensors, device_id=self.device_id).to_dict()
        temp_ev = self.temporal.evaluate_telemetry(self.device_id, sensors, q_sensor=sq["q_sensor"]).to_dict()

        ml_ev = {"dataset": "caml", "predicted_class": 0, "class_probabilities": {0: 0.95}, "confidence": 0.95, "dangerous_class": False, "model_id": "RF-v1"}
        ais_ev = {"dataset": "caml", "is_anomaly": False, "anomaly_score": 0.05, "matched_detector_count": 0, "nearest_detector_distance": 0.85, "ais_model_id": "NSA-v1"}
        vis_ev = {"visual_state": "NO_VISUAL_BLOOM", "confidence": 0.96, "q_visual": 0.94, "effective_confidence": 0.902, "risk_level": "NONE"}

        res = self.fusion.fuse(ml_ev, ais_ev, sensors=sensors, visual_evidence=vis_ev, sensor_quality=sq, temporal_evidence=temp_ev)
        assert res["fusion"]["final_state"] == "NORMAL"
        assert res["fusion"]["ecological_state"] == "NORMAL"
        assert res["fusion"]["composite_risk_score"] < 0.15

        expl = self.explainer.explain(res, device_id=self.device_id)
        assert expl.state == "NORMAL"

    # --- SCENARIO 2: Emerging Bloom (Gradual change, mild evidence, rising trend -> EARLY_WARNING) ---
    def test_scenario_2_emerging_bloom(self):
        """Scenario 2: Emerging bloom (Gradual warming & pH rise, early visual evidence -> EARLY_WARNING)."""
        base_time = datetime.datetime(2026, 9, 20, 10, 0, 0)
        temp_ev = None
        for i in range(5):
            ts = (base_time + datetime.timedelta(seconds=i * 10)).isoformat()
            sensors = {
                "timestamp": ts,
                "temperature_c": 22.0 + i * 0.08,
                "ph": 7.6 + i * 0.14,  # Rapid pH rise
                "turbidity_ntu": 8.0 + i * 1.5,
                "dissolved_oxygen_mg_l": 8.0 + i * 0.20,
                "salinity_ppt": 0.2
            }
            sq = self.quality.evaluate(sensors, device_id=self.device_id).to_dict()
            temp_ev = self.temporal.evaluate_telemetry(self.device_id, sensors, q_sensor=sq["q_sensor"]).to_dict()

        ml_ev = {"dataset": "caml", "predicted_class": 0, "class_probabilities": {0: 0.70, 1: 0.30}, "confidence": 0.70, "dangerous_class": False, "model_id": "RF-v1"}
        ais_ev = {"dataset": "caml", "is_anomaly": True, "anomaly_score": 0.65, "matched_detector_count": 1, "nearest_detector_distance": 0.08, "ais_model_id": "NSA-v1"}
        vis_ev = {"visual_state": "BLOOM_EVIDENCE", "confidence": 0.88, "q_visual": 0.86, "effective_confidence": 0.756, "risk_level": "HIGH"}

        res = self.fusion.fuse(ml_ev, ais_ev, sensors=sensors, visual_evidence=vis_ev, sensor_quality=sq, temporal_evidence=temp_ev)
        assert res["fusion"]["ecological_state"] in ["EARLY_WARNING", "HIGH_RISK"]
        assert res["fusion"]["final_state"] in ["WARNING", "CRITICAL"]

        expl = self.explainer.explain(res, device_id=self.device_id)
        assert any("pH" in f or "algal bloom scum" in f for f in expl.key_factors)

    # --- SCENARIO 3: Confirmed Bloom ---
    def test_scenario_3_confirmed_bloom(self):
        """Scenario 3: Confirmed bloom (Extreme parameters, confirmed visual scum, AIS novelty -> BLOOM_CONFIRMED)."""
        sensors = {"temperature_c": 28.0, "ph": 9.4, "turbidity_ntu": 65.0, "dissolved_oxygen_mg_l": 12.0, "salinity_ppt": 0.2}
        sq = self.quality.evaluate(sensors, device_id=self.device_id).to_dict()

        temp_ev = {
            "temporal_state": "BLOOM_CONFIRMED",
            "trajectory_risk_score": 0.90,
            "persistence_cycles": 5,
            "window_size_evaluated": 10
        }
        ml_ev = {"dataset": "caml", "predicted_class": 4, "class_probabilities": {4: 0.95}, "confidence": 0.95, "dangerous_class": True, "model_id": "RF-v1"}
        ais_ev = {"dataset": "caml", "is_anomaly": True, "anomaly_score": 0.92, "matched_detector_count": 4, "nearest_detector_distance": 0.02, "ais_model_id": "NSA-v1"}
        vis_ev = {"visual_state": "BLOOM_EVIDENCE", "confidence": 0.97, "q_visual": 0.95, "effective_confidence": 0.921, "risk_level": "HIGH"}

        res = self.fusion.fuse(ml_ev, ais_ev, sensors=sensors, visual_evidence=vis_ev, sensor_quality=sq, temporal_evidence=temp_ev)
        assert res["fusion"]["final_state"] == "CRITICAL"
        assert res["fusion"]["ecological_state"] == "BLOOM_CONFIRMED"
        assert res["fusion"]["composite_risk_score"] >= 0.75

    # --- SCENARIO 4: Sensor Fault Graceful Handling ---
    def test_scenario_4_sensor_fault_graceful_handling(self):
        """Scenario 4: Sensor fault (Impossible physical spike, low Q_sensor -> Degraded sensor evidence, no false bloom)."""
        # Inject an impossible rate jump from pH 7.0 to 13.5 in 10s
        self.quality.evaluate({"ph": 7.0, "temperature_c": 20.0, "turbidity_ntu": 5.0, "dissolved_oxygen_mg_l": 8.0, "salinity_ppt": 0.2}, device_id="D_FAULT")
        sq_fault = self.quality.evaluate({"ph": 13.5, "temperature_c": 20.0, "turbidity_ntu": 5.0, "dissolved_oxygen_mg_l": 8.0, "salinity_ppt": 0.2}, device_id="D_FAULT").to_dict()

        assert sq_fault["q_sensor"] < 0.85
        assert sq_fault["components"]["ph"]["status"] in ["DEGRADED", "SUSPICIOUS", "FAULT"]
        assert "SUSPICIOUS_PH_RATE" in str(sq_fault["degradation_reasons"]) or len(sq_fault["degradation_reasons"]) > 0

        # Normal vision confirming clear water
        vis_clear = {"visual_state": "NO_VISUAL_BLOOM", "confidence": 0.95, "q_visual": 0.95, "effective_confidence": 0.90, "risk_level": "NONE"}
        ml_ev = {"dataset": "caml", "predicted_class": 0, "class_probabilities": {0: 0.90}, "confidence": 0.90, "dangerous_class": False, "model_id": "RF-v1"}
        ais_ev = {"dataset": "caml", "is_anomaly": False, "anomaly_score": 0.10, "matched_detector_count": 0, "nearest_detector_distance": 0.70, "ais_model_id": "NSA-v1"}

        res = self.fusion.fuse(ml_ev, ais_ev, visual_evidence=vis_clear, sensor_quality=sq_fault)
        # Should NOT trigger bloom alarm
        assert res["fusion"]["final_state"] == "NORMAL"
        assert res["fusion"]["ecological_state"] == "NORMAL"

    # --- SCENARIO 5: Camera Fault Graceful Fallback ---
    def test_scenario_5_camera_fault_graceful_fallback(self):
        """Scenario 5: Camera fault (Camera offline/corrupted/fogged -> Gracefully retains sensor decision)."""
        vis_fault = {
            "visual_state": "CAMERA_FAULT",
            "confidence": 0.0,
            "q_visual": 0.0,
            "reason_code": "VISUAL_CAMERA_FAULT",
            "risk_level": "UNKNOWN"
        }
        ml_normal = {"dataset": "caml", "predicted_class": 0, "class_probabilities": {0: 0.95}, "confidence": 0.95, "dangerous_class": False, "model_id": "RF-v1"}
        ais_normal = {"dataset": "caml", "is_anomaly": False, "anomaly_score": 0.05, "matched_detector_count": 0, "nearest_detector_distance": 0.85, "ais_model_id": "NSA-v1"}

        res = self.fusion.fuse(ml_normal, ais_normal, visual_evidence=vis_fault)
        assert res["fusion"]["final_state"] == "NORMAL"
        assert res["fusion"]["reason_code"] == "VISUAL_CAMERA_FAULT"
        assert res["fusion"]["modality_weights"]["visual"] == 0.0  # Camera discounted

    # --- SCENARIO 6: Conflicting Evidence Handling ---
    def test_scenario_6_conflicting_evidence_handling(self):
        """Scenario 6: Conflicting evidence (Sensor ML low conf warning + Camera confirms clear water -> Mitigated to NORMAL)."""
        ml_low_conf = {"dataset": "caml", "predicted_class": 2, "class_probabilities": {2: 0.40}, "confidence": 0.40, "dangerous_class": True, "model_id": "RF-v1"}
        ais_normal = {"dataset": "caml", "is_anomaly": False, "anomaly_score": 0.10, "matched_detector_count": 0, "nearest_detector_distance": 0.75, "ais_model_id": "NSA-v1"}
        vis_clear = {"visual_state": "NO_VISUAL_BLOOM", "confidence": 0.97, "q_visual": 0.95, "effective_confidence": 0.92, "risk_level": "NONE"}

        res = self.fusion.fuse(ml_low_conf, ais_normal, visual_evidence=vis_clear)
        assert res["fusion"]["final_state"] == "NORMAL"
        assert res["fusion"]["reason_code"] == "VISUAL_DISCONFIRMED_NORMAL"

    # --- SCENARIO 7: Full Recovery with Hysteresis ---
    def test_scenario_7_full_recovery_with_hysteresis(self):
        """Scenario 7: Recovery cycle (Alarm state -> 3 consecutive normals required -> step-down to NORMAL)."""
        dev = "AQUA_RECOVERY_TEST"

        # 1. Active threat
        st1, r_st1, cnt1 = self.hysteresis.apply_hysteresis(dev, "BLOOM_CONFIRMED")
        assert st1 == "BLOOM_CONFIRMED"
        assert r_st1 == "STABLE"

        # 2. First normal reading after intervention
        st2, r_st2, cnt2 = self.hysteresis.apply_hysteresis(dev, "NORMAL")
        assert st2 in ["EARLY_WARNING", "WATCH"]
        assert r_st2 == "RECOVERY_HOLD"
        assert cnt2 == 1

        # 3. Second normal reading
        st3, r_st3, cnt3 = self.hysteresis.apply_hysteresis(dev, "NORMAL")
        assert r_st3 == "RECOVERY_HOLD"
        assert cnt3 == 2

        # 4. Third normal reading -> Confirmed Recovery!
        st4, r_st4, cnt4 = self.hysteresis.apply_hysteresis(dev, "NORMAL")
        assert st4 == "NORMAL"
        assert r_st4 == "RECOVERED"
        assert cnt4 == 3
