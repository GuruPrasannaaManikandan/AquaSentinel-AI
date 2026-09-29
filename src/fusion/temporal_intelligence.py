import time
import math
import logging
import datetime
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Tuple


@dataclass
class TelemetryHistoryPoint:
    """Snapshot of telemetry values and timestamp for sliding-window temporal analysis."""
    timestamp_sec: float
    iso_timestamp: str
    temperature_c: Optional[float]
    ph: Optional[float]
    turbidity_ntu: Optional[float]
    dissolved_oxygen_mg_l: Optional[float]
    salinity_ppt: Optional[float]
    turbidity_voltage: Optional[float] = None
    q_sensor: float = 1.0


@dataclass
class MetricTrend:
    """Computed trajectory and linear regression slope for a single sensor metric."""
    metric_name: str
    current_value: Optional[float]
    slope_per_sec: Optional[float]
    slope_per_min: Optional[float]
    delta_total: Optional[float]
    rate_of_change: Optional[float]
    is_rising: bool
    is_falling: bool
    is_accelerating: bool
    persistence_count: int


@dataclass
class TemporalTrajectoryResult:
    """
    Structured temporal environmental intelligence contract.
    Encapsulates rolling trajectory analysis, rate-of-change slopes, persistence counters,
    and the multi-tier ecological threat progression.
    """
    device_id: str
    timestamp: str
    temporal_state: str  # "NORMAL", "WATCH", "EARLY_WARNING", "HIGH_RISK", "BLOOM_CONFIRMED"
    trajectory_risk_score: float  # [0.0, 1.0]
    persistence_cycles: int
    window_size_evaluated: int
    lead_indicators: List[str] = field(default_factory=list)
    trend_slopes: Dict[str, Optional[float]] = field(default_factory=dict)
    rates_of_change: Dict[str, Optional[float]] = field(default_factory=dict)
    metric_trends: Dict[str, Any] = field(default_factory=dict)
    is_stable: bool = True
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TemporalEnvironmentalEngine:
    """
    V5.3 Temporal Environmental Trend & Trajectory Engine.
    Operates on a rolling sliding window of the last N=12 telemetry cycles per device.
    Calculates linear regression trend slopes, instantaneous rates of change, and cumulative
    persistence to detect emerging eutrophication trajectories well before static thresholds trip.
    """
    def __init__(
        self,
        window_size: int = 12,
        max_window_age_sec: float = 600.0,
        temp_warning_slope_c_per_min: float = 0.15,
        ph_warning_slope_per_min: float = 0.08,
        ph_critical_slope_per_min: float = 0.20,
        turb_warning_slope_ntu_per_min: float = 3.0,
        do_warning_slope_mg_l_per_min: float = 0.20
    ):
        self.window_size = window_size
        self.max_window_age_sec = max_window_age_sec
        self.temp_warning_slope_c_per_min = temp_warning_slope_c_per_min
        self.ph_warning_slope_per_min = ph_warning_slope_per_min
        self.ph_critical_slope_per_min = ph_critical_slope_per_min
        self.turb_warning_slope_ntu_per_min = turb_warning_slope_ntu_per_min
        self.do_warning_slope_mg_l_per_min = do_warning_slope_mg_l_per_min

        # Rolling buffers keyed by device_id: deque of TelemetryHistoryPoint
        self.device_buffers: Dict[str, deque] = {}
        # Cumulative persistence tracking per device
        self.persistence_counters: Dict[str, int] = {}
        self.last_states: Dict[str, str] = {}

    def _get_buffer(self, device_id: str) -> deque:
        if device_id not in self.device_buffers:
            self.device_buffers[device_id] = deque(maxlen=self.window_size)
            self.persistence_counters[device_id] = 0
            self.last_states[device_id] = "NORMAL"
        return self.device_buffers[device_id]

    def reset_device(self, device_id: str):
        """Resets history for a specific device."""
        if device_id in self.device_buffers:
            self.device_buffers[device_id].clear()
            self.persistence_counters[device_id] = 0
            self.last_states[device_id] = "NORMAL"

    def _parse_timestamp(self, ts: Any) -> float:
        """Converts ISO timestamp string or float seconds into epoch seconds."""
        if isinstance(ts, (int, float)):
            return float(ts)
        if isinstance(ts, str):
            try:
                # Handle ISO format
                dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                return dt.timestamp()
            except Exception:
                pass
        return time.time()

    def _calculate_linear_slope(self, times: List[float], values: List[float]) -> float:
        """
        Calculates ordinary least squares linear regression slope:
        slope = (N * sum(t*y) - sum(t)*sum(y)) / (N * sum(t^2) - (sum(t))^2)
        Returns slope in units per second.
        """
        n = len(times)
        if n < 2:
            return 0.0

        t0 = times[0]
        # Normalize time to avoid numerical instability
        t_norm = [t - t0 for t in times]

        sum_t = sum(t_norm)
        sum_y = sum(values)
        sum_ty = sum(t * y for t, y in zip(t_norm, values))
        sum_t2 = sum(t * t for t in t_norm)

        denominator = n * sum_t2 - (sum_t * sum_t)
        if abs(denominator) < 1e-9:
            return 0.0

        slope_per_sec = (n * sum_ty - (sum_t * sum_y)) / denominator
        return float(slope_per_sec)

    def _analyze_metric(
        self,
        name: str,
        history: List[TelemetryHistoryPoint],
        attr_name: str
    ) -> MetricTrend:
        """Extracts values and computes trajectory slope, delta, and rate of change."""
        valid_points = [
            (p.timestamp_sec, getattr(p, attr_name))
            for p in history
            if getattr(p, attr_name) is not None
        ]

        if not valid_points:
            return MetricTrend(
                metric_name=name,
                current_value=None,
                slope_per_sec=None,
                slope_per_min=None,
                delta_total=None,
                rate_of_change=None,
                is_rising=False,
                is_falling=False,
                is_accelerating=False,
                persistence_count=0
            )

        times = [pt[0] for pt in valid_points]
        vals = [pt[1] for pt in valid_points]
        curr_val = vals[-1]

        if len(vals) < 2:
            return MetricTrend(
                metric_name=name,
                current_value=curr_val,
                slope_per_sec=None,
                slope_per_min=None,
                delta_total=0.0,
                rate_of_change=0.0,
                is_rising=False,
                is_falling=False,
                is_accelerating=False,
                persistence_count=0
            )

        dt_total = max(times[-1] - times[0], 0.1)
        delta_total = vals[-1] - vals[0]
        slope_per_sec = self._calculate_linear_slope(times, vals)
        slope_per_min = slope_per_sec * 60.0

        # Rate of change from penultimate point
        dt_last = max(times[-1] - times[-2], 0.1)
        roc = (vals[-1] - vals[-2]) / dt_last

        # Detect curvature / acceleration
        is_accel = False
        if len(vals) >= 3:
            dt1 = max(times[-2] - times[-3], 0.1)
            roc_prev = (vals[-2] - vals[-3]) / dt1
            is_accel = (roc > roc_prev > 0) or (roc < roc_prev < 0)

        # Rising or falling based on slope
        is_rising = slope_per_min > 0.01
        is_falling = slope_per_min < -0.01

        # Persistence of same direction over last points
        persistence = 0
        for i in range(len(vals) - 1, 0, -1):
            if is_rising and vals[i] >= vals[i - 1]:
                persistence += 1
            elif is_falling and vals[i] <= vals[i - 1]:
                persistence += 1
            else:
                break

        return MetricTrend(
            metric_name=name,
            current_value=curr_val,
            slope_per_sec=round(slope_per_sec, 6),
            slope_per_min=round(slope_per_min, 4),
            delta_total=round(delta_total, 4),
            rate_of_change=round(roc, 4),
            is_rising=is_rising,
            is_falling=is_falling,
            is_accelerating=is_accel,
            persistence_count=persistence
        )

    def evaluate_telemetry(
        self,
        device_id: str,
        telemetry: Dict[str, Any],
        q_sensor: float = 1.0
    ) -> TemporalTrajectoryResult:
        """
        Ingests a new telemetry point for device_id, evaluates sliding-window slopes,
        lead indicators, and produces the multi-tier ecological threat classification.
        """
        buf = self._get_buffer(device_id)

        iso_ts = telemetry.get("timestamp") or datetime.datetime.now().isoformat()
        ts_sec = self._parse_timestamp(iso_ts)

        turb_v = telemetry.get("turbidity_voltage")
        if turb_v is None:
            turb_v = telemetry.get("turbidity_ntu")

        point = TelemetryHistoryPoint(
            timestamp_sec=ts_sec,
            iso_timestamp=iso_ts,
            temperature_c=telemetry.get("temperature_c"),
            ph=telemetry.get("ph"),
            turbidity_ntu=telemetry.get("turbidity_ntu"),
            dissolved_oxygen_mg_l=telemetry.get("dissolved_oxygen_mg_l"),
            salinity_ppt=telemetry.get("salinity_ppt"),
            turbidity_voltage=turb_v,
            q_sensor=q_sensor
        )

        # Evict points older than max_window_age_sec relative to new point
        while buf and (ts_sec - buf[0].timestamp_sec > self.max_window_age_sec):
            buf.popleft()

        buf.append(point)
        history = list(buf)
        n_points = len(history)

        # Cold start handling
        if n_points < 2:
            return TemporalTrajectoryResult(
                device_id=device_id,
                timestamp=iso_ts,
                temporal_state="NORMAL",
                trajectory_risk_score=0.0,
                persistence_cycles=0,
                window_size_evaluated=n_points,
                lead_indicators=["Cold start: Insufficient temporal history (< 2 points)"],
                trend_slopes={},
                rates_of_change={},
                metric_trends={},
                is_stable=True,
                summary="Baseline temporal window initializing."
            )

        # Analyze each key metric
        trend_temp = self._analyze_metric("temperature_c", history, "temperature_c")
        trend_ph = self._analyze_metric("ph", history, "ph")
        trend_turb = self._analyze_metric("turbidity_ntu", history, "turbidity_ntu")
        trend_turb_v = self._analyze_metric("turbidity_voltage", history, "turbidity_voltage")
        trend_do = self._analyze_metric("dissolved_oxygen_mg_l", history, "dissolved_oxygen_mg_l")
        trend_sal = self._analyze_metric("salinity_ppt", history, "salinity_ppt")

        metric_trends = {
            "temperature_c": asdict(trend_temp),
            "ph": asdict(trend_ph),
            "turbidity_ntu": asdict(trend_turb),
            "turbidity_voltage": asdict(trend_turb_v),
            "dissolved_oxygen_mg_l": asdict(trend_do),
            "salinity_ppt": asdict(trend_sal)
        }

        trend_slopes = {
            "temperature_c_per_min": trend_temp.slope_per_min,
            "ph_per_min": trend_ph.slope_per_min,
            "turbidity_ntu_per_min": trend_turb.slope_per_min,
            "turbidity_voltage_per_min": trend_turb_v.slope_per_min,
            "dissolved_oxygen_mg_l_per_min": trend_do.slope_per_min,
            "salinity_ppt_per_min": trend_sal.slope_per_min
        }

        rates_of_change = {
            "temperature_c_roc": trend_temp.rate_of_change,
            "ph_roc": trend_ph.rate_of_change,
            "turbidity_ntu_roc": trend_turb.rate_of_change,
            "turbidity_voltage_roc": trend_turb_v.rate_of_change,
            "dissolved_oxygen_mg_l_roc": trend_do.rate_of_change
        }

        # Multi-stage eutrophication trajectory detection
        lead_indicators = []
        threat_points = 0.0

        # Phase 1: Incubation (Water warming trend)
        is_warming = (
            trend_temp.slope_per_min is not None
            and trend_temp.slope_per_min >= self.temp_warning_slope_c_per_min
            and trend_temp.persistence_count >= 2
        )
        if is_warming:
            lead_indicators.append(f"Water temperature warming (+{trend_temp.slope_per_min:.2f}°C/min)")
            threat_points += 0.20

        # Phase 2: Photosynthetic Proliferation (Accelerating pH climb + DO rise)
        is_ph_accelerating = (
            trend_ph.slope_per_min is not None
            and trend_ph.slope_per_min >= self.ph_warning_slope_per_min
            and trend_ph.persistence_count >= 2
        )
        is_ph_critical = (
            trend_ph.slope_per_min is not None
            and trend_ph.slope_per_min >= self.ph_critical_slope_per_min
        )
        if is_ph_critical:
            lead_indicators.append(f"Rapid pH climb (+{trend_ph.slope_per_min:.2f} pH/min, critical trajectory)")
            threat_points += 0.40
        elif is_ph_accelerating:
            lead_indicators.append(f"Elevated pH upward trend (+{trend_ph.slope_per_min:.2f} pH/min)")
            threat_points += 0.25

        is_do_coupled_rise = (
            trend_do.slope_per_min is not None
            and trend_do.slope_per_min >= self.do_warning_slope_mg_l_per_min
            and trend_ph.is_rising
        )
        if is_do_coupled_rise:
            lead_indicators.append(f"Coupled photosynthetic DO saturation rise (+{trend_do.slope_per_min:.2f} mg/L/min)")
            threat_points += 0.20

        # Phase 3: Turbidity and organic proliferation
        is_turbidity_surge = (
            trend_turb.slope_per_min is not None
            and trend_turb.slope_per_min >= self.turb_warning_slope_ntu_per_min
            and trend_turb.persistence_count >= 2
        )
        if is_turbidity_surge:
            lead_indicators.append(f"Accelerating turbidity climb (+{trend_turb.slope_per_min:.2f} NTU/min)")
            threat_points += 0.30

        # High absolute value check
        if trend_ph.current_value is not None and trend_ph.current_value >= 9.0:
            lead_indicators.append(f"Current pH exceeds eutrophic threshold ({trend_ph.current_value:.2f})")
            threat_points += 0.25
        if trend_turb.current_value is not None and trend_turb.current_value >= 40.0:
            lead_indicators.append(f"Current turbidity exceeds high-risk threshold ({trend_turb.current_value:.1f} NTU)")
            threat_points += 0.25

        # Discount threat if sensor quality is poor (Q_sensor penalty)
        effective_threat = min(1.0, threat_points * math.sqrt(max(0.1, q_sensor)))

        # Update persistence counter
        if effective_threat >= 0.30:
            self.persistence_counters[device_id] = self.persistence_counters.get(device_id, 0) + 1
        else:
            self.persistence_counters[device_id] = max(0, self.persistence_counters.get(device_id, 0) - 1)

        persist = self.persistence_counters[device_id]

        # Classify multi-tier threat state
        # 1. NORMAL
        # 2. WATCH (Early precursors, warming or mild pH rise, persist >= 1)
        # 3. EARLY_WARNING (Multiple coupled upward trends, persist >= 2)
        # 4. HIGH_RISK (Sustained accelerating bloom trajectory, persist >= 3)
        # 5. BLOOM_CONFIRMED (Persistent high threat + absolute thresholds, persist >= 4)
        if effective_threat >= 0.70 and persist >= 4:
            state = "BLOOM_CONFIRMED"
        elif effective_threat >= 0.50 and persist >= 3:
            state = "HIGH_RISK"
        elif effective_threat >= 0.30 and persist >= 2:
            state = "EARLY_WARNING"
        elif effective_threat >= 0.20:
            state = "WATCH"
        else:
            state = "NORMAL"

        self.last_states[device_id] = state
        is_stable = state == "NORMAL"

        summary_parts = []
        if is_stable:
            summary = "Ecosystem parameters stable within rolling baseline limits."
        else:
            summary = f"Temporal Trajectory [{state}]: {'; '.join(lead_indicators)} (persistence={persist})."

        return TemporalTrajectoryResult(
            device_id=device_id,
            timestamp=iso_ts,
            temporal_state=state,
            trajectory_risk_score=round(effective_threat, 4),
            persistence_cycles=persist,
            window_size_evaluated=n_points,
            lead_indicators=lead_indicators,
            trend_slopes=trend_slopes,
            rates_of_change=rates_of_change,
            metric_trends=metric_trends,
            is_stable=is_stable,
            summary=summary
        )
