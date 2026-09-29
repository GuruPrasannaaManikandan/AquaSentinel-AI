import time
import uuid
import logging
import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Tuple

from src.fusion.risk_trajectory import RiskTrendResult

logger = logging.getLogger(__name__)


@dataclass
class ActuatorDecision:
    """
    Auditable record of an actuator command proposal, safety gate evaluation,
    approval status, and verification feedback.
    """
    timestamp: str
    device_id: str
    command_id: str
    requested_action: str  # "ACTIVATE_PUMP", "ACTIVATE_BUZZER", "DEACTIVATE_PUMP", "DEACTIVATE_BUZZER", "NO_ACTION"
    approved_action: str   # "APPROVED", "BLOCKED", "NO_ACTION"
    policy_state: str      # "MONITOR", "WATCH", "PREPARE", "INTERVENE", "EMERGENCY", "RECOVERY"
    risk_state: str        # e.g., "NORMAL", "WATCH", "EARLY_WARNING", "HIGH_RISK", "CRITICAL"
    evidence_summary: Dict[str, Any] = field(default_factory=dict)
    safety_checks: Dict[str, bool] = field(default_factory=dict)
    blocked_reasons: List[str] = field(default_factory=list)
    execution_status: str = "COMMAND_NOT_VERIFIED"  # "COMMAND_ISSUED", "COMMAND_NOT_VERIFIED", "COMMAND_VERIFIED", "COMMAND_FAILED", "COMMAND_TIMEOUT"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ActuatorSafetyGate:
    """
    Multi-barrier safety gate interceptor.
    Prevents raw ML predictions or single uncorroborated noisy probes
    from triggering unsafe physical actuator outputs.
    """
    def __init__(
        self,
        pump_risk_threshold: float = 0.50,
        buzzer_risk_threshold: float = 0.80,
        min_sensor_quality: float = 0.70,
        min_optical_quality: float = 0.65,
        pump_cooldown_sec: float = 30.0,
        buzzer_cooldown_sec: float = 60.0,
        max_commands_per_minute: int = 3
    ):
        self.pump_risk_threshold = pump_risk_threshold
        self.buzzer_risk_threshold = buzzer_risk_threshold
        self.min_sensor_quality = min_sensor_quality
        self.min_optical_quality = min_optical_quality
        self.pump_cooldown_sec = pump_cooldown_sec
        self.buzzer_cooldown_sec = buzzer_cooldown_sec
        self.max_commands_per_minute = max_commands_per_minute

        # State tracking per device: {device_id: {"last_pump_time": float, "last_buzzer_time": float, "cmd_timestamps": deque}}
        self.device_state: Dict[str, Dict[str, Any]] = {}

    def _get_device_state(self, device_id: str) -> Dict[str, Any]:
        if device_id not in self.device_state:
            self.device_state[device_id] = {
                "last_pump_time": 0.0,
                "last_buzzer_time": 0.0,
                "command_timestamps": [],
                "active_actuators": {"pump": False, "buzzer": False}
            }
        return self.device_state[device_id]

    def reset_device(self, device_id: str):
        """Resets safety gate tracking for a device."""
        if device_id in self.device_state:
            del self.device_state[device_id]

    def evaluate_gate(
        self,
        device_id: str,
        requested_action: str,
        policy_state: str,
        risk_score: float,
        sensor_quality: Optional[Dict[str, Any]],
        visual_evidence: Optional[Dict[str, Any]],
        multimodal_intel: Optional[Dict[str, Any]],
        is_override: bool = False,
        now_sec: Optional[float] = None
    ) -> Tuple[bool, Dict[str, bool], List[str]]:
        """
        Evaluates safety barriers for the requested actuator action.
        Returns: (is_approved, safety_checks_dict, blocked_reasons_list)
        """
        now = now_sec if now_sec is not None else time.time()
        dev_state = self._get_device_state(device_id)

        # Deactivations and NO_ACTION are inherently safe
        if requested_action in ["NO_ACTION", "DEACTIVATE_PUMP", "DEACTIVATE_BUZZER"]:
            return True, {"safe_action": True}, []

        # Emergency Operator Override: bypasses automated gates if explicitly flagged
        if is_override:
            dev_state["command_timestamps"].append(now)
            return True, {"emergency_override_bypassed": True}, ["MANUAL_OVERRIDE_APPLIED"]

        checks: Dict[str, bool] = {}
        blocked: List[str] = []

        # 1. Ecological Risk Threshold Gate
        if "BUZZER" in requested_action:
            threshold_ok = risk_score >= self.buzzer_risk_threshold and policy_state == "EMERGENCY"
            checks["risk_threshold_ok"] = threshold_ok
            if not threshold_ok:
                blocked.append(f"RISK_BELOW_BUZZER_THRESHOLD ({risk_score:.2f} < {self.buzzer_risk_threshold})")
        elif "PUMP" in requested_action:
            threshold_ok = risk_score >= self.pump_risk_threshold and policy_state in ["INTERVENE", "EMERGENCY"]
            checks["risk_threshold_ok"] = threshold_ok
            if not threshold_ok:
                blocked.append(f"RISK_BELOW_PUMP_THRESHOLD ({risk_score:.2f} < {self.pump_risk_threshold})")
        else:
            checks["risk_threshold_ok"] = True

        # 2. Evidence Quality Gate
        sq = sensor_quality.get("q_sensor", 1.0) if sensor_quality else 1.0
        sensor_q_ok = sq >= self.min_sensor_quality
        checks["sensor_quality_ok"] = sensor_q_ok
        if not sensor_q_ok:
            blocked.append(f"SENSOR_QUALITY_DEGRADED (Q_s={sq:.2f} < {self.min_sensor_quality})")

        optical_q_ok = True
        if visual_evidence:
            vq = visual_evidence.get("quality_index", 1.0)
            optical_q_ok = vq >= self.min_optical_quality
            checks["optical_quality_ok"] = optical_q_ok
            if not optical_q_ok and visual_evidence.get("visual_state") == "BLOOM_EVIDENCE":
                blocked.append(f"OPTICAL_QUALITY_DEGRADED (Q_v={vq:.2f} < {self.min_optical_quality})")
        else:
            checks["optical_quality_ok"] = True

        # 3. Multimodal Corroboration Gate
        # Emergency actuation must have at least 2 corroborating modalities or high concordance
        if multimodal_intel:
            concordance = multimodal_intel.get("concordance_score", 1.0)
            conflict = multimodal_intel.get("conflict_detected", False)
            dominance_prevented = multimodal_intel.get("dominance_prevented", False)
            available_mods = multimodal_intel.get("valid_modalities", 1)

            # Block if cross-modality conflict is present
            no_conflict = not conflict
            checks["no_conflict_gate"] = no_conflict
            if not no_conflict:
                blocked.append(f"CROSS_MODALITY_CONFLICT_PRESENT ({multimodal_intel.get('conflict_type')})")

            # Block if dominance prevention intervened
            checks["dominance_prevented_ok"] = not dominance_prevented
            if dominance_prevented:
                blocked.append("SINGLE_MODALITY_DOMINANCE_PREVENTED")

            # Corroboration requirement for emergency buzzer
            if "BUZZER" in requested_action:
                corroborated = available_mods >= 2 and concordance >= 0.60
                checks["multimodal_corroborated"] = corroborated
                if not corroborated:
                    blocked.append("INSUFFICIENT_MULTIMODAL_CORROBORATION_FOR_EMERGENCY")
            else:
                checks["multimodal_corroborated"] = True
        else:
            checks["no_conflict_gate"] = True
            checks["dominance_prevented_ok"] = True
            checks["multimodal_corroborated"] = True

        # 4. Actuator Cooldown Gate
        if "PUMP" in requested_action:
            last_t = dev_state["last_pump_time"]
            cooldown_ok = (now - last_t) >= self.pump_cooldown_sec
            checks["pump_cooldown_ok"] = cooldown_ok
            if not cooldown_ok:
                remaining = round(self.pump_cooldown_sec - (now - last_t), 1)
                blocked.append(f"PUMP_COOLDOWN_ACTIVE ({remaining}s remaining)")
        elif "BUZZER" in requested_action:
            last_t = dev_state["last_buzzer_time"]
            cooldown_ok = (now - last_t) >= self.buzzer_cooldown_sec
            checks["buzzer_cooldown_ok"] = cooldown_ok
            if not cooldown_ok:
                remaining = round(self.buzzer_cooldown_sec - (now - last_t), 1)
                blocked.append(f"BUZZER_COOLDOWN_ACTIVE ({remaining}s remaining)")

        # 5. Command Rate Limit Gate (max N commands per 60s)
        # Purge timestamps older than 60s
        dev_state["command_timestamps"] = [t for t in dev_state["command_timestamps"] if (now - t) < 60.0]
        rate_limit_ok = len(dev_state["command_timestamps"]) < self.max_commands_per_minute
        checks["rate_limit_ok"] = rate_limit_ok
        if not rate_limit_ok:
            blocked.append(f"RATE_LIMIT_EXCEEDED ({len(dev_state['command_timestamps'])} commands in last 60s)")

        # Final Approval Determination
        is_approved = len(blocked) == 0

        if is_approved:
            dev_state["command_timestamps"].append(now)
            if "PUMP" in requested_action:
                dev_state["last_pump_time"] = now
            if "BUZZER" in requested_action:
                dev_state["last_buzzer_time"] = now

        return is_approved, checks, blocked


