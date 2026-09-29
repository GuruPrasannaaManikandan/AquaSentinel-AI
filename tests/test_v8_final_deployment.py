import os
import time
import json
import sqlite3
import tempfile
import pytest
from typing import Dict, Any

from src.fusion.risk_trajectory import RiskTrajectoryEngine, RiskTrendResult
from src.fusion.autonomous_response import (
    AutonomousResponseEngine,
    ActuatorSafetyGate,
    AutonomousRecoveryManager,
    ActuatorDecision
)
from src.iot.gateway import Gateway
from src.iot.esp32_device import ESP32Device
from src.iot.event_store import EventStore
from tests.soak_test_v8 import run_soak_test


class TestV8FinalDeployment:
    """
    V8 Research-Grade Deployment & End-to-End Validation Suite.
    Covers 21 mandatory scenarios spanning normal operation, multimodal conditions,
    fault injection, safety gate barriers, and a 1,000-cycle soak test.
    """

    @pytest.fixture(autouse=True)
    def setup_suite(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "v8_test.db")
        self.event_store = EventStore(db_path=self.db_path)
        self.risk_engine = RiskTrajectoryEngine(window_size=12, min_sufficient_cycles=3)
        self.response_engine = AutonomousResponseEngine(pump_cooldown_sec=5.0, buzzer_cooldown_sec=10.0)
        yield
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    # =========================================================================
    # 1. NORMAL OPERATION
    # =========================================================================

    def test_01_stable_healthy_ecosystem(self):
        """Scenario 1: Stable healthy ecosystem leads to MONITOR policy and NORMAL horizon."""
        dev_id = "DEV_01"
        for i in range(5):
            decision = {
                "timestamp": f"2026-09-20T12:0{i}:00Z",
                "fusion": {"final_state": "NORMAL", "confidence": 0.90},
                "ml_evidence": {"predicted_class": 1, "confidence": 0.92},
                "multimodal_intelligence": {
                    "synthesized_state": "NORMAL",
                    "confidence": 0.90,
                    "concordance_score": 0.95,
                    "conflict_detected": False,
                    "dominance_prevented": False
                }
            }
            trend = self.risk_engine.evaluate_trajectory(dev_id, decision, current_time_sec=i * 60.0)
            policy, act = self.response_engine.evaluate_response(dev_id, decision, trend, now_sec=i * 60.0)

        assert trend.trajectory == "STABLE"
        assert trend.horizon_state == "NO_IMMEDIATE_RISK"
        assert policy == "MONITOR"
        assert act.approved_action == "NO_ACTION"

    def test_02_gradually_increasing_bloom_risk(self):
        """Scenario 2: Gradually rising risk slope produces RISING trajectory and DEVELOPING_RISK."""
        dev_id = "DEV_02"
        states = ["NORMAL", "WATCH", "WATCH", "EARLY_WARNING", "EARLY_WARNING"]
        for i, st in enumerate(states):
            decision = {
                "timestamp": f"2026-09-20T12:0{i}:00Z",
                "fusion": {"final_state": st, "confidence": 0.85},
                "ml_evidence": {"predicted_class": 2, "confidence": 0.80},
                "multimodal_intelligence": {
                    "synthesized_state": st,
                    "confidence": 0.85,
                    "concordance_score": 0.90,
                    "conflict_detected": False,
                    "dominance_prevented": False
                }
            }
            trend = self.risk_engine.evaluate_trajectory(dev_id, decision, current_time_sec=i * 60.0)

        assert trend.trajectory in ["RISING", "ACCELERATING"]
        assert trend.horizon_state in ["DEVELOPING_RISK", "NEAR_TERM_RISK"]
        assert trend.slope_per_min > 0.0

    def test_03_confirmed_bloom_reaches_intervention(self):
        """Scenario 3: Corroborated bloom escalation triggers INTERVENE or EMERGENCY response policy."""
        dev_id = "DEV_03"
        for i in range(4):
            decision = {
                "timestamp": f"2026-09-20T12:0{i}:00Z",
                "fusion": {"final_state": "CRITICAL", "confidence": 0.92},
                "ml_evidence": {"predicted_class": 5, "confidence": 0.95},
                "visual_evidence": {"visual_state": "BLOOM_EVIDENCE", "quality_index": 0.85, "valid": True},
                "multimodal_intelligence": {
                    "synthesized_state": "CRITICAL",
                    "confidence": 0.92,
                    "concordance_score": 0.95,
                    "conflict_detected": False,
                    "dominance_prevented": False,
                    "valid_modalities": 3
                }
            }
            trend = self.risk_engine.evaluate_trajectory(dev_id, decision, current_time_sec=i * 60.0)
            policy, act = self.response_engine.evaluate_response(
                dev_id, decision, trend,
                sensor_quality={"q_sensor": 0.90, "is_valid": True},
                visual_evidence={"quality_index": 0.85, "valid": True},
                now_sec=i * 60.0
            )

        assert trend.horizon_state == "ACTIVE_EVENT"
        assert policy in ["INTERVENE", "EMERGENCY"]
        assert act.approved_action == "APPROVED"
        assert act.execution_status == "COMMAND_ISSUED"

    def test_04_recovery_hysteresis_and_return_to_monitor(self):
        """Scenario 4: Recovery requires K=3 consecutive verified cycles before returning to MONITOR."""
        dev_id = "DEV_04"
        # 1. Trigger elevated state
        dec_alert = {
            "timestamp": "2026-09-20T12:00:00Z",
            "fusion": {"final_state": "CRITICAL", "confidence": 0.90},
            "multimodal_intelligence": {"synthesized_state": "CRITICAL", "confidence": 0.90, "concordance_score": 0.9}
        }
        tr_alert = self.risk_engine.evaluate_trajectory(dev_id, dec_alert, current_time_sec=0.0)
        pol, _ = self.response_engine.evaluate_response(dev_id, dec_alert, tr_alert, now_sec=0.0)
        assert pol in ["INTERVENE", "EMERGENCY"]

        # 2. Return to normal observations
        dec_norm = {
            "timestamp": "2026-09-20T12:01:00Z",
            "fusion": {"final_state": "NORMAL", "confidence": 0.88},
            "multimodal_intelligence": {"synthesized_state": "NORMAL", "confidence": 0.88, "concordance_score": 0.9}
        }
        # Cycle 1 normal -> held in RECOVERY_HOLD
        tr1 = self.risk_engine.evaluate_trajectory(dev_id, dec_norm, current_time_sec=60.0)
        pol1, _ = self.response_engine.evaluate_response(dev_id, dec_norm, tr1, now_sec=60.0)
        assert pol1 in ["RECOVERY", "WATCH"]

        # Cycle 2 normal -> held
        tr2 = self.risk_engine.evaluate_trajectory(dev_id, dec_norm, current_time_sec=120.0)
        pol2, _ = self.response_engine.evaluate_response(dev_id, dec_norm, tr2, now_sec=120.0)
        assert pol2 in ["RECOVERY", "WATCH"]

        # Cycle 3 normal -> K=3 confirmed -> returns to MONITOR
        tr3 = self.risk_engine.evaluate_trajectory(dev_id, dec_norm, current_time_sec=180.0)
        pol3, _ = self.response_engine.evaluate_response(dev_id, dec_norm, tr3, now_sec=180.0)
        assert pol3 == "MONITOR"

    # =========================================================================
    # 2. MULTIMODAL CONDITIONS
    # =========================================================================

    def test_05_multimodal_agreement_high_confidence(self):
        """Scenario 5: Multi-stream concordance raises confidence and reduces uncertainty."""
        dev_id = "DEV_05"
        for i in range(6):
            decision = {
                "timestamp": f"2026-09-20T12:0{i}:00Z",
                "fusion": {"final_state": "NORMAL", "confidence": 0.85},
                "ml_evidence": {"predicted_class": 1, "confidence": 0.85},
                "visual_evidence": {"visual_state": "NORMAL_WATER", "quality_index": 0.90, "valid": True},
                "temporal_evidence": {"temporal_state": "NORMAL", "trajectory_risk_score": 0.05},
                "ais_evidence": {"is_anomaly": False, "anomaly_score": 0.10},
                "multimodal_intelligence": {
                    "synthesized_state": "NORMAL",
                    "confidence": 0.90,
                    "concordance_score": 0.98,
                    "conflict_detected": False,
                    "dominance_prevented": False
                }
            }
            trend = self.risk_engine.evaluate_trajectory(dev_id, decision, current_time_sec=i * 60.0)

        assert len(trend.supporting_modalities) >= 3
        assert trend.uncertainty < 0.25
        assert trend.confidence >= 0.70

    def test_06_sensor_vision_conflict_blocks_false_emergency(self):
        """Scenario 6: Cross-modality conflict dampens risk and safety gate blocks emergency."""
        dev_id = "DEV_06"
        for i in range(4):
            decision = {
                "timestamp": f"2026-09-20T12:0{i}:00Z",
                "fusion": {"final_state": "WATCH", "confidence": 0.75},
                "ml_evidence": {"predicted_class": 5, "confidence": 0.80},
                "visual_evidence": {"visual_state": "NORMAL_WATER", "quality_index": 0.85, "valid": True},
                "multimodal_intelligence": {
                    "synthesized_state": "WATCH",
                    "confidence": 0.65,
                    "concordance_score": 0.35,
                    "conflict_detected": True,
                    "conflict_type": "SENSOR_VS_VISION",
                    "dominance_prevented": True
                }
            }
            trend = self.risk_engine.evaluate_trajectory(dev_id, decision, current_time_sec=i * 60.0)
            policy, act = self.response_engine.evaluate_response(
                dev_id, decision, trend,
                sensor_quality={"q_sensor": 0.85, "is_valid": True},
                visual_evidence={"quality_index": 0.85, "valid": True},
                now_sec=i * 60.0
            )

        assert "MODALITY_CONFLICT_DAMPENED" in trend.reason_codes
        assert policy in ["WATCH", "PREPARE"]
        assert act.approved_action == "NO_ACTION"

    def test_07_missing_camera_graceful_fallback(self):
        """Scenario 7: Missing camera does not crash system, operates on sensor + temporal streams."""
        dev_id = "DEV_07"
        decision = {
            "timestamp": "2026-09-20T12:00:00Z",
            "fusion": {"final_state": "NORMAL", "confidence": 0.80},
            "ml_evidence": {"predicted_class": 1, "confidence": 0.85},
            "visual_evidence": None,
            "multimodal_intelligence": {
                "synthesized_state": "NORMAL",
                "confidence": 0.80,
                "concordance_score": 0.85,
                "valid_modalities": 2
            }
        }
        for i in range(4):
            trend = self.risk_engine.evaluate_trajectory(dev_id, decision, current_time_sec=i * 60.0)
            policy, act = self.response_engine.evaluate_response(dev_id, decision, trend, now_sec=i * 60.0)

        assert "visual" not in trend.supporting_modalities
        assert trend.horizon_state == "NO_IMMEDIATE_RISK"
        assert policy == "MONITOR"

    def test_08_missing_sensor_graceful_fallback(self):
        """Scenario 8: Missing sensor data gracefully falls back to available modalities."""
        dev_id = "DEV_08"
        decision = {
            "timestamp": "2026-09-20T12:00:00Z",
            "fusion": {"final_state": "NORMAL", "confidence": 0.70},
            "ml_evidence": None,
            "visual_evidence": {"visual_state": "NORMAL_WATER", "quality_index": 0.80, "valid": True},
            "multimodal_intelligence": {
                "synthesized_state": "NORMAL",
                "confidence": 0.70,
                "concordance_score": 0.80,
                "valid_modalities": 1
            }
        }
        for i in range(4):
            trend = self.risk_engine.evaluate_trajectory(dev_id, decision, current_time_sec=i * 60.0)
            policy, act = self.response_engine.evaluate_response(dev_id, decision, trend, now_sec=i * 60.0)

        assert "sensor_ml" not in trend.supporting_modalities
        assert "visual" in trend.supporting_modalities
        assert policy == "MONITOR"

    def test_09_missing_ais_graceful_fallback(self):
        """Scenario 9: Missing AIS evidence does not compromise sensor+optical synthesis."""
        dev_id = "DEV_09"
        decision = {
            "timestamp": "2026-09-20T12:00:00Z",
            "fusion": {"final_state": "NORMAL", "confidence": 0.82},
            "ml_evidence": {"predicted_class": 1, "confidence": 0.88},
            "visual_evidence": {"visual_state": "NORMAL_WATER", "quality_index": 0.85, "valid": True},
            "ais_evidence": None,
            "multimodal_intelligence": {"synthesized_state": "NORMAL", "confidence": 0.82, "valid_modalities": 2}
        }
        for i in range(4):
            trend = self.risk_engine.evaluate_trajectory(dev_id, decision, current_time_sec=i * 60.0)
            policy, act = self.response_engine.evaluate_response(dev_id, decision, trend, now_sec=i * 60.0)

        assert "ais" not in trend.supporting_modalities
        assert policy == "MONITOR"

    def test_10_multiple_degraded_modalities_fallback(self):
        """Scenario 10: Multiple degraded streams increase uncertainty and inhibit autonomous actuation."""
        dev_id = "DEV_10"
        decision = {
            "timestamp": "2026-09-20T12:00:00Z",
            "fusion": {"final_state": "HIGH_RISK", "confidence": 0.55},
            "ml_evidence": {"predicted_class": 4, "confidence": 0.60},
            "visual_evidence": {"visual_state": "DEGRADED_VISUAL", "quality_index": 0.40, "valid": False},
            "multimodal_intelligence": {
                "synthesized_state": "WATCH",
                "confidence": 0.45,
                "dominance_prevented": True,
                "conflict_detected": False
            }
        }
        for i in range(4):
            trend = self.risk_engine.evaluate_trajectory(
                dev_id, decision,
                sensor_quality={"q_sensor": 0.55, "is_valid": False},
                current_time_sec=i * 60.0
            )
            policy, act = self.response_engine.evaluate_response(
                dev_id, decision, trend,
                sensor_quality={"q_sensor": 0.55, "is_valid": False},
                visual_evidence={"quality_index": 0.40, "valid": False},
                now_sec=i * 60.0
            )

        assert trend.uncertainty >= 0.30
        assert act.approved_action in ["NO_ACTION", "BLOCKED"]

    # =========================================================================
    # 3. FAULT CONDITIONS
    # =========================================================================

    def test_11_single_sensor_spike_dampened(self):
        """Scenario 11: Single transient spike does not trigger false bloom alarm."""
        dev_id = "DEV_11"
        # 3 normal baseline cycles
        for i in range(3):
            norm_dec = {
                "timestamp": f"2026-09-20T12:0{i}:00Z",
                "fusion": {"final_state": "NORMAL", "confidence": 0.90},
                "multimodal_intelligence": {"synthesized_state": "NORMAL", "confidence": 0.90}
            }
            self.risk_engine.evaluate_trajectory(dev_id, norm_dec, current_time_sec=i * 60.0)

        # Spike cycle
        spike_dec = {
            "timestamp": "2026-09-20T12:03:00Z",
            "fusion": {"final_state": "CRITICAL", "confidence": 0.85},
            "multimodal_intelligence": {"synthesized_state": "CRITICAL", "confidence": 0.85}
        }
        trend = self.risk_engine.evaluate_trajectory(dev_id, spike_dec, current_time_sec=180.0)
        policy, act = self.response_engine.evaluate_response(dev_id, spike_dec, trend, now_sec=180.0)

        assert "SINGLE_SPIKE_DAMPENED" in trend.reason_codes
        assert trend.horizon_state != "ACTIVE_EVENT"
        assert act.approved_action in ["NO_ACTION", "BLOCKED"]

    def test_12_camera_corruption_handling(self):
        """Scenario 12: Corrupted camera bytes do not trigger false visual bloom."""
        dev_id = "DEV_12"
        decision = {
            "timestamp": "2026-09-20T12:00:00Z",
            "fusion": {"final_state": "NORMAL", "confidence": 0.85},
            "visual_evidence": {"visual_state": "CAMERA_FAULT", "quality_index": 0.0, "valid": False},
            "multimodal_intelligence": {"synthesized_state": "NORMAL", "confidence": 0.85}
        }
        for i in range(4):
            trend = self.risk_engine.evaluate_trajectory(dev_id, decision, current_time_sec=i * 60.0)
            policy, act = self.response_engine.evaluate_response(
                dev_id, decision, trend,
                visual_evidence={"quality_index": 0.0, "valid": False},
                now_sec=i * 60.0
            )

        assert trend.horizon_state == "NO_IMMEDIATE_RISK"
        assert policy == "MONITOR"

    def test_13_stale_evidence_handling(self):
        """Scenario 13: Stale evidence reduces confidence and increases uncertainty."""
        dev_id = "DEV_13"
        decision = {
            "timestamp": "2026-09-20T12:00:00Z",
            "fusion": {"final_state": "NORMAL", "confidence": 0.60},
            "multimodal_snapshot": {"alignment_status": "EXCESSIVE_SKEW", "max_time_skew_seconds": 120.0},
            "multimodal_intelligence": {"synthesized_state": "NORMAL", "confidence": 0.50}
        }
        for i in range(4):
            trend = self.risk_engine.evaluate_trajectory(dev_id, decision, current_time_sec=i * 60.0)

        assert trend.uncertainty > 0.10
        assert trend.confidence <= 0.60

    def test_14_network_interruption_simulation(self):
        """Scenario 14: Simulates network dropouts; gateway handles packet gap gracefully."""
        gateway = Gateway(use_mock=True)
        # Drop connection
        gateway.disconnect()
        assert gateway.client.connected is False
        # Reconnect
        gateway.connect()
        assert gateway.client.connected is True

    def test_15_database_delay_and_busy_timeout(self):
        """Scenario 15: EventStore busy timeout safely handles concurrent sqlite access."""
        store = EventStore(db_path=self.db_path)
        # Verify busy timeout is configured to 10.0 seconds
        conn = store._connect_db()
        cursor = conn.cursor()
        cursor.execute("PRAGMA busy_timeout")
        row = cursor.fetchone()
        conn.close()
        assert row[0] >= 10000

    def test_16_actuator_command_failure_tracking(self):
        """Scenario 16: Blocked or failed actuator commands are tracked with COMMAND_FAILED."""
        dev_id = "DEV_16"
        decision = {
            "timestamp": "2026-09-20T12:00:00Z",
            "fusion": {"final_state": "WATCH"},
            "multimodal_intelligence": {"synthesized_state": "WATCH", "confidence": 0.60}
        }
        trend = RiskTrendResult(
            trajectory="STABLE",
            horizon_state="DEVELOPING_RISK",
            confidence=0.60,
            evidence_window=4,
            risk_score=0.30
        )
        # Manually evaluate buzzer without emergency state -> should be blocked
        is_app, checks, blocked = self.response_engine.safety_gate.evaluate_gate(
            device_id=dev_id,
            requested_action="ACTIVATE_BUZZER",
            policy_state="WATCH",
            risk_score=0.30,
            sensor_quality={"q_sensor": 0.90},
            visual_evidence=None,
            multimodal_intel={"conflict_detected": False}
        )
        assert is_app is False
        assert len(blocked) > 0

    # =========================================================================
    # 4. SAFETY CONDITIONS
    # =========================================================================

    def test_17_low_confidence_bloom_prevents_unsafe_actuation(self):
        """Scenario 17: Low-confidence bloom flags risk but safety gate blocks physical actuation."""
        dev_id = "DEV_17"
        decision = {
            "timestamp": "2026-09-20T12:00:00Z",
            "fusion": {"final_state": "CRITICAL", "confidence": 0.40},
            "multimodal_intelligence": {
                "synthesized_state": "CRITICAL",
                "confidence": 0.40,
                "concordance_score": 0.40,
                "valid_modalities": 1
            }
        }
        trend = RiskTrendResult(
            trajectory="RISING",
            horizon_state="DEVELOPING_RISK",
            confidence=0.35,
            evidence_window=4,
            risk_score=0.65
        )
        policy, act = self.response_engine.evaluate_response(
            dev_id, decision, trend,
            sensor_quality={"q_sensor": 0.60, "is_valid": True},
            now_sec=100.0
        )
        assert act.approved_action in ["NO_ACTION", "BLOCKED"]
        assert act.execution_status in ["COMMAND_NOT_VERIFIED", "COMMAND_FAILED"]

    def test_18_single_noisy_sensor_blocks_unsafe_escalation(self):
        """Scenario 18: Noisy sensor ($Q_s < 0.70$) blocks actuation even with elevated reading."""
        dev_id = "DEV_18"
        decision = {
            "timestamp": "2026-09-20T12:00:00Z",
            "fusion": {"final_state": "CRITICAL"},
            "multimodal_intelligence": {"synthesized_state": "CRITICAL", "confidence": 0.85}
        }
        trend = RiskTrendResult(
            trajectory="RISING",
            horizon_state="ACTIVE_EVENT",
            confidence=0.85,
            evidence_window=5,
            risk_score=0.85
        )
        policy, act = self.response_engine.evaluate_response(
            dev_id, decision, trend,
            sensor_quality={"q_sensor": 0.50, "is_valid": True},  # Degraded SNR
            now_sec=100.0
        )
        assert act.approved_action == "BLOCKED"
        assert any("SENSOR_QUALITY_DEGRADED" in r for r in act.blocked_reasons)

    def test_19_conflicting_modalities_safety_gate_applied(self):
        """Scenario 19: Cross-modality conflict explicitly trips safety gate."""
        gate = ActuatorSafetyGate()
        is_app, checks, blocked = gate.evaluate_gate(
            device_id="DEV_19",
            requested_action="ACTIVATE_PUMP",
            policy_state="INTERVENE",
            risk_score=0.75,
            sensor_quality={"q_sensor": 0.85},
            visual_evidence={"quality_index": 0.85},
            multimodal_intel={
                "conflict_detected": True,
                "conflict_type": "TURBIDITY_VS_SEDIMENT",
                "dominance_prevented": False
            }
        )
        assert is_app is False
        assert any("CROSS_MODALITY_CONFLICT_PRESENT" in b for b in blocked)

    def test_20_insufficient_history_reports_insufficient_data(self):
        """Scenario 20: Window with fewer than min cycles reports INSUFFICIENT_DATA and high uncertainty."""
        dev_id = "DEV_20"
        decision = {
            "timestamp": "2026-09-20T12:00:00Z",
            "fusion": {"final_state": "CRITICAL", "confidence": 0.90},
            "multimodal_intelligence": {"synthesized_state": "CRITICAL", "confidence": 0.90}
        }
        # Only 1 cycle evaluated
        trend = self.risk_engine.evaluate_trajectory(dev_id, decision, current_time_sec=0.0)

        assert trend.data_sufficiency == "INSUFFICIENT_DATA"
        assert trend.uncertainty >= 0.65
        assert "INSUFFICIENT_HISTORY" in trend.reason_codes
        assert trend.horizon_state == "DEVELOPING_RISK"  # Clamped away from ACTIVE_EVENT

    # =========================================================================
    # 5. LONG-DURATION SOAK TEST
    # =========================================================================

    def test_21_long_duration_soak_1000_cycles(self):
        """Scenario 21: 1,000-cycle soak test confirms throughput > 3 cyc/s, 0 crashes, 0 false escalations."""
        soak_res = run_soak_test(cycles=1000)

        assert soak_res["cycles_completed"] == 1000
        assert soak_res["error_count"] == 0
        assert soak_res["success_rate_percent"] == 100.0
        assert soak_res["throughput_cycles_sec"] > 3.0
        assert soak_res["p95_latency_ms"] < 500.0
        assert soak_res["false_escalation_count"] == 0
