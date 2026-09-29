import time
import math
import logging
import datetime
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


@dataclass
class RiskTrendResult:
    """
    Structured research-grade predictive intelligence and risk trend contract.
    Encapsulates risk trajectory, interpretable early-warning horizon,
    confidence, uncertainty, data sufficiency, and falsification guards.
    """
    trajectory: str  # "STABLE", "RISING", "ACCELERATING", "PEAKING", "DECLINING", "RECOVERING"
    horizon_state: str  # "NO_IMMEDIATE_RISK", "DEVELOPING_RISK", "NEAR_TERM_RISK", "ACTIVE_EVENT", "RECOVERY"
    confidence: float  # [0.0, 1.0]
    evidence_window: int  # Number of cycles evaluated
    supporting_modalities: List[str] = field(default_factory=list)
    uncertainty: float = 0.0  # [0.0, 1.0]
    data_sufficiency: str = "SUFFICIENT"  # "SUFFICIENT", "MARGINAL", "INSUFFICIENT_DATA"
    reason_codes: List[str] = field(default_factory=list)
    risk_score: float = 0.0  # Current composite risk score [0.0, 1.0]
    slope_per_min: float = 0.0  # Linear rate-of-change per minute
    acceleration: float = 0.0  # Derivative of slope
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RiskTrajectoryEngine:
    """
    V8 Advanced Risk Trend & Predictive Intelligence Engine.
    Operates on a multi-cycle rolling buffer (default N=12) of synchronized multimodal
    evidence, temporal slopes, and historical deviations.
    Provides deterministic, statistical early-warning horizon estimates without
    unjustified black-box deep learning forecasting on non-continuous data.
    """
    def __init__(
        self,
        window_size: int = 12,
        min_sufficient_cycles: int = 3,
        slope_rising_threshold: float = 0.05,
        slope_accelerating_threshold: float = 0.12,
        peak_risk_threshold: float = 0.80,
        declining_threshold: float = -0.04
    ):
        self.window_size = window_size
        self.min_sufficient_cycles = min_sufficient_cycles
        self.slope_rising_threshold = slope_rising_threshold
        self.slope_accelerating_threshold = slope_accelerating_threshold
        self.peak_risk_threshold = peak_risk_threshold
        self.declining_threshold = declining_threshold

        # Device buffers: {device_id: deque of historical points}
        # Point structure: (timestamp_sec, composite_risk, effective_confidence, state, modalities_dict)
        self.device_buffers: Dict[str, deque] = {}
        self.last_slopes: Dict[str, float] = {}

    def _get_buffer(self, device_id: str) -> deque:
        if device_id not in self.device_buffers:
            self.device_buffers[device_id] = deque(maxlen=self.window_size)
            self.last_slopes[device_id] = 0.0
        return self.device_buffers[device_id]

    def reset_device(self, device_id: str):
        """Resets the history for a given device."""
        if device_id in self.device_buffers:
            del self.device_buffers[device_id]
        if device_id in self.last_slopes:
            del self.last_slopes[device_id]

    def _map_state_to_risk(self, state: str) -> float:
        """Deterministic mapping of categorical ecological state to baseline risk in [0.0, 1.0]."""
        mapping = {
            "NORMAL": 0.05,
            "WATCH": 0.30,
            "EARLY_WARNING": 0.60,
            "HIGH_RISK": 0.85,
            "CRITICAL": 0.95,
            "BLOOM_CONFIRMED": 0.95,
            "UNKNOWN_ANOMALY": 0.45,
            "SENSOR_FAULT": 0.20
        }
        return mapping.get(state.upper(), 0.10)

    def evaluate_trajectory(
        self,
        device_id: str,
        multimodal_decision: Dict[str, Any],
        temporal_evidence: Optional[Dict[str, Any]] = None,
        sensor_quality: Optional[Dict[str, Any]] = None,
        historical_evidence: Optional[Dict[str, Any]] = None,
        current_time_sec: Optional[float] = None
    ) -> RiskTrendResult:
        """
        Evaluates the multi-cycle risk trajectory and produces an auditable RiskTrendResult.
        """
        buf = self._get_buffer(device_id)
        now_sec = current_time_sec if current_time_sec is not None else time.time()

        # 1. Extract current state & confidence
        fusion_info = multimodal_decision.get("fusion", {})
        mm_intel = multimodal_decision.get("multimodal_intelligence", {})
        state = mm_intel.get("synthesized_state") or fusion_info.get("final_state", "NORMAL")
        confidence = mm_intel.get("confidence") or fusion_info.get("confidence", 0.80)
        concordance_score = mm_intel.get("concordance_score", 1.0)
        conflict_detected = mm_intel.get("conflict_detected", False)
        dominance_prevented = mm_intel.get("dominance_prevented", False)

        # Baseline risk from categorical state
        base_risk = self._map_state_to_risk(state)

        # Blend with temporal risk score if available
        temp_risk = None
        if temporal_evidence:
            temp_risk = temporal_evidence.get("trajectory_risk_score")
        
        # Blend with historical deviation if available
        hist_deviation = 0.0
        if historical_evidence:
            if isinstance(historical_evidence, dict):
                hist_deviation = historical_evidence.get("anomaly_severity", 0.0)
            elif hasattr(historical_evidence, "anomaly_severity"):
                hist_deviation = getattr(historical_evidence, "anomaly_severity", 0.0)
            elif hasattr(historical_evidence, "to_dict"):
                hist_deviation = historical_evidence.to_dict().get("anomaly_severity", 0.0)

        # Calculate composite point risk
        if temp_risk is not None:
            composite_risk = (base_risk * 0.60) + (temp_risk * 0.30) + (hist_deviation * 0.10)
        else:
            composite_risk = (base_risk * 0.80) + (hist_deviation * 0.20)
        composite_risk = max(0.0, min(1.0, composite_risk))

        # Identify supporting modalities
        supporting_modalities: List[str] = []
        if multimodal_decision.get("ml_evidence"):
            supporting_modalities.append("sensor_ml")
        if multimodal_decision.get("visual_evidence") and multimodal_decision.get("visual_evidence", {}).get("valid", True):
            supporting_modalities.append("visual")
        if temporal_evidence:
            supporting_modalities.append("temporal")
        if multimodal_decision.get("ais_evidence"):
            supporting_modalities.append("ais")
        if historical_evidence:
            supporting_modalities.append("historical")

        # Append current observation to rolling window
        record = {
            "time_sec": now_sec,
            "risk": composite_risk,
            "confidence": confidence,
            "state": state,
            "supporting_count": len(supporting_modalities)
        }
        buf.append(record)
        window_len = len(buf)

        reason_codes: List[str] = []

        # 2. Check Data Sufficiency & False-Prediction Protection
        if window_len < self.min_sufficient_cycles:
            data_sufficiency = "INSUFFICIENT_DATA"
            uncertainty = max(0.65, 1.0 - (window_len / self.min_sufficient_cycles) * 0.5)
            reason_codes.append("INSUFFICIENT_HISTORY")
            trajectory = "STABLE"
            
            # Clamp horizon state when data is insufficient
            if state in ["CRITICAL", "BLOOM_CONFIRMED", "HIGH_RISK"]:
                horizon_state = "DEVELOPING_RISK"
                reason_codes.append("EARLY_ALARM_CLAMPED_INSUFFICIENT_HISTORY")
            else:
                horizon_state = "NO_IMMEDIATE_RISK"

            return RiskTrendResult(
                trajectory=trajectory,
                horizon_state=horizon_state,
                confidence=round(confidence * 0.60, 3),
                evidence_window=window_len,
                supporting_modalities=supporting_modalities,
                uncertainty=round(uncertainty, 3),
                data_sufficiency=data_sufficiency,
                reason_codes=reason_codes,
                risk_score=round(composite_risk, 3),
                slope_per_min=0.0,
                acceleration=0.0,
                summary=f"Insufficient multi-cycle history ({window_len}/{self.min_sufficient_cycles} cycles). Forecast suppressed."
            )
        elif window_len < 6:
            data_sufficiency = "MARGINAL"
            uncertainty = 0.35
            reason_codes.append("MARGINAL_WINDOW_SIZE")
        else:
            data_sufficiency = "SUFFICIENT"
            uncertainty = 0.15

        # 3. Calculate Rate of Change (Linear Regression Slope)
        times = [p["time_sec"] for p in buf]
        risks = [p["risk"] for p in buf]

        t_mean = sum(times) / len(times)
        r_mean = sum(risks) / len(risks)

        dt = times[-1] - times[0]
        # Avoid division by zero if all timestamps are identical (e.g. simulated clock freeze)
        if dt > 0.001:
            num = sum((t - t_mean) * (r - r_mean) for t, r in zip(times, risks))
            den = sum((t - t_mean) ** 2 for t in times)
            slope_per_sec = num / den if den > 1e-9 else 0.0
            slope_per_min = slope_per_sec * 60.0
        else:
            # Fallback: step-based slope if timestamp delta is zero
            num = sum((i - (window_len - 1) / 2) * (r - r_mean) for i, r in enumerate(risks))
            den = sum((i - (window_len - 1) / 2) ** 2 for i in range(window_len))
            slope_per_min = (num / den) * 2.0 if den > 0 else 0.0

        # Acceleration (derivative of slope)
        prev_slope = self.last_slopes.get(device_id, 0.0)
        acceleration = slope_per_min - prev_slope
        self.last_slopes[device_id] = slope_per_min

        # 4. Falsification Guards & False-Prediction Dampening
        # Guard A: Single sensor spike (instantaneous jump with no prior persistence)
        is_spike = False
        if window_len >= 3 and risks[-1] >= 0.60 and risks[-2] < 0.25 and risks[-3] < 0.25:
            is_spike = True
            reason_codes.append("SINGLE_SPIKE_DAMPENED")
            uncertainty = min(1.0, uncertainty + 0.35)

        # Guard B: Degraded sensor or optical quality
        if sensor_quality and sensor_quality.get("q_sensor", 1.0) < 0.60:
            reason_codes.append("DEGRADED_SENSOR_SNR")
            uncertainty = min(1.0, uncertainty + 0.20)
        
        # Guard C: Cross-modality conflict
        if conflict_detected:
            reason_codes.append("MODALITY_CONFLICT_DAMPENED")
            uncertainty = min(1.0, uncertainty + 0.25)

        # Guard D: Dominance prevented
        if dominance_prevented:
            reason_codes.append("DOMINANCE_PREVENTED")
            uncertainty = min(1.0, uncertainty + 0.15)

        # 5. Classify Trajectory
        # Historical context: is it returning from a peak?
        max_prior_risk = max(risks[:-1]) if window_len > 1 else 0.0

        if composite_risk >= self.peak_risk_threshold and abs(slope_per_min) < self.slope_rising_threshold:
            trajectory = "PEAKING"
            reason_codes.append("RISK_AT_PEAK")
        elif slope_per_min <= self.declining_threshold and composite_risk < max_prior_risk:
            if max_prior_risk >= 0.60:
                trajectory = "RECOVERING"
                reason_codes.append("ECOSYSTEM_RECOVERY_DETECTED")
            else:
                trajectory = "DECLINING"
                reason_codes.append("RISK_TREND_DECLINING")
        elif slope_per_min >= self.slope_accelerating_threshold or (slope_per_min >= self.slope_rising_threshold and acceleration > 0.05):
            trajectory = "ACCELERATING"
            reason_codes.append("RISK_ACCELERATING")
        elif slope_per_min >= self.slope_rising_threshold:
            trajectory = "RISING"
            reason_codes.append("RISK_RISING")
        else:
            trajectory = "STABLE"
            reason_codes.append("RISK_STABLE")

        # 6. Classify Early-Warning Horizon
        if state in ["CRITICAL", "BLOOM_CONFIRMED"] or composite_risk >= self.peak_risk_threshold:
            if is_spike:
                horizon_state = "DEVELOPING_RISK"
                reason_codes.append("ACTIVE_EVENT_CLAMPED_DUE_TO_SPIKE")
            else:
                horizon_state = "ACTIVE_EVENT"
        elif trajectory in ["ACCELERATING", "RISING"] and composite_risk >= 0.50:
            if is_spike or conflict_detected:
                horizon_state = "DEVELOPING_RISK"
            else:
                horizon_state = "NEAR_TERM_RISK"
        elif trajectory in ["RISING", "ACCELERATING"] or composite_risk >= 0.25:
            horizon_state = "DEVELOPING_RISK"
        elif trajectory == "RECOVERING":
            horizon_state = "RECOVERY"
        else:
            horizon_state = "NO_IMMEDIATE_RISK"

        # 7. Final Confidence Adjustment
        final_confidence = confidence * (1.0 - uncertainty * 0.5) * (0.7 + 0.3 * concordance_score)
        final_confidence = max(0.10, min(1.0, final_confidence))

        summary = (
            f"Trajectory: {trajectory} (slope: {slope_per_min:+.3f}/min). "
            f"Horizon: {horizon_state} (risk: {composite_risk:.2f}, uncertainty: {uncertainty:.2f})."
        )

        return RiskTrendResult(
            trajectory=trajectory,
            horizon_state=horizon_state,
            confidence=round(final_confidence, 3),
            evidence_window=window_len,
            supporting_modalities=supporting_modalities,
            uncertainty=round(uncertainty, 3),
            data_sufficiency=data_sufficiency,
            reason_codes=reason_codes,
            risk_score=round(composite_risk, 3),
            slope_per_min=round(slope_per_min, 4),
            acceleration=round(acceleration, 4),
            summary=summary,
            metadata={
                "base_risk": round(base_risk, 3),
                "temp_risk": round(temp_risk, 3) if temp_risk is not None else None,
                "is_spike": is_spike,
                "max_prior_risk": round(max_prior_risk, 3)
            }
        )