class AutonomousRecoveryManager:
    """
    V8 Multi-Vector Recovery Intelligence Manager.
    Extends V5.6 K=3 recovery hysteresis with multi-vector health checks:
    - K consecutive verified NORMAL cycles
    - Multimodal concordance in recovery
    - Sensor quality restored
    - Camera quality restored
    - Actuator cooldown satisfied
    - Safe return to MONITOR policy
    """
    def __init__(self, required_normal_cycles: int = 3):
        self.required_normal_cycles = required_normal_cycles
        self.device_recovery: Dict[str, Dict[str, Any]] = {}

    def _get_state(self, device_id: str) -> Dict[str, Any]:
        if device_id not in self.device_recovery:
            self.device_recovery[device_id] = {
                "in_elevated_state": False,
                "highest_policy": "MONITOR",
                "consecutive_normal_cycles": 0,
                "active_policy": "MONITOR"
            }
        return self.device_recovery[device_id]

    def reset_device(self, device_id: str):
        if device_id in self.device_recovery:
            del self.device_recovery[device_id]

    def evaluate_recovery(
        self,
        device_id: str,
        target_policy: str,
        risk_trend: RiskTrendResult,
        sensor_quality_ok: bool = True,
        optical_quality_ok: bool = True
    ) -> Tuple[str, str, int]:
        """
        Applies multi-vector recovery logic.
        Returns: (effective_policy, recovery_phase, consecutive_normals)
        where recovery_phase in ["NORMAL", "ELEVATED", "RECOVERY_HOLD", "RECOVERED"]
        """
        st = self._get_state(device_id)
        is_elevated = target_policy in ["PREPARE", "INTERVENE", "EMERGENCY"]

        if is_elevated:
            st["in_elevated_state"] = True
            st["highest_policy"] = target_policy
            st["consecutive_normal_cycles"] = 0
            st["active_policy"] = target_policy
            return target_policy, "ELEVATED", 0

        # Target policy is MONITOR or WATCH
        if not st["in_elevated_state"]:
            st["consecutive_normal_cycles"] = 0
            st["active_policy"] = target_policy
            return target_policy, "NORMAL", 0

        # System was in an elevated policy and is now observing nominal conditions
        trajectory_declining = risk_trend.trajectory in ["DECLINING", "RECOVERING", "STABLE"]
        all_probes_healthy = sensor_quality_ok and optical_quality_ok

        if trajectory_declining and all_probes_healthy:
            st["consecutive_normal_cycles"] += 1
        else:
            # Fluctuation or probe degradation resets recovery count
            st["consecutive_normal_cycles"] = max(0, st["consecutive_normal_cycles"] - 1)

        count = st["consecutive_normal_cycles"]

        if count < self.required_normal_cycles:
            # Hold in safe RECOVERY/WATCH policy
            hold_policy = "WATCH" if st["highest_policy"] == "PREPARE" else "RECOVERY"
            st["active_policy"] = hold_policy
            return hold_policy, "RECOVERY_HOLD", count
        else:
            # Recovery confirmed after K consecutive stable nominal cycles
            st["in_elevated_state"] = False
            st["consecutive_normal_cycles"] = 0
            st["highest_policy"] = "MONITOR"
            st["active_policy"] = "MONITOR"
            return "MONITOR", "RECOVERED", count


