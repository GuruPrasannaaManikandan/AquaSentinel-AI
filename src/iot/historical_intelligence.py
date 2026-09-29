import time
import math
import logging
import datetime
import numpy as np
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Tuple


@dataclass
class ChannelBaseline:
    """Statistical summary of historical baseline distribution for a single sensor channel."""
    metric_name: str
    mean: float
    std: float
    median: float
    min_val: float
    max_val: float
    sample_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DigitalEcosystemState:
    """
    Structured digital twin state of the monitored aquatic ecosystem site.
    Preserves rolling historical baselines, contextual Z-scores, and recent event history.
    """
    device_id: str
    last_updated: str
    total_observations: int
    baselines: Dict[str, Any] = field(default_factory=dict)
    deviations_from_baseline: Dict[str, float] = field(default_factory=dict)
    recent_events: List[Dict[str, Any]] = field(default_factory=list)
    ecosystem_health_index: float = 1.0  # [0.0, 1.0]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HistoricalIntelligenceEngine:
    """
    V5.7 / V5.8 Historical Ecosystem Intelligence & Digital State Engine.
    Maintains rolling baselines per device over a configurable history window (default 100 points).
    Computes moving means, standard deviations, and contextual deviation Z-scores to distinguish
    site-specific natural variation from true ecological disturbances.
    """
    def __init__(self, max_history_points: int = 100):
        self.max_history_points = max_history_points
        # In-memory history queues: {device_id: {metric: deque(maxlen=max_history_points)}}
        self.history_buffers: Dict[str, Dict[str, deque]] = {}
        # Recent threat events: {device_id: deque(maxlen=20)}
        self.event_buffers: Dict[str, deque] = {}
        self.observation_counters: Dict[str, int] = {}

    def _get_metric_deque(self, device_id: str, metric: str) -> deque:
        if device_id not in self.history_buffers:
            self.history_buffers[device_id] = {
                "temperature_c": deque(maxlen=self.max_history_points),
                "ph": deque(maxlen=self.max_history_points),
                "turbidity_ntu": deque(maxlen=self.max_history_points),
                "dissolved_oxygen_mg_l": deque(maxlen=self.max_history_points),
                "salinity_ppt": deque(maxlen=self.max_history_points)
            }
            self.event_buffers[device_id] = deque(maxlen=20)
            if device_id not in self.observation_counters:
                self.observation_counters[device_id] = 0

        if metric not in self.history_buffers[device_id]:
            self.history_buffers[device_id][metric] = deque(maxlen=self.max_history_points)

        return self.history_buffers[device_id][metric]

    def reset_device(self, device_id: str):
        """Clears historical baseline for a device."""
        if device_id in self.history_buffers:
            del self.history_buffers[device_id]
        if device_id in self.event_buffers:
            del self.event_buffers[device_id]
        if device_id in self.observation_counters:
            del self.observation_counters[device_id]

    def update_and_evaluate(
        self,
        device_id: str,
        telemetry: Dict[str, Any],
        decision: Optional[Dict[str, Any]] = None
    ) -> DigitalEcosystemState:
        """
        Ingests observation, updates rolling channel baselines, calculates Z-score deviations,
        and returns the current DigitalEcosystemState.
        """
        now_iso = telemetry.get("timestamp") or datetime.datetime.now().isoformat()
        self.observation_counters[device_id] = self.observation_counters.get(device_id, 0) + 1

        metrics = ["temperature_c", "ph", "turbidity_ntu", "dissolved_oxygen_mg_l", "salinity_ppt"]

        baselines = {}
        deviations = {}

        for m in metrics:
            val = telemetry.get(m)
            if val is not None and isinstance(val, (int, float)) and math.isfinite(val):
                dq = self._get_metric_deque(device_id, m)
                dq.append(float(val))

                arr = np.array(dq, dtype=np.float32)
                mean_val = float(np.mean(arr))
                std_val = float(np.std(arr))
                med_val = float(np.median(arr))
                min_v = float(np.min(arr))
                max_v = float(np.max(arr))

                baseline = ChannelBaseline(
                    metric_name=m,
                    mean=round(mean_val, 3),
                    std=round(std_val, 3),
                    median=round(med_val, 3),
                    min_val=round(min_v, 3),
                    max_val=round(max_v, 3),
                    sample_count=len(arr)
                )
                baselines[m] = baseline.to_dict()

                # Calculate Z-score deviation from site baseline
                denom = max(std_val, 0.05)
                z_score = (float(val) - mean_val) / denom
                deviations[f"{m}_zscore"] = round(float(z_score), 2)
            else:
                baselines[m] = None
                deviations[f"{m}_zscore"] = 0.0

        # Log significant decision event if present
        if decision:
            fusion = decision.get("fusion", {})
            st = fusion.get("ecological_state") or fusion.get("final_state") or "NORMAL"
            if st != "NORMAL":
                event_entry = {
                    "timestamp": now_iso,
                    "state": st,
                    "reason_code": fusion.get("reason_code", "UNKNOWN"),
                    "risk_score": fusion.get("composite_risk_score", 0.0)
                }
                if device_id in self.event_buffers:
                    self.event_buffers[device_id].append(event_entry)

        events_list = list(self.event_buffers.get(device_id, []))

        # Calculate overall ecosystem health index [0.0, 1.0]
        # Health decreases with extreme Z-scores
        z_magnitudes = [abs(v) for k, v in deviations.items() if k.endswith("_zscore")]
        mean_z = float(np.mean(z_magnitudes)) if z_magnitudes else 0.0
        health_idx = max(0.0, min(1.0, 1.0 - (mean_z * 0.15)))

        return DigitalEcosystemState(
            device_id=device_id,
            last_updated=now_iso,
            total_observations=self.observation_counters[device_id],
            baselines=baselines,
            deviations_from_baseline=deviations,
            recent_events=events_list,
            ecosystem_health_index=round(health_idx, 3)
        )
