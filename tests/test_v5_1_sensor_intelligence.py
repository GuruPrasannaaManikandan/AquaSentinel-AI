import pytest
import datetime
import numpy as np
from src.iot.sensor_quality import (
    SensorQualityEvaluator,
    SensorQualityResult,
    SensorQualityComponent
)
from src.iot.sensor_simulator import AquaticSensorSimulator
from src.iot.edge_validation import EdgeValidator


class TestV51SensorIntelligence:
    """
    Comprehensive test suite for V5.1 Advanced Sensor Quality & Edge Intelligence.
    Verifies rate-of-change, statistical deviation (MAD), noise, drift, cross-sensor
    plausibility, freshness, bounded determinism, and V4 backward compatibility.
    """

    @pytest.fixture
    def evaluator(self):
        return SensorQualityEvaluator()

    @pytest.fixture
    def simulator(self):
        return AquaticSensorSimulator(ecosystem_type="Freshwater", random_seed=42)

    # 1. Normal Sensor Quality
    def test_normal_sensor_quality(self, evaluator, simulator):
        evaluator.reset_history()
        results = []
        base_time = datetime.datetime(2026, 8, 26, 12, 0, 0)
        for i in range(6):
            t = base_time + datetime.timedelta(seconds=i * 10)
            reading = simulator.generate_reading(scenario="NORMAL", timestamp=t)
            res = evaluator.evaluate(reading, timestamp=t, device_id="TEST_DEV")
            results.append(res)

        last_res = results[-1]
        assert 0.80 <= last_res.overall_quality <= 1.0
        assert last_res.validation_state in ["RELIABLE", "DEGRADED"]
        assert last_res.stale_data_status == "FRESH"
        assert len(last_res.components) == 5
        for s_name, comp in last_res.components.items():
            assert comp.quality_score >= 0.80
            assert comp.status == "OK"

    # 2. Rate of Change Violation
    def test_rate_of_change_violation(self, evaluator):
        evaluator.reset_history()
        t0 = datetime.datetime(2026, 8, 26, 12, 0, 0)
        t1 = t0 + datetime.timedelta(seconds=10)

        r0 = {"temperature_c": 22.0, "ph": 7.2, "turbidity_ntu": 3.0, "salinity_ppt": 0.2, "dissolved_oxygen_mg_l": 8.0}
        # Rapid jump in pH: delta = 2.4 in 10s -> rate = 0.24 units/s > max limit 0.10
        r1 = {"temperature_c": 22.0, "ph": 9.6, "turbidity_ntu": 3.0, "salinity_ppt": 0.2, "dissolved_oxygen_mg_l": 8.0}

        evaluator.evaluate(r0, timestamp=t0, device_id="DEV_RATE")
        res1 = evaluator.evaluate(r1, timestamp=t1, device_id="DEV_RATE")

        ph_comp = res1.components["ph"]
        assert ph_comp.rate_of_change is not None
        assert ph_comp.rate_of_change >= 0.20
        assert ph_comp.quality_score < 0.70
        assert any("rate-of-change" in r.lower() for r in ph_comp.reasons)
        assert res1.overall_quality < 0.85

    # 3. pH Spike
    def test_pH_spike(self, evaluator, simulator):
        evaluator.reset_history()
        simulator.reset_seed(42)
        base_t = datetime.datetime(2026, 8, 26, 12, 0, 0)
        # Step 1: Normal
        r0 = simulator.generate_reading(scenario="NORMAL", timestamp=base_t)
        evaluator.evaluate(r0, timestamp=base_t, device_id="DEV_SPIKE")

        # Step 2: Sudden Spike
        t1 = base_t + datetime.timedelta(seconds=10)
        r1 = simulator.generate_reading(scenario="SUDDEN_SPIKE", timestamp=t1)
        res1 = evaluator.evaluate(r1, timestamp=t1, device_id="DEV_SPIKE")

        assert res1.components["ph"].raw_value == 9.8
        assert res1.components["ph"].quality_score < 0.60
        assert any("rate-of-change" in r.lower() for r in res1.components["ph"].reasons)
        assert res1.overall_quality < 0.85

    # 4. Temperature Spike
    def test_temperature_spike(self, evaluator):
        evaluator.reset_history()
        t0 = datetime.datetime(2026, 8, 26, 12, 0, 0)
        t1 = t0 + datetime.timedelta(seconds=10)

        r0 = {"temperature_c": 22.0, "ph": 7.4, "turbidity_ntu": 3.0, "salinity_ppt": 0.2, "dissolved_oxygen_mg_l": 8.0}
        # Jump from 22°C to 34°C in 10s -> rate = 1.2°C/s > 0.25 max physical limit
        r1 = {"temperature_c": 34.0, "ph": 7.4, "turbidity_ntu": 3.0, "salinity_ppt": 0.2, "dissolved_oxygen_mg_l": 8.0}

        evaluator.evaluate(r0, timestamp=t0, device_id="DEV_TEMP")
        res1 = evaluator.evaluate(r1, timestamp=t1, device_id="DEV_TEMP")

        temp_comp = res1.components["temperature_c"]
        assert temp_comp.rate_of_change >= 1.0
        assert temp_comp.quality_score < 0.70
        assert any("rate-of-change" in r.lower() for r in temp_comp.reasons)

    # 5. Turbidity Spike
    def test_turbidity_spike(self, evaluator):
        evaluator.reset_history()
        t0 = datetime.datetime(2026, 8, 26, 12, 0, 0)
        t1 = t0 + datetime.timedelta(seconds=10)

        r0 = {"temperature_c": 22.0, "ph": 7.4, "turbidity_ntu": 3.0, "salinity_ppt": 0.2, "dissolved_oxygen_mg_l": 8.0}
        # Turbidity jumps from 3.0 to 120.0 NTU in 10s -> rate = 11.7 NTU/s > 8.0 max
        r1 = {"temperature_c": 22.0, "ph": 7.4, "turbidity_ntu": 120.0, "salinity_ppt": 0.2, "dissolved_oxygen_mg_l": 8.0}

        evaluator.evaluate(r0, timestamp=t0, device_id="DEV_TURB")
        res1 = evaluator.evaluate(r1, timestamp=t1, device_id="DEV_TURB")

        turb_comp = res1.components["turbidity_ntu"]
        assert turb_comp.rate_of_change > 8.0
        assert turb_comp.quality_score < 0.70
        assert any("rate-of-change" in r.lower() for r in turb_comp.reasons)

    # 6. Noisy Sensor
    def test_noisy_sensor(self, evaluator, simulator):
        evaluator.reset_history()
        simulator.reset_seed(42)
        base_t = datetime.datetime(2026, 8, 26, 12, 0, 0)
        last_res = None

        for i in range(8):
            t = base_t + datetime.timedelta(seconds=i * 10)
            reading = simulator.generate_reading(scenario="NOISY_SENSOR", timestamp=t)
            last_res = evaluator.evaluate(reading, timestamp=t, device_id="DEV_NOISE")

        ph_comp = last_res.components["ph"]
        assert ph_comp.is_noisy is True or any("noise" in r.lower() for r in ph_comp.reasons)
        assert ph_comp.quality_score < 0.85

    # 7. Sensor Drift
    def test_sensor_drift(self, evaluator, simulator):
        evaluator.reset_history()
        simulator.reset_seed(42)
        base_t = datetime.datetime(2026, 8, 26, 12, 0, 0)
        last_res = None

        for i in range(8):
            t = base_t + datetime.timedelta(seconds=i * 10)
            reading = simulator.generate_reading(scenario="SENSOR_DRIFT", timestamp=t)
            last_res = evaluator.evaluate(reading, timestamp=t, device_id="DEV_DRIFT")

        ph_comp = last_res.components["ph"]
        assert ph_comp.is_drifting is True or any("drift" in r.lower() for r in ph_comp.reasons)

    # 8. Stuck Sensor
    def test_stuck_sensor(self, evaluator, simulator):
        evaluator.reset_history()
        simulator.reset_seed(42)
        base_t = datetime.datetime(2026, 8, 26, 12, 0, 0)
        last_res = None

        for i in range(7):
            t = base_t + datetime.timedelta(seconds=i * 10)
            reading = simulator.generate_reading(scenario="STUCK_SENSOR", timestamp=t)
            last_res = evaluator.evaluate(reading, timestamp=t, device_id="DEV_STUCK")

        assert any(comp.is_stuck for comp in last_res.components.values())
        assert last_res.stale_data_status == "FROZEN"
        assert last_res.overall_quality <= 0.60

    # 9. Missing Sensor
    def test_missing_sensor(self, evaluator, simulator):
        evaluator.reset_history()
        base_t = datetime.datetime(2026, 8, 26, 12, 0, 0)
        reading = simulator.generate_reading(scenario="MISSING_SENSOR", timestamp=base_t)
        res = evaluator.evaluate(reading, timestamp=base_t, device_id="DEV_MISS")

        ph_comp = res.components["ph"]
        assert ph_comp.is_missing is True
        assert ph_comp.quality_score == 0.0
        assert ph_comp.status == "FAULT"
        assert res.overall_quality < 0.85
        assert "PH_MISSING" in res.anomaly_flags

    # 10. Stale Sensor Data
    def test_stale_sensor(self, evaluator):
        evaluator.reset_history()
        t0 = datetime.datetime(2026, 8, 26, 12, 0, 0)
        # Gap of 90 seconds (> 45s max_stale threshold)
        t1 = t0 + datetime.timedelta(seconds=90)

        r = {"temperature_c": 22.0, "ph": 7.4, "turbidity_ntu": 3.0, "salinity_ppt": 0.2, "dissolved_oxygen_mg_l": 8.0}
        evaluator.evaluate(r, timestamp=t0, device_id="DEV_STALE")
        res1 = evaluator.evaluate(r, timestamp=t1, device_id="DEV_STALE")

        assert res1.stale_data_status == "STALE"
        assert res1.metadata["freshness_factor"] < 1.0
        assert res1.overall_quality < 0.85

    # 11. Cross Sensor Inconsistency
    def test_cross_sensor_inconsistency(self, evaluator, simulator):
        evaluator.reset_history()
        base_t = datetime.datetime(2026, 8, 26, 12, 0, 0)
        reading = simulator.generate_reading(scenario="CROSS_SENSOR_INCONSISTENCY", timestamp=base_t)
        res = evaluator.evaluate(reading, timestamp=base_t, device_id="DEV_CROSS")

        assert res.cross_sensor_consistency < 1.0
        assert len(res.cross_sensor_issues) > 0
        assert any("implausible" in issue.lower() or "anoxic" in issue.lower() for issue in res.cross_sensor_issues)

    # 12. Legitimate Environmental Change
    def test_legitimate_environmental_change(self, evaluator, simulator):
        evaluator.reset_history()
        simulator.reset_seed(42)
        base_t = datetime.datetime(2026, 8, 26, 12, 0, 0)
        results = []

        for i in range(5):
            t = base_t + datetime.timedelta(seconds=i * 10)
            reading = simulator.generate_reading(scenario="LEGITIMATE_ENVIRONMENTAL_CHANGE", timestamp=t)
            res = evaluator.evaluate(reading, timestamp=t, device_id="DEV_LEGIT")
            results.append(res)

        last_res = results[-1]
        # System should NOT mark this as FAULT because all parameters shift together in biological coupling
        assert last_res.validation_state in ["RELIABLE", "DEGRADED"]
        assert last_res.overall_quality >= 0.70
        assert last_res.cross_sensor_consistency == 1.0

    # 13. Quality Score Strictly Bounded
    def test_quality_bounds(self, evaluator):
        evaluator.reset_history()
        rng = np.random.default_rng(12345)
        base_t = datetime.datetime(2026, 8, 26, 12, 0, 0)

        for i in range(200):
            t = base_t + datetime.timedelta(seconds=i * 10)
            # Randomized adversarial values including out of bounds, negatives, NaNs
            reading = {
                "temperature_c": float(rng.uniform(-20.0, 80.0)) if i % 10 != 0 else None,
                "ph": float(rng.uniform(-5.0, 20.0)) if i % 15 != 0 else None,
                "turbidity_ntu": float(rng.uniform(-10.0, 1000.0)),
                "salinity_ppt": float(rng.uniform(-5.0, 100.0)),
                "dissolved_oxygen_mg_l": float(rng.uniform(-2.0, 40.0))
            }
            res = evaluator.evaluate(reading, timestamp=t, device_id="DEV_BOUNDS")
            assert 0.0 <= res.overall_quality <= 1.0, f"Q_sensor out of bounds: {res.overall_quality}"
            assert 0.0 <= res.cross_sensor_consistency <= 1.0
            for comp in res.components.values():
                assert 0.0 <= comp.quality_score <= 1.0

    # 14. Determinism
    def test_quality_determinism(self, evaluator, simulator):
        simulator.reset_seed(999)
        base_t = datetime.datetime(2026, 8, 26, 12, 0, 0)
        readings = [simulator.generate_reading(scenario="NORMAL", timestamp=base_t + datetime.timedelta(seconds=i * 10)) for i in range(5)]

        evaluator.reset_history()
        run1 = [evaluator.evaluate(r, timestamp=r["timestamp"], device_id="DEV_DET").overall_quality for r in readings]

        evaluator.reset_history()
        run2 = [evaluator.evaluate(r, timestamp=r["timestamp"], device_id="DEV_DET").overall_quality for r in readings]

        assert run1 == run2, "Evaluator output is not deterministic across identical inputs"

    # 15. Quality Explanation Format Summary
    def test_quality_explanation(self, evaluator, simulator):
        evaluator.reset_history()
        base_t = datetime.datetime(2026, 8, 26, 12, 0, 0)
        reading = simulator.generate_reading(scenario="CROSS_SENSOR_INCONSISTENCY", timestamp=base_t)
        res = evaluator.evaluate(reading, timestamp=base_t, device_id="DEV_EXP")

        summary = res.format_summary()
        assert "V5.1 SENSOR QUALITY REPORT" in summary
        assert "Overall Quality (Q_sensor):" in summary
        assert "temperature_c" in summary
        assert "ph" in summary
        assert "Cross-Sensor Consistency Warnings:" in summary

    # 16. Backward Compatibility with V4 EdgeValidator
    def test_v4_backward_compatibility(self, simulator):
        val = EdgeValidator()
        reading = simulator.generate_reading(scenario="NORMAL")

        # Legacy 3-tuple call
        ret = val.validate(reading)
        assert isinstance(ret, tuple)
        assert len(ret) == 3
        is_valid, errors, health = ret
        assert is_valid is True
        assert errors == []
        assert health == "OK"

        # New V5.1 4-tuple call
        ret4 = val.validate_with_quality(reading)
        assert isinstance(ret4, tuple)
        assert len(ret4) == 4
        is_valid, errors, health, q_res = ret4
        assert is_valid is True
        assert isinstance(q_res, SensorQualityResult)
        assert 0.0 <= q_res.overall_quality <= 1.0