class AutonomousResponseEngine:
    """
    V8 Autonomous Response & Safety Engine.
    Unifies:
    1. Response Policy Engine (MONITOR, WATCH, PREPARE, INTERVENE, EMERGENCY, RECOVERY)
    2. Multi-barrier Actuator Safety Gate
    3. Multi-vector Recovery Intelligence
    4. Feedback & Verification Tracking (COMMAND_ISSUED, COMMAND_NOT_VERIFIED, COMMAND_VERIFIED, COMMAND_FAILED, COMMAND_TIMEOUT)
    """
    def __init__(
        self,
        pump_cooldown_sec: float = 30.0,
        buzzer_cooldown_sec: float = 60.0
    ):
        self.safety_gate = ActuatorSafetyGate(
            pump_cooldown_sec=pump_cooldown_sec,
            buzzer_cooldown_sec=buzzer_cooldown_sec
        )
        self.recovery_manager = AutonomousRecoveryManager(required_normal_cycles=3)

    def evaluate_response(
        self,
        device_id: str,
        multimodal_decision: Dict[str, Any],
        risk_trend: RiskTrendResult,
        sensor_quality: Optional[Dict[str, Any]] = None,
        visual_evidence: Optional[Dict[str, Any]] = None,
        is_override: bool = False,
        now_sec: Optional[float] = None
    ) -> Tuple[str, ActuatorDecision]:
        """
        Determines the appropriate autonomous policy, evaluates safety gates,
        and produces an auditable ActuatorDecision record.
        Returns: (policy_state, ActuatorDecision)
        """
        ts = multimodal_decision.get("timestamp") or datetime.datetime.now().isoformat()
        cmd_id = f"cmd_{uuid.uuid4().hex[:8]}"

        fusion_info = multimodal_decision.get("fusion", {})
        mm_intel = multimodal_decision.get("multimodal_intelligence", {})
        state = mm_intel.get("synthesized_state") or fusion_info.get("final_state", "NORMAL")
        risk_score = risk_trend.risk_score

        # Transient spike protection
        is_spike = risk_trend.metadata.get("is_spike", False) or ("SINGLE_SPIKE_DAMPENED" in risk_trend.reason_codes)

        # 1. Map Ecological State & Risk Trajectory to Target Policy
        if is_spike:
            # Single uncorroborated probe spike: clamp to WATCH, suppress physical actuation
            target_policy = "WATCH"
            requested_action = "NO_ACTION"
        elif state in ["CRITICAL", "BLOOM_CONFIRMED"] and risk_score >= 0.80 and risk_trend.horizon_state == "ACTIVE_EVENT":
            target_policy = "EMERGENCY"
            requested_action = "ACTIVATE_BUZZER"
        elif state in ["HIGH_RISK", "CRITICAL"] or (risk_score >= 0.60 and risk_trend.trajectory in ["ACCELERATING", "RISING"]):
            target_policy = "INTERVENE"
            requested_action = "ACTIVATE_PUMP"
        elif state in ["EARLY_WARNING", "WATCH"] or risk_trend.horizon_state in ["DEVELOPING_RISK", "NEAR_TERM_RISK"]:
            if risk_trend.trajectory in ["ACCELERATING", "RISING"] and risk_score >= 0.40:
                target_policy = "PREPARE"
                requested_action = "NO_ACTION"
            else:
                target_policy = "WATCH"
                requested_action = "NO_ACTION"
        elif state == "NORMAL":
            target_policy = "MONITOR"
            requested_action = "NO_ACTION"
        else:
            target_policy = "WATCH"
            requested_action = "NO_ACTION"

        # 2. Multi-Vector Recovery Filter
        sq_ok = sensor_quality.get("is_valid", True) if sensor_quality else True
        vq_ok = visual_evidence.get("valid", True) if visual_evidence else True
        effective_policy, recovery_phase, recovery_count = self.recovery_manager.evaluate_recovery(
            device_id=device_id,
            target_policy=target_policy,
            risk_trend=risk_trend,
            sensor_quality_ok=sq_ok,
            optical_quality_ok=vq_ok
        )

        # If held in recovery, prevent emergency actions
        if recovery_phase == "RECOVERY_HOLD" and requested_action in ["ACTIVATE_BUZZER", "ACTIVATE_PUMP"]:
            requested_action = "NO_ACTION"

        # 3. Actuator Safety Gate Evaluation
        is_approved, checks, blocked = self.safety_gate.evaluate_gate(
            device_id=device_id,
            requested_action=requested_action,
            policy_state=effective_policy,
            risk_score=risk_score,
            sensor_quality=sensor_quality,
            visual_evidence=visual_evidence,
            multimodal_intel=mm_intel,
            is_override=is_override,
            now_sec=now_sec
        )

        approved_action = "APPROVED" if is_approved and requested_action != "NO_ACTION" else (
            "NO_ACTION" if requested_action == "NO_ACTION" else "BLOCKED"
        )

        # Execution Status: explicitly represents verification status
        if approved_action == "APPROVED":
            execution_status = "COMMAND_ISSUED"
        elif approved_action == "BLOCKED":
            execution_status = "COMMAND_FAILED"
        else:
            execution_status = "COMMAND_NOT_VERIFIED"

        evidence_summary = {
            "risk_score": risk_score,
            "trajectory": risk_trend.trajectory,
            "horizon_state": risk_trend.horizon_state,
            "data_sufficiency": risk_trend.data_sufficiency,
            "concordance_score": mm_intel.get("concordance_score", 1.0),
            "conflict_detected": mm_intel.get("conflict_detected", False),
            "recovery_phase": recovery_phase,
            "recovery_count": recovery_count
        }

        decision = ActuatorDecision(
            timestamp=ts,
            device_id=device_id,
            command_id=cmd_id,
            requested_action=requested_action,
            approved_action=approved_action,
            policy_state=effective_policy,
            risk_state=state,
            evidence_summary=evidence_summary,
            safety_checks=checks,
            blocked_reasons=blocked,
            execution_status=execution_status,
            metadata={
                "target_policy": target_policy,
                "effective_policy": effective_policy,
                "recovery_phase": recovery_phase,
                "is_override": is_override
            }
        )

        return effective_policy, decision

    def update_verification_status(
        self,
        decision: ActuatorDecision,
        verification_status: str
    ) -> ActuatorDecision:
        """
        Updates an existing decision with verified feedback
        (e.g., COMMAND_VERIFIED, COMMAND_TIMEOUT, COMMAND_FAILED).
        """
        valid_statuses = [
            "COMMAND_ISSUED",
            "COMMAND_NOT_VERIFIED",
            "COMMAND_VERIFIED",
            "COMMAND_FAILED",
            "COMMAND_TIMEOUT"
        ]
        if verification_status in valid_statuses:
            decision.execution_status = verification_status
        return decision
