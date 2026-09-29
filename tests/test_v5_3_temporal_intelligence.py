import os
import sys
import pytest
import datetime

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fusion.temporal_intelligence import (
    TemporalEnvironmentalEngine,
    TemporalTrajectoryResult,
    MetricTrend
)


class TestV53TemporalEnvironmentalIntelligence:
    """Comprehensive test suite for V5.3 Temporal Environmental Trend & Early Warning Engine."""

    def setup_method(self):
        self.engine = TemporalEnvironmentalEngine(window_size=12, max_window_age_sec=600.0)
        self.device_id = "AQUA_TEST_001"

    def test_01_cold_start_initialization(self):
        """Verifies cold-start gracefully yields NORMAL state with zero risk."""
        reading = {
            "timestamp": "2026-09-20T12:00:00Z",
            "temperature_c": 22.0,
            "ph": 7.4,
            "turbidity_ntu": 5.0,
            "dissolved_oxygen_mg_l": 8.0,
            "salinity_ppt": 0.2
        }
        res = self.engine.evaluate_telemetry(self.device_id, reading)
        assert res.temporal_state == "NORMAL"
        assert res.trajectory_risk_score == 0.0
        assert res.persistence_cycles == 0
        assert res.is_stable is True
        assert res.window_size_evaluated == 1

    def test_02_stable_ecosystem_baseline(self):
        """Verifies stable telemetry across 6 cycles maintains NORMAL state and near-zero slopes."""
        base_time = datetime.datetime(2026, 9, 20, 12, 0, 0)
        for i in range(6):
            ts = (base_time + datetime.timedelta(seconds=i * 10)).isoformat()
            reading = {
                "timestamp": ts,
                "temperature_c": 22.0 + (i % 2) * 0.05,
                "ph": 7.4 + (i % 2) * 0.02,
                "turbidity_ntu": 5.0 + (i % 2) * 0.1,
                "dissolved_oxygen_mg_l": 8.0 - (i % 2) * 0.05,
                "salinity_ppt": 0.2
            }
            res = self.engine.evaluate_telemetry(self.device_id, reading)

        assert res.temporal_state == "NORMAL"
        assert res.trajectory_risk_score < 0.20
        assert res.is_stable is True
        assert res.window_size_evaluated == 6
        assert abs(res.trend_slopes["ph_per_min"]) < 0.05

    def test_03_linear_slope_calculation(self):
        """Verifies exact linear slope math for controlled synthetic rates."""
        base_time = datetime.datetime(2026, 9, 20, 12, 0, 0)
        # Add 1.0 degree per 60 seconds (slope = 1.0 C/min)
        for i in range(7):
            ts = (base_time + datetime.timedelta(seconds=i * 10)).isoformat()
            reading = {
                "timestamp": ts,
                "temperature_c": 20.0 + (i * 10 / 60.0) * 1.0,
                "ph": 7.0,
                "turbidity_ntu": 5.0,
                "dissolved_oxygen_mg_l": 8.0,
                "salinity_ppt": 0.2
            }
            res = self.engine.evaluate_telemetry(self.device_id, reading)

        slope_min = res.trend_slopes["temperature_c_per_min"]
        assert pytest.approx(slope_min, abs=0.05) == 1.0

    def test_04_incubation_warming_triggers_watch(self):
        """Verifies water warming trend (+0.25 C/min) triggers WATCH state with incubation indicator."""
        base_time = datetime.datetime(2026, 9, 20, 12, 0, 0)
        res = None
        for i in range(4):
            ts = (base_time + datetime.timedelta(seconds=i * 10)).isoformat()
            reading = {
                "timestamp": ts,
                "temperature_c": 22.0 + (i * 10 / 60.0) * 0.30,  # +0.30 C/min warming
                "ph": 7.4,
                "turbidity_ntu": 5.0,
                "dissolved_oxygen_mg_l": 8.0,
                "salinity_ppt": 0.2
            }
            res = self.engine.evaluate_telemetry(self.device_id, reading)

        assert res.temporal_state == "WATCH"
        assert any("temperature warming" in ind for ind in res.lead_indicators)
        assert res.is_stable is False

    def test_05_coupled_eutrophication_triggers_early_warning(self):
        """Verifies accelerating pH + coupled DO + warming progression elevates to EARLY_WARNING."""
        base_time = datetime.datetime(2026, 9, 20, 12, 0, 0)
        states_seen = []
        res = None
        for i in range(6):
            ts = (base_time + datetime.timedelta(seconds=i * 10)).isoformat()
            reading = {
                "timestamp": ts,
                "temperature_c": 23.0 + i * 0.05,
                "ph": 7.5 + i * 0.12,  # Rapid pH rise
                "turbidity_ntu": 6.0 + i * 0.3,
                "dissolved_oxygen_mg_l": 8.0 + i * 0.15,  # Coupled DO rise
                "salinity_ppt": 0.2
            }
            res = self.engine.evaluate_telemetry(self.device_id, reading)
            states_seen.append(res.temporal_state)

        assert "EARLY_WARNING" in states_seen or "HIGH_RISK" in states_seen
        assert res.persistence_cycles >= 2
        assert res.trajectory_risk_score >= 0.30
        assert any("pH" in ind for ind in res.lead_indicators)

    def test_06_persistent_trajectory_triggers_high_risk_and_bloom_confirmed(self):
        """Verifies persistent, accelerating eutrophication over 8 cycles triggers HIGH_RISK and BLOOM_CONFIRMED."""
        base_time = datetime.datetime(2026, 9, 20, 12, 0, 0)
        res = None
        for i in range(10):
            ts = (base_time + datetime.timedelta(seconds=i * 10)).isoformat()
            reading = {
                "timestamp": ts,
                "temperature_c": 24.0 + i * 0.10,
                "ph": 8.0 + i * 0.15,  # Crossing 9.0
                "turbidity_ntu": 15.0 + i * 3.5,  # Crossing 40 NTU
                "dissolved_oxygen_mg_l": 9.0 + i * 0.20,
                "salinity_ppt": 0.2
            }
            res = self.engine.evaluate_telemetry(self.device_id, reading)

        assert res.temporal_state in ["HIGH_RISK", "BLOOM_CONFIRMED"]
        assert res.persistence_cycles >= 4
        assert res.trajectory_risk_score >= 0.70

    def test_07_transient_single_spike_suppression(self):
        """Verifies an isolated single-cycle anomaly does not reach EARLY_WARNING due to persistence check."""
        base_time = datetime.datetime(2026, 9, 20, 12, 0, 0)
        # Establish stable history
        for i in range(5):
            ts = (base_time + datetime.timedelta(seconds=i * 10)).isoformat()
            self.engine.evaluate_telemetry(self.device_id, {
                "timestamp": ts, "temperature_c": 22.0, "ph": 7.4, "turbidity_ntu": 5.0, "dissolved_oxygen_mg_l": 8.0, "salinity_ppt": 0.2
            })

        # Inject single instantaneous spike
        spike_ts = (base_time + datetime.timedelta(seconds=50)).isoformat()
        spike_res = self.engine.evaluate_telemetry(self.device_id, {
            "timestamp": spike_ts, "temperature_c": 22.0, "ph": 9.2, "turbidity_ntu": 5.0, "dissolved_oxygen_mg_l": 8.0, "salinity_ppt": 0.2
        })

        # Persistence is only 1, so it cannot be EARLY_WARNING or HIGH_RISK
        assert spike_res.persistence_cycles <= 1
        assert spike_res.temporal_state in ["NORMAL", "WATCH"]

    def test_08_sensor_quality_degradation_discounts_threat(self):
        """Verifies poor sensor quality (Q_sensor = 0.20) dampens trajectory risk score."""
        base_time = datetime.datetime(2026, 9, 20, 12, 0, 0)
        engine_good = TemporalEnvironmentalEngine()
        engine_poor = TemporalEnvironmentalEngine()

        res_good, res_poor = None, None
        for i in range(4):
            ts = (base_time + datetime.timedelta(seconds=i * 10)).isoformat()
            reading = {
                "timestamp": ts, "temperature_c": 22.0 + i * 0.1, "ph": 7.5 + i * 0.15, "turbidity_ntu": 10.0 + i * 1.0, "dissolved_oxygen_mg_l": 8.0, "salinity_ppt": 0.2
            }
            res_good = engine_good.evaluate_telemetry("D1", reading, q_sensor=1.0)
            res_poor = engine_poor.evaluate_telemetry("D2", reading, q_sensor=0.20)

        assert res_poor.trajectory_risk_score < res_good.trajectory_risk_score

    def test_09_device_reset_and_isolation(self):
        """Verifies resetting one device does not affect another device's buffer."""
        base_time = datetime.datetime(2026, 9, 20, 12, 0, 0)
        for i in range(4):
            ts = (base_time + datetime.timedelta(seconds=i * 10)).isoformat()
            self.engine.evaluate_telemetry("DEV_A", {"timestamp": ts, "temperature_c": 22.0 + i, "ph": 7.5, "turbidity_ntu": 5.0, "dissolved_oxygen_mg_l": 8.0, "salinity_ppt": 0.2})
            self.engine.evaluate_telemetry("DEV_B", {"timestamp": ts, "temperature_c": 25.0, "ph": 7.0, "turbidity_ntu": 5.0, "dissolved_oxygen_mg_l": 8.0, "salinity_ppt": 0.2})

        assert len(self.engine.device_buffers["DEV_A"]) == 4
        self.engine.reset_device("DEV_A")
        assert len(self.engine.device_buffers["DEV_A"]) == 0
        assert len(self.engine.device_buffers["DEV_B"]) == 4

    def test_10_to_dict_serialization(self):
        """Verifies TemporalTrajectoryResult serializes cleanly to JSON-compatible dictionary."""
        reading = {"timestamp": "2026-09-20T12:00:00Z", "temperature_c": 22.0, "ph": 7.4, "turbidity_ntu": 5.0, "dissolved_oxygen_mg_l": 8.0, "salinity_ppt": 0.2}
        res = self.engine.evaluate_telemetry(self.device_id, reading)
        d = res.to_dict()
        assert isinstance(d, dict)
        assert d["temporal_state"] == "NORMAL"
        assert "trend_slopes" in d
        assert "lead_indicators" in d
