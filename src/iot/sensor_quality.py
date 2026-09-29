import os
import json
import math
import logging
import datetime
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Tuple, Union

logger = logging.getLogger("SensorQuality")


@dataclass
class SensorQualityComponent:
    """
    Quality evaluation for an individual physical sensor stream.
    """
    sensor_name: str
    raw_value: Optional[float]
    quality_score: float = 1.0
    status: str = "OK"  # "OK", "DEGRADED", "SUSPICIOUS", "FAULT"
    rate_of_change: Optional[float] = None  # units / second
    z_score: Optional[float] = None
    is_outlier: bool = False
    is_noisy: bool = False
    is_drifting: bool = False
    is_stuck: bool = False
    is_missing: bool = False
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sensor_name": self.sensor_name,
            "raw_value": self.raw_value,
            "quality_score": round(float(self.quality_score), 4),
            "status": self.status,
            "rate_of_change": round(float(self.rate_of_change), 4) if self.rate_of_change is not None else None,
            "z_score": round(float(self.z_score), 3) if self.z_score is not None else None,
            "is_outlier": self.is_outlier,
            "is_noisy": self.is_noisy,
            "is_drifting": self.is_drifting,
            "is_stuck": self.is_stuck,
            "is_missing": self.is_missing,
            "reasons": list(self.reasons)
        }


@dataclass
class SensorQualityResult:
    """
    Aggregated multi-sensor quality evaluation contract for V5.1.
    """
    overall_quality: float  # Q_sensor in [0.0, 1.0]
    validation_state: str   # "RELIABLE", "DEGRADED", "SUSPICIOUS", "FAULT"
    timestamp: str
    components: Dict[str, SensorQualityComponent] = field(default_factory=dict)
    anomaly_flags: List[str] = field(default_factory=list)
    reason_codes: List[str] = field(default_factory=list)
    cross_sensor_consistency: float = 1.0
    cross_sensor_issues: List[str] = field(default_factory=list)
    stale_data_status: str = "FRESH"  # "FRESH", "STALE", "FROZEN", "MISSING"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_quality": round(float(self.overall_quality), 4),
            "q_sensor": round(float(self.overall_quality), 4),
            "validation_state": self.validation_state,
            "quality_state": self.validation_state,
            "timestamp": self.timestamp,
            "components": {k: v.to_dict() for k, v in self.components.items()},
            "anomaly_flags": list(self.anomaly_flags),
            "reason_codes": list(self.reason_codes),
            "degradation_reasons": list(self.reason_codes),
            "cross_sensor_consistency": round(float(self.cross_sensor_consistency), 4),
            "cross_sensor_issues": list(self.cross_sensor_issues),
            "stale_data_status": self.stale_data_status,
            "metadata": dict(self.metadata)
        }

    def format_summary(self) -> str:
        """Generates a human-readable diagnostic report."""
        lines = [
            "=" * 45,
            f"V5.1 SENSOR QUALITY REPORT [{self.timestamp}]",
            f"Overall Quality (Q_sensor): {self.overall_quality:.2f} ({self.validation_state})",
            f"Cross-Sensor Consistency:  {self.cross_sensor_consistency:.2f}",
            f"Data Freshness Status:     {self.stale_data_status}",
            "-" * 45
        ]
        for name, comp in self.components.items():
            val_str = f"{comp.raw_value:.2f}" if comp.raw_value is not None else "None"
            lines.append(f"• {name:<22}: Val={val_str:<7} Q={comp.quality_score:.2f} [{comp.status}]")
            if comp.reasons:
                for r in comp.reasons:
                    lines.append(f"    - {r}")
        if self.cross_sensor_issues:
            lines.append("-" * 45)
            lines.append("Cross-Sensor Consistency Warnings:")
            for issue in self.cross_sensor_issues:
                lines.append(f"  ⚠ {issue}")
        lines.append("=" * 45)
        return "\n".join(lines)


