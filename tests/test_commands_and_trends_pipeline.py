import os
import sys
import pytest
import datetime
from typing import Dict, Any

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backend.services import BackendService
from src.fusion.temporal_intelligence import (
    TemporalEnvironmentalEngine,
    TemporalTrajectoryResult
)
from src.iot.event_store import EventStore


class TestCommandsAndTrendsPipeline:
    """
    Exhaustive verification suite for Actuator Command Overrides,
    physical sensor data mapping, missing sensor semantics, and trend slope calculations.
    """

    def setup_method(self):
        self.service = BackendService.get_instance()
        self.device_id = "AQUA_FRESH_001"
        self.engine = TemporalEnvironmentalEngine(window_size=12, max_window_age_sec=600.0)

    # =========================================================================
    # PHASE 1 & 2: COMMAND EXECUTION MATRIX
    # =========================================================================

    def test_01_command_request_reading(self):
        """Verifies REQUEST_READING triggers immediate acquisition and returns COMMAND_COMPLETED."""
        res = self.service.send_device_command(self.device_id, "REQUEST_READING", {})
        assert res.get("status") == "COMMAND_COMPLETED"
        assert res.get("action") == "REQUEST_READING"
        assert "Fresh physical sensor reading acquisition triggered" in res.get("message", "")

    def test_02_command_set_sampling_interval_valid_and_invalid(self):
        """Verifies SET_SAMPLING_INTERVAL validates bounds (2 to 300s) and updates scheduler."""
        # Valid intervals
        res = self.service.send_device_command(self.device_id, "SET_SAMPLING_INTERVAL", {"interval": 5})
        assert res.get("status") == "COMMAND_COMPLETED"
        assert res.get("interval_sec") == 5

        # Invalid intervals (< 2 or > 300) must raise ValueError
        with pytest.raises(ValueError, match="Invalid sampling interval"):
            self.service.send_device_command(self.device_id, "SET_SAMPLING_INTERVAL", {"interval": 1})

        with pytest.raises(ValueError, match="Invalid sampling interval"):
            self.service.send_device_command(self.device_id, "SET_SAMPLING_INTERVAL", {"interval": 999})

    def test_03_command_activate_and_deactivate_buzzer(self):
        """Verifies ACTIVATE_BUZZER sets GPIO14 HIGH and DEACTIVATE_BUZZER sets GPIO14 LOW."""
        res_act = self.service.send_device_command(self.device_id, "ACTIVATE_BUZZER", {})
        assert res_act.get("status") == "COMMAND_COMPLETED"
        assert res_act.get("pin") == "GPIO14"
        assert res_act.get("state") == "HIGH"

        res_deact = self.service.send_device_command(self.device_id, "DEACTIVATE_BUZZER", {})
        assert res_deact.get("status") == "COMMAND_COMPLETED"
        assert res_deact.get("pin") == "GPIO14"
        assert res_deact.get("state") == "LOW"

    def test_04_command_activate_and_deactivate_relay(self):
        """Verifies ACTIVATE_RELAY and DEACTIVATE_RELAY affect GPIO19 electrical switching with NO pump claim."""
        res_act = self.service.send_device_command(self.device_id, "ACTIVATE_RELAY", {})
        assert res_act.get("status") == "COMMAND_COMPLETED"
        assert res_act.get("pin") == "GPIO19"
        assert res_act.get("state") == "HIGH"
        assert "pump not connected" in res_act.get("message", "").lower()

        res_deact = self.service.send_device_command(self.device_id, "DEACTIVATE_RELAY", {})
        assert res_deact.get("status") == "COMMAND_COMPLETED"
        assert res_deact.get("pin") == "GPIO19"
        assert res_deact.get("state") == "LOW"

    def test_05_command_pin_diagnostics(self):
        """Verifies PIN_DIAGNOSTICS reports actual GPIOs and explicitly flags missing sensors."""
        res = self.service.send_device_command(self.device_id, "PIN_DIAGNOSTICS", {})
        assert res.get("status") == "COMMAND_COMPLETED"
        pins = res.get("pins", {})
        assert pins.get("buzzer") == "GPIO14"
        assert pins.get("relay") == "GPIO19"
        assert "GPIO32" in pins.get("ph", "")
        assert "GPIO34" in pins.get("turbidity", "")
        assert "PHYSICALLY DISCONNECTED" in pins.get("ds18b20", "")
        assert pins.get("dissolved_oxygen") == "NOT AVAILABLE"
        assert pins.get("salinity") == "NOT AVAILABLE"

    def test_06_command_restart_device_safe(self):
        """Verifies RESTART_DEVICE returns COMMAND_COMPLETED safely."""
        res = self.service.send_device_command(self.device_id, "RESTART_DEVICE", {})
        assert res.get("status") == "COMMAND_COMPLETED"
        assert "Controlled device restart command processed safely" in res.get("message", "")

    # =========================================================================
    # PHASE 4 & 6: SENSOR DATA MAPPING & CANONICAL SCHEMA
    # =========================================================================

    def test_07_physical_sensor_telemetry_mapping(self):
        """Verifies real telemetry preserves physical pH (GPIO32) and Turbidity (GPIO34) while missing sensors are None."""
        raw_esp32_packet = {
            "device_id": self.device_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "provenance_timestamp": None,
            "location": {"latitude": None, "longitude": None},
            "sensors": {
                "temperature_c": None,
                "salinity_ppt": None,
                "ph": 28.87,
                "turbidity_ntu": 0.40,
                "dissolved_oxygen_mg_l": None
            },
            "device_health": {
                "wifi_connected": False,
                "mqtt_connected": True,
                "sensor_status": "OK"
            }
        }
        # Ingest into event store
        self.service.event_store.log_telemetry(raw_esp32_packet)

        # Retrieve latest
        latest = self.service.event_store.get_latest_telemetry(self.device_id)
        assert latest is not None
        assert latest["ph"] == 28.87
        assert latest["turbidity_ntu"] == 0.40
        assert latest["temperature_c"] is None
        assert latest["dissolved_oxygen_mg_l"] is None
        assert latest["salinity_ppt"] is None

    # =========================================================================
    # PHASE 7, 8, 9, 10: TREND ENGINE NULL & CHRONOLOGICAL SEMANTICS
    # =========================================================================

    def test_08_trend_slopes_for_physical_and_missing_sensors(self):
        """
        Verifies trend regression:
        - Real physical pH & turbidity voltage produce numeric slopes
        - Missing sensors (temperature, DO, salinity) yield strictly None (never 0.0 or synthetic slopes)
        """
        base_time = datetime.datetime(2026, 9, 29, 12, 0, 0)
        engine = TemporalEnvironmentalEngine(window_size=12, max_window_age_sec=600.0)

        # Feed 5 chronological packets with real physical profile:
        # pH slowly drifting, turbidity voltage slightly dropping, missing sensors as None
        for i in range(5):
            ts = (base_time + datetime.timedelta(seconds=i * 5)).isoformat()
            sample = {
                "timestamp": ts,
                "ph": 28.87 - (i * 0.02),
                "turbidity_voltage": 0.40 - (i * 0.01),
                "turbidity_ntu": 0.40 - (i * 0.01),
                "temperature_c": None,
                "dissolved_oxygen_mg_l": None,
                "salinity_ppt": None
            }
            res = engine.evaluate_telemetry("AQUA_TEST_PHYSICAL", sample)

        # pH trend must be negative numeric slope
        assert res.trend_slopes["ph_per_min"] is not None
        assert res.trend_slopes["ph_per_min"] < 0.0

        # Turbidity voltage trend must be negative numeric slope
        assert res.trend_slopes["turbidity_voltage_per_min"] is not None
        assert res.trend_slopes["turbidity_voltage_per_min"] < 0.0

        # Missing sensors MUST BE None (N/A) - never 0.0 or synthetic
        assert res.trend_slopes["temperature_c_per_min"] is None
        assert res.trend_slopes["dissolved_oxygen_mg_l_per_min"] is None
        assert res.trend_slopes["salinity_ppt_per_min"] is None

        # Verify MetricTrend objects also reflect None
        assert res.metric_trends["temperature_c"]["slope_per_min"] is None
        assert res.metric_trends["dissolved_oxygen_mg_l"]["slope_per_min"] is None
        assert res.metric_trends["salinity_ppt"]["slope_per_min"] is None

    def test_09_trend_does_not_convert_null_to_zero(self):
        """Verifies that null is NEVER treated as 0.0 reading."""
        engine = TemporalEnvironmentalEngine(window_size=12, max_window_age_sec=600.0)
        base_time = datetime.datetime(2026, 9, 29, 12, 0, 0)
        for i in range(3):
            ts = (base_time + datetime.timedelta(seconds=i * 5)).isoformat()
            sample = {
                "timestamp": ts,
                "ph": 28.87,
                "turbidity_voltage": 0.40,
                "temperature_c": None,
                "dissolved_oxygen_mg_l": None,
                "salinity_ppt": None
            }
            res = engine.evaluate_telemetry("AQUA_TEST_NULLS", sample)

        # Rate of change for missing sensors must be None, not 0.0
        assert res.rates_of_change["temperature_c_roc"] is None
        assert res.rates_of_change["dissolved_oxygen_mg_l_roc"] is None

    def test_10_chronological_ordering_enforced(self):
        """Verifies that sliding window preserves chronological order."""
        engine = TemporalEnvironmentalEngine(window_size=12, max_window_age_sec=600.0)
        base_time = datetime.datetime(2026, 9, 29, 12, 0, 0)

        # Add in order
        t1 = (base_time + datetime.timedelta(seconds=0)).isoformat()
        t2 = (base_time + datetime.timedelta(seconds=10)).isoformat()
        engine.evaluate_telemetry("AQUA_CHRONO", {"timestamp": t1, "ph": 28.80, "turbidity_voltage": 0.40})
        res2 = engine.evaluate_telemetry("AQUA_CHRONO", {"timestamp": t2, "ph": 28.90, "turbidity_voltage": 0.42})

        # From t1 to t2, pH rose by 0.10 in 10 sec -> +0.60 / min
        slope = res2.trend_slopes["ph_per_min"]
        assert slope is not None
        assert pytest.approx(slope, 0.01) == 0.60
