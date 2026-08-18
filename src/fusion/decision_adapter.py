import time
import uuid
import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Union

from src.fusion.multimodal_fusion import FusedEvidence

@dataclass
class SystemEvent:
    """
    Abstract system event produced by the DecisionAdapter for consumption by the V3.6 FSM and actuator layer.
    Hides camera/CV model specifics while preserving complete multimodal provenance.
    """
    event_id: str
    timestamp: str
    event_type: str  # "SYSTEM_STATE_NORMAL", "SYSTEM_STATE_WARNING", "SYSTEM_STATE_CRITICAL", "SYSTEM_STATE_UNKNOWN_ANOMALY", "SYSTEM_STATE_SENSOR_FAULT"
    target_fsm_state: str  # "NORMAL", "WARNING", "CRITICAL", "UNKNOWN_ANOMALY", "SENSOR_FAULT"
    reason_code: str
    reasoning: str
    multimodal: bool
    sensor_contribution: bool
    visual_contribution: bool
    conflict_detected: bool
    adapter_time_ms: float
    provenance: Dict[str, Any] = field(default_factory=dict)


class DecisionAdapter:
    """
    Lightweight, deterministic adapter converting V4.5 FusedEvidence / decision dictionaries
    into abstract SystemEvents for the V3.6 FSM and actuator manager.
    Supports event deduplication to avoid redundant actuation triggers.
    """
    def __init__(self, deduplication_window_sec: float = 1.0):
        self.deduplication_window_sec = deduplication_window_sec
        self.last_event_type: Optional[str] = None
        self.last_event_timestamp: Optional[float] = None
        self.last_fusion_id: Optional[str] = None

    def adapt(self, fused_decision: Union[FusedEvidence, Dict[str, Any]]) -> SystemEvent:
        """
        Converts a V4.5 fused decision into a standardized SystemEvent.
        Measures decision_adapter_time_ms.
        """
        start_time = time.perf_counter()

        # Extract dictionary payload
        if hasattr(fused_decision, "__dict__") and not isinstance(fused_decision, dict):
            f_dict = fused_decision.__dict__
        elif isinstance(fused_decision, dict):
            f_dict = fused_decision
        else:
            raise TypeError("Input must be a FusedEvidence object or dictionary")

        fusion_meta = f_dict.get("fusion", {})
        final_state = fusion_meta.get("final_state", f_dict.get("final_state", "NORMAL"))
        reason_code = fusion_meta.get("reason_code", f_dict.get("reason_code", "ML_NORMAL_AIS_NORMAL"))
        reasoning = fusion_meta.get("reasoning", f_dict.get("reasoning", ""))
        is_multimodal = fusion_meta.get("multimodal", f_dict.get("multimodal", False))

        # Map state to abstract system event type
        event_type_map = {
            "NORMAL": "SYSTEM_STATE_NORMAL",
            "WARNING": "SYSTEM_STATE_WARNING",
            "CRITICAL": "SYSTEM_STATE_CRITICAL",
            "UNKNOWN_ANOMALY": "SYSTEM_STATE_UNKNOWN_ANOMALY",
            "SENSOR_FAULT": "SYSTEM_STATE_SENSOR_FAULT"
        }
        event_type = event_type_map.get(final_state, "SYSTEM_STATE_NORMAL")

        # Determine modal contributions
        has_sensor = "ml_evidence" in f_dict and f_dict["ml_evidence"] is not None
        has_visual = is_multimodal and ("visual_evidence" in f_dict and f_dict["visual_evidence"] is not None)

        # Conflict Detection Check
        conflict_detected = (reason_code in [
            "VISUAL_EARLY_WARNING",
            "VISUAL_DISCONFIRMED_NORMAL",
            "VISUAL_TURBIDITY_MITIGATED"
        ])

        now_str = datetime.datetime.now().isoformat()
        event_id = f"evt_{uuid.uuid4().hex[:8]}"

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        provenance_data = {
            "fusion_version": f_dict.get("system_metadata", {}).get("fusion_version", "1.0.0"),
            "confidence_band": fusion_meta.get("confidence_band", "HIGH"),
            "dataset": f_dict.get("dataset", "unknown"),
            "raw_visual_state": f_dict.get("visual_evidence", {}).get("visual_state") if has_visual else None,
            "raw_sensor_ml": f_dict.get("ml_evidence", {}).get("predicted_class") if has_sensor else None
        }

        return SystemEvent(
            event_id=event_id,
            timestamp=now_str,
            event_type=event_type,
            target_fsm_state=final_state,
            reason_code=reason_code,
            reasoning=reasoning,
            multimodal=is_multimodal,
            sensor_contribution=has_sensor,
            visual_contribution=has_visual,
            conflict_detected=conflict_detected,
            adapter_time_ms=round(duration_ms, 3),
            provenance=provenance_data
        )

    def is_duplicate(self, event: SystemEvent) -> bool:
        """Determines if an event is a duplicate within the deduplication window."""
        now = time.time()
        if (
            self.last_event_type == event.event_type and
            self.last_event_timestamp is not None and
            (now - self.last_event_timestamp) < self.deduplication_window_sec
        ):
            return True

        self.last_event_type = event.event_type
        self.last_event_timestamp = now
        return False