class SensorQualityEvaluator:
    """
    Deterministic, physically grounded sequential sensor quality evaluator.
    Evaluates rate-of-change, statistical deviation (MAD), noise variance,
    monotonic drift, and cross-sensor physiological/chemical plausibility.
    """
    def __init__(self, config_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        if config is not None:
            self.config = config
        elif config_path is not None and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            default_cfg_path = os.path.join(base_dir, "config", "sensor_quality_config.json")
            if os.path.exists(default_cfg_path):
                with open(default_cfg_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            else:
                self.config = self._get_fallback_config()

        # Extract config parameters
        self.window_size = int(self.config.get("history_window_size", 10))
        self.min_history = int(self.config.get("min_history_for_stats", 4))
        self.max_stale_sec = float(self.config.get("max_stale_interval_sec", 45.0))
        self.max_frozen_count = int(self.config.get("max_frozen_count", 5))
        self.mad_multiplier = float(self.config.get("mad_outlier_multiplier", 3.5))
        self.weights = self.config.get("weights", {
            "ph": 0.25,
            "dissolved_oxygen_mg_l": 0.25,
            "turbidity_ntu": 0.20,
            "temperature_c": 0.15,
            "salinity_ppt": 0.15
        })
        self.bounds = self.config.get("physical_bounds", {
            "temperature_c": [-5.0, 45.0],
            "salinity_ppt": [0.0, 50.0],
            "ph": [0.0, 14.0],
            "turbidity_ntu": [0.0, 500.0],
            "dissolved_oxygen_mg_l": [0.0, 25.0]
        })
        self.rate_limits = self.config.get("rate_of_change_limits", {})
        self.noise_thresholds = self.config.get("noise_amplitude_thresholds", {})
        self.drift_thresholds = self.config.get("drift_thresholds", {})
        self.state_thresholds = self.config.get("quality_state_thresholds", {
            "reliable": 0.85,
            "degraded": 0.65,
            "suspicious": 0.35
        })

        # History structure: device_id -> sensor_name -> list of (datetime, value)
        self.history: Dict[str, Dict[str, List[Tuple[datetime.datetime, float]]]] = {}
        # Frozen history tracking: device_id -> sensor_name -> list of consecutive identical values
        self.frozen_history: Dict[str, Dict[str, List[float]]] = {}
        # Last observation timestamp per device
        self.last_timestamps: Dict[str, datetime.datetime] = {}

    def _get_fallback_config(self) -> Dict[str, Any]:
        return {
            "history_window_size": 10,
            "min_history_for_stats": 4,
            "max_stale_interval_sec": 45.0,
            "max_frozen_count": 5,
            "mad_outlier_multiplier": 3.5,
            "weights": {
                "ph": 0.25,
                "dissolved_oxygen_mg_l": 0.25,
                "turbidity_ntu": 0.20,
                "temperature_c": 0.15,
                "salinity_ppt": 0.15
            },
            "physical_bounds": {
                "temperature_c": [-5.0, 45.0],
                "salinity_ppt": [0.0, 50.0],
                "ph": [0.0, 14.0],
                "turbidity_ntu": [0.0, 500.0],
                "dissolved_oxygen_mg_l": [0.0, 25.0]
            },
            "rate_of_change_limits": {
                "temperature_c": {"warning_rate_per_sec": 0.10, "max_physical_rate_per_sec": 0.25},
                "ph": {"warning_rate_per_sec": 0.03, "max_physical_rate_per_sec": 0.10},
                "turbidity_ntu": {"warning_rate_per_sec": 2.5, "max_physical_rate_per_sec": 8.0},
                "salinity_ppt": {"warning_rate_per_sec": 0.20, "max_physical_rate_per_sec": 0.60},
                "dissolved_oxygen_mg_l": {"warning_rate_per_sec": 0.10, "max_physical_rate_per_sec": 0.30}
            },
            "noise_amplitude_thresholds": {
                "temperature_c": 0.8, "ph": 0.35, "turbidity_ntu": 8.0, "salinity_ppt": 0.5, "dissolved_oxygen_mg_l": 0.8
            },
            "drift_thresholds": {
                "temperature_c": 2.5, "ph": 0.8, "turbidity_ntu": 15.0, "salinity_ppt": 1.5, "dissolved_oxygen_mg_l": 2.0
            },
            "quality_state_thresholds": {
                "reliable": 0.85, "degraded": 0.65, "suspicious": 0.35
            }
        }

    def reset_history(self, device_id: Optional[str] = None):
        """Resets tracking history."""
        if device_id is not None:
            self.history.pop(device_id, None)
            self.frozen_history.pop(device_id, None)
            self.last_timestamps.pop(device_id, None)
        else:
            self.history.clear()
            self.frozen_history.clear()
            self.last_timestamps.clear()

    def _parse_timestamp(self, ts: Optional[Union[str, datetime.datetime]]) -> datetime.datetime:
        if ts is None:
            return datetime.datetime.now()
        if isinstance(ts, datetime.datetime):
            return ts
        try:
            clean_str = ts.rstrip("Z")
            return datetime.datetime.fromisoformat(clean_str)
        except Exception:
            return datetime.datetime.now()

    def evaluate(
        self,
        readings: Dict[str, Any],
        timestamp: Optional[Union[str, datetime.datetime]] = None,
        device_id: str = "DEFAULT"
    ) -> SensorQualityResult:
        """
        Executes end-to-end multi-metric sensor quality evaluation on an observation.
        """
        current_dt = self._parse_timestamp(timestamp or readings.get("timestamp"))
        ts_iso = current_dt.isoformat()

        # Initialize device tracking if missing
        if device_id not in self.history:
            self.history[device_id] = {k: [] for k in self.bounds.keys()}
            self.frozen_history[device_id] = {k: [] for k in self.bounds.keys()}

        # 1. Freshness / Timestamp Delta Check
        stale_status = "FRESH"
        freshness_factor = 1.0
        if device_id in self.last_timestamps:
            prev_dt = self.last_timestamps[device_id]
            delta_sec = (current_dt - prev_dt).total_seconds()
            if delta_sec > self.max_stale_sec:
                stale_status = "STALE"
                freshness_factor = 0.70  # Max 30% penalty for stale gaps
            elif delta_sec < 0.0:
                stale_status = "CLOCK_SKEW"
                freshness_factor = 0.85

        self.last_timestamps[device_id] = current_dt

        components: Dict[str, SensorQualityComponent] = {}
        anomaly_flags: List[str] = []
        reason_codes: List[str] = []

        # Target sensor keys
        sensor_names = ["temperature_c", "ph", "turbidity_ntu", "salinity_ppt", "dissolved_oxygen_mg_l"]

        for s_name in sensor_names:
            comp = self._evaluate_single_sensor(
                s_name=s_name,
                readings=readings,
                current_dt=current_dt,
                device_id=device_id
            )
            components[s_name] = comp

            # Accumulate flags & reason codes
            if comp.is_missing:
                anomaly_flags.append(f"{s_name.upper()}_MISSING")
                reason_codes.append(f"{s_name.upper()}_MISSING")
            if comp.is_outlier:
                anomaly_flags.append(f"{s_name.upper()}_OUTLIER")
                reason_codes.append(f"{s_name.upper()}_OUTLIER")
            if comp.is_noisy:
                anomaly_flags.append(f"{s_name.upper()}_NOISY")
                reason_codes.append(f"{s_name.upper()}_NOISY")
            if comp.is_drifting:
                anomaly_flags.append(f"{s_name.upper()}_DRIFT")
                reason_codes.append(f"{s_name.upper()}_DRIFT")
            if comp.is_stuck:
                anomaly_flags.append(f"{s_name.upper()}_STUCK")
                reason_codes.append(f"{s_name.upper()}_STUCK")
            if comp.rate_of_change is not None and comp.status in ["SUSPICIOUS", "FAULT"] and any("rate-of-change" in r.lower() for r in comp.reasons):
                anomaly_flags.append(f"{s_name.upper()}_RATE_VIOLATION")
                reason_codes.append(f"{s_name.upper()}_RATE_VIOLATION")

        # 2. Cross-Sensor Plausibility
        cross_consistency, cross_issues = self._evaluate_cross_sensor_plausibility(readings, components)
        if cross_issues:
            for issue in cross_issues:
                anomaly_flags.append(f"CROSS_{issue.upper().replace(' ', '_')}")
                reason_codes.append(f"CROSS_{issue.upper().replace(' ', '_')}")

        # Check if all sensors are stuck
        all_stuck = all(comp.is_stuck for comp in components.values() if not comp.is_missing)
        if all_stuck and len(components) > 0:
            stale_status = "FROZEN"

        # 3. Aggregate Overall Quality Q_sensor
        overall_q = self._compute_overall_quality(
            components=components,
            cross_consistency=cross_consistency,
            freshness_factor=freshness_factor,
            stale_status=stale_status
        )

        # 4. Map to Validation State
        if overall_q >= self.state_thresholds.get("reliable", 0.85):
            val_state = "RELIABLE"
        elif overall_q >= self.state_thresholds.get("degraded", 0.65):
            val_state = "DEGRADED"
        elif overall_q >= self.state_thresholds.get("suspicious", 0.35):
            val_state = "SUSPICIOUS"
        else:
            val_state = "FAULT"

        return SensorQualityResult(
            overall_quality=overall_q,
            validation_state=val_state,
            timestamp=ts_iso,
            components=components,
            anomaly_flags=list(set(anomaly_flags)),
            reason_codes=list(set(reason_codes)),
            cross_sensor_consistency=cross_consistency,
            cross_sensor_issues=cross_issues,
            stale_data_status=stale_status,
            metadata={
                "device_id": device_id,
                "freshness_factor": freshness_factor,
                "components_count": len(components)
            }
        )

    def _evaluate_single_sensor(
        self,
        s_name: str,
        readings: Dict[str, Any],
        current_dt: datetime.datetime,
        device_id: str
    ) -> SensorQualityComponent:
        """Evaluates all dimensions of quality for a single sensor."""
        # 1. Check presence and finite numeric validity
        raw_val = readings.get(s_name)
        reasons = []

        if raw_val is None:
            return SensorQualityComponent(
                sensor_name=s_name,
                raw_value=None,
                quality_score=0.0,
                status="FAULT",
                is_missing=True,
                reasons=[f"Missing or None reading for {s_name}"]
            )

        if not isinstance(raw_val, (int, float)) or not math.isfinite(raw_val):
            return SensorQualityComponent(
                sensor_name=s_name,
                raw_value=None,
                quality_score=0.0,
                status="FAULT",
                is_missing=True,
                reasons=[f"Non-numeric or non-finite reading for {s_name}: {raw_val}"]
            )

        val = float(raw_val)
        quality = 1.0

        # 2. Check Static Physical Boundaries
        min_b, max_b = self.bounds.get(s_name, (-9999.0, 9999.0))
        if not (min_b <= val <= max_b):
            reasons.append(f"Out of physical bounds [{min_b}, {max_b}]: val={val:.2f}")
            quality -= 0.85  # Severe penalty for physically impossible reading

        # 3. Stuck / Frozen Value Tracking
        stuck_list = self.frozen_history[device_id][s_name]
        is_stuck = False
        if len(stuck_list) > 0 and abs(stuck_list[-1] - val) < 1e-6:
            stuck_list.append(val)
            if len(stuck_list) >= self.max_frozen_count:
                is_stuck = True
                reasons.append(f"Frozen value detected ({len(stuck_list)} consecutive identical readings: {val:.3f})")
                quality -= 0.35
        else:
            self.frozen_history[device_id][s_name] = [val]

        # Fetch historical series
        hist_series = self.history[device_id][s_name]
        rate_of_change = None
        z_score = None
        is_outlier = False
        is_noisy = False
        is_drifting = False

        if len(hist_series) > 0:
            # 4. Rate-of-Change Check
            prev_dt, prev_val = hist_series[-1]
            dt_sec = max((current_dt - prev_dt).total_seconds(), 0.1)  # Bound minimum dt
            rate_of_change = abs(val - prev_val) / dt_sec

            limits = self.rate_limits.get(s_name, {"warning_rate_per_sec": 1.0, "max_physical_rate_per_sec": 5.0})
            warn_rate = limits.get("warning_rate_per_sec", 1.0)
            max_rate = limits.get("max_physical_rate_per_sec", 5.0)

            if rate_of_change > max_rate:
                reasons.append(f"Severe rate-of-change violation ({rate_of_change:.3f} > {max_rate:.3f} units/s)")
                quality -= 0.55
            elif rate_of_change > warn_rate:
                reasons.append(f"High rate-of-change warning ({rate_of_change:.3f} > {warn_rate:.3f} units/s)")
                quality -= 0.25

        # 5. Statistical Outlier Check via Median Absolute Deviation (MAD)
        if len(hist_series) >= self.min_history:
            past_vals = [h[1] for h in hist_series[-self.window_size:]]
            med = float(np.median(past_vals))
            mad = float(np.median(np.abs(np.array(past_vals) - med)))
            mad = max(mad, 1e-4)  # Prevent divide by zero

            modified_z = 0.6745 * abs(val - med) / mad
            z_score = modified_z

            if modified_z > self.mad_multiplier:
                is_outlier = True
                reasons.append(f"Statistical outlier detected (Modified Z-score={modified_z:.2f} > {self.mad_multiplier:.2f})")
                quality -= 0.35

            # 6. Noise Characterization (High-frequency Alternating Jitter)
            recent_series = past_vals + [val]
            if len(recent_series) >= 6:
                diffs = np.diff(recent_series[-6:])
                sign_flips = np.sum(np.diff(np.sign(diffs)) != 0)
                noise_amp = np.std(recent_series[-6:])
                thresh_amp = self.noise_thresholds.get(s_name, 1.0)

                if sign_flips >= 3 and noise_amp > thresh_amp:
                    is_noisy = True
                    reasons.append(f"Excessive noise/jitter detected (amp={noise_amp:.2f} > {thresh_amp:.2f})")
                    quality -= 0.25

            # 7. Monotonic Sensor Drift Check
            if len(recent_series) >= 6:
                total_drift = abs(recent_series[-1] - recent_series[-6])
                drift_thresh = self.drift_thresholds.get(s_name, 2.0)
                # Check near-monotonic slope
                diffs = np.diff(recent_series[-6:])
                strictly_increasing = np.all(diffs >= -1e-4)
                strictly_decreasing = np.all(diffs <= 1e-4)

                if (strictly_increasing or strictly_decreasing) and total_drift > drift_thresh:
                    is_drifting = True
                    reasons.append(f"Monotonic sensor drift detected (delta={total_drift:.2f} > {drift_thresh:.2f})")
                    quality -= 0.20

        # Append to history ring buffer
        hist_series.append((current_dt, val))
        if len(hist_series) > self.window_size * 2:
            self.history[device_id][s_name] = hist_series[-self.window_size:]

        # Bound quality score strictly within [0.0, 1.0]
        quality = max(0.0, min(1.0, quality))

        # Determine individual status
        if quality >= 0.85:
            status = "OK"
        elif quality >= 0.65:
            status = "DEGRADED"
        elif quality >= 0.35:
            status = "SUSPICIOUS"
        else:
            status = "FAULT"

        return SensorQualityComponent(
            sensor_name=s_name,
            raw_value=val,
            quality_score=quality,
            status=status,
            rate_of_change=rate_of_change,
            z_score=z_score,
            is_outlier=is_outlier,
            is_noisy=is_noisy,
            is_drifting=is_drifting,
            is_stuck=is_stuck,
            is_missing=False,
            reasons=reasons
        )

    def _evaluate_cross_sensor_plausibility(
        self,
        readings: Dict[str, Any],
        components: Dict[str, SensorQualityComponent]
    ) -> Tuple[float, List[str]]:
        """
        Physically grounded cross-sensor plausibility checks.
        Evaluates coupled relationships among pH, Dissolved Oxygen, Temperature, and Turbidity.
        """
        cross_issues = []
        consistency = 1.0

        temp = readings.get("temperature_c")
        ph = readings.get("ph")
        do = readings.get("dissolved_oxygen_mg_l")
        turb = readings.get("turbidity_ntu")
        sal = readings.get("salinity_ppt")

        # Skip checks if essential coupled values are None or faulty
        if temp is None or ph is None or do is None:
            return 1.0, []

        # Rule 1: Photosynthetic Coupling
        # In natural aquatic ecosystems, strong alkaline pH spike (e.g. pH > 9.0) caused by biological bloom
        # consumes CO2 and generates dissolved oxygen, while suspended algae raises turbidity.
        # If pH spikes extremely high (pH >= 9.2) while DO crashes near anoxia (DO < 3.0 mg/L) and turbidity is pristine (< 3.0 NTU),
        # this is physically contradictory for a natural aquatic body (indicates pH probe glass junction failure).
        if ph >= 9.2 and do < 3.0 and turb is not None and turb < 3.0:
            cross_issues.append("Extreme alkaline pH with anoxic DO and clear water is physically implausible")
            consistency -= 0.35

        # Rule 2: Henry's Law Thermal Dissolved Oxygen Saturation
        # Hot water (e.g. temp > 35°C) has a low physical gas solubility ceiling (~7.0 mg/L).
        # If water temperature is extremely high (>35°C) but DO is simultaneously reported at extreme supersaturation (>18.0 mg/L)
        # without extreme turbidity, flag thermal-gas solubility contradiction.
        if temp > 35.0 and do > 18.0:
            cross_issues.append(f"Extreme DO supersaturation ({do:.1f} mg/L) at high temperature ({temp:.1f}°C) exceeds gas solubility limit")
            consistency -= 0.25

        # Rule 3: Freshwater Salinity Boundary Check
        # If freshwater lake reading exhibits marine ocean salinity (>15 ppt) while pH/temp are normal freshwater, flag context contradiction.
        if sal is not None and sal > 25.0 and readings.get("dataset_route", "caml").lower() == "caml":
            cross_issues.append(f"Marine salinity ({sal:.1f} ppt) reported for freshwater lake site")
            consistency -= 0.20

        # Bound consistency
        consistency = max(0.20, min(1.0, consistency))
        return consistency, cross_issues

    def _compute_overall_quality(
        self,
        components: Dict[str, SensorQualityComponent],
        cross_consistency: float,
        freshness_factor: float,
        stale_status: str
    ) -> float:
        """
        Computes bounded, deterministic Q_sensor score.
        Q_sensor = sum(w_i * q_i) * C_cross * F_fresh
        """
        if not components:
            return 0.0

        weighted_sum = 0.0
        total_weight = 0.0

        for name, comp in components.items():
            w = self.weights.get(name, 0.20)
            weighted_sum += w * comp.quality_score
            total_weight += w

        base_q = weighted_sum / total_weight if total_weight > 0 else 0.0

        # If any component is severely degraded, penalize overall reliability
        min_comp_q = min(comp.quality_score for comp in components.values())
        if min_comp_q < 0.60:
            severe_discount = 0.70 + (0.30 * (min_comp_q / 0.60))
            base_q *= severe_discount

        # Apply cross-sensor consistency and freshness multipliers
        overall = base_q * cross_consistency * freshness_factor

        # If data is frozen/stuck across all channels, hard cap at 0.40
        if stale_status == "FROZEN":
            overall = min(overall, 0.40)

        return round(max(0.0, min(1.0, overall)), 4)
