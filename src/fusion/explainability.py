import time
import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Tuple


@dataclass
class ExplanationResult:
    """
    Structured explainable AI (XAI) output contract.
    Provides transparent mathematical attribution across sensing modalities,
    key driving physical factors, and recovery hysteresis status.
    """
    device_id: str
    timestamp: str
    state: str  # "NORMAL", "WATCH", "EARLY_WARNING", "HIGH_RISK", "BLOOM_CONFIRMED"
    risk_score: float  # [0.0, 1.0]
    modality_attribution: Dict[str, float] = field(default_factory=dict)  # Percentages summing to 100.0%
    feature_attribution: Dict[str, float] = field(default_factory=dict)   # Percentages summing to 100.0%
    key_factors: List[str] = field(default_factory=list)
    recovery_status: str = "STABLE"  # "STABLE", "RECOVERY_HOLD", "RECOVERED"
    recovery_cycles_confirmed: int = 0
    recovery_cycles_required: int = 3
    summary: str = ""
    # V7 Multimodal Intelligence Extensions
    concordance_state: Optional[str] = None
    concordance_score: Optional[float] = None
    conflict_detected: bool = False
    conflict_type: Optional[str] = None
    prescriptive_action: Optional[str] = None
    dominance_prevented: bool = False
    missing_modalities: List[str] = field(default_factory=list)
    degraded_modalities: List[str] = field(default_factory=list)
    multimodal_explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ExplainabilityEngine:
    """
    V5.6 Explainable Decision Engine.
    Decomposes evidential multimodal decisions into mathematically transparent
    modality attribution vectors, feature-level contribution percentages, and plain-language
    diagnostic justifications.
    """
    def __init__(self):
        pass

    def explain(
        self,
        fused_decision: Dict[str, Any],
        device_id: Optional[str] = None
    ) -> ExplanationResult:
        """
        Generates an ExplanationResult from a fused decision payload.
        """
        dev_id = device_id or fused_decision.get("device_id", "UNKNOWN_DEVICE")
        ts = fused_decision.get("timestamp") or datetime.datetime.now().isoformat()

        fusion = fused_decision.get("fusion", {})
        final_state = fusion.get("final_state", "NORMAL")
        eco_state = fusion.get("ecological_state", final_state)
        risk_score = float(fusion.get("composite_risk_score", 0.0))
        reason_code = fusion.get("reason_code", "OK")

        ml_ev = fused_decision.get("ml_evidence", {})
        ais_ev = fused_decision.get("ais_evidence", {})
        vis_ev = fused_decision.get("visual_evidence")
        temp_ev = fused_decision.get("temporal_evidence")
        sensor_q = fused_decision.get("sensor_quality")
        weights = fusion.get("modality_weights", {})

        # 1. Modality Attribution Calculation
        # Raw contributions: weight * threat
        w_s = float(weights.get("sensor", 0.40))
        w_v = float(weights.get("visual", 0.0))
        w_t = float(weights.get("temporal", 0.0))
        w_ais = float(weights.get("ais", 0.20))

        # Threat signals [0.0, 1.0]
        t_s = 0.85 if ml_ev.get("dangerous_class", False) else 0.05
        t_ais = float(ais_ev.get("anomaly_score", 0.05))

        t_v = 0.0
        if vis_ev is not None and isinstance(vis_ev, dict):
            v_st = vis_ev.get("visual_state", "UNCERTAIN")
            if v_st == "BLOOM_EVIDENCE":
                t_v = float(vis_ev.get("effective_confidence", 0.90))
            elif v_st == "TURBID_DISCOLORATION":
                t_v = 0.15

        t_t = 0.0
        if temp_ev is not None and isinstance(temp_ev, dict):
            t_t = float(temp_ev.get("trajectory_risk_score", 0.0))

        # Raw modality contribution masses
        mass_s = max(0.001, w_s * t_s)
        mass_v = max(0.001, w_v * t_v) if w_v > 0 else 0.0
        mass_t = max(0.001, w_t * t_t) if w_t > 0 else 0.0
        mass_ais = max(0.001, w_ais * t_ais)

        total_mass = mass_s + mass_v + mass_t + mass_ais
        modality_attribution = {
            "sensor_pct": round((mass_s / total_mass) * 100.0, 2),
            "visual_pct": round((mass_v / total_mass) * 100.0, 2),
            "temporal_pct": round((mass_t / total_mass) * 100.0, 2),
            "ais_pct": round((mass_ais / total_mass) * 100.0, 2)
        }

        # 2. Feature-Level Attribution Calculation
        feat_masses = {}
        # Sensor probe contributions
        if temp_ev and "metric_trends" in temp_ev:
            trends = temp_ev["metric_trends"]
            ph_trend = trends.get("ph", {})
            turb_trend = trends.get("turbidity_ntu", {})
            temp_trend = trends.get("temperature_c", {})
            do_trend = trends.get("dissolved_oxygen_mg_l", {})

            ph_val = float(ph_trend.get("current_value") or 7.0)
            turb_val = float(turb_trend.get("current_value") or 5.0)
            temp_val = float(temp_trend.get("current_value") or 20.0)
            do_val = float(do_trend.get("current_value") or 8.0)

            feat_masses["ph_elevation"] = max(0.05, (ph_val - 7.0) * 0.35 + ph_trend.get("slope_per_min", 0) * 2.0)
            feat_masses["turbidity_surge"] = max(0.05, (turb_val / 50.0) * 0.40 + turb_trend.get("slope_per_min", 0) * 0.1)
            feat_masses["temperature_warming"] = max(0.05, temp_trend.get("slope_per_min", 0) * 1.5)
            feat_masses["photosynthetic_do"] = max(0.05, do_trend.get("slope_per_min", 0) * 1.0)
        else:
            feat_masses["ph_elevation"] = 0.30 if ml_ev.get("dangerous_class") else 0.10
            feat_masses["turbidity_surge"] = 0.25 if ml_ev.get("dangerous_class") else 0.10
            feat_masses["temperature_warming"] = 0.15
            feat_masses["photosynthetic_do"] = 0.10

        feat_masses["visual_green_scum"] = max(0.05, t_v * 0.50) if w_v > 0 else 0.0
        feat_masses["ais_novelty"] = max(0.05, t_ais * 0.40)

        total_feat = sum(feat_masses.values())
        feature_attribution = {
            k: round((v / total_feat) * 100.0, 2)
            for k, v in feat_masses.items()
        }

        # 3. V7 Multimodal Alignment & Intelligence Extractions
        concordance = fused_decision.get("concordance") or fused_decision.get("multimodal_intelligence", {}).get("concordance", {})
        conflict = fused_decision.get("conflict") or fused_decision.get("multimodal_intelligence", {}).get("conflict", {})
        state_res = fused_decision.get("multimodal_state") or fused_decision.get("multimodal_intelligence", {}).get("state_result", {})
        snapshot = fused_decision.get("multimodal_snapshot") or {}

        conc_state = concordance.get("concordance_state")
        conc_score = float(concordance.get("agreement_score", 0.0)) if concordance.get("agreement_score") is not None else None
        has_conflict = bool(conflict.get("conflict_detected", False))
        conf_type = conflict.get("conflict_type", "NONE")
        presc_action = conflict.get("prescriptive_action") or conflict.get("recommended_handling", "STANDARD_FUSION")
        dom_prevented = bool(state_res.get("dominance_prevented", False))
        missing_mods = list(snapshot.get("missing_modalities", []))
        degraded_mods = list(snapshot.get("degraded_modalities", []))

        # 4. Plain Language Key Factors Extraction
        key_factors = []

        # Concordance explanation
        if conc_state and conc_state != "INCONCLUSIVE":
            key_factors.append(f"Multimodal Concordance: {conc_state} (agreement score={conc_score:.1%}).")

        # Conflict explanation
        if has_conflict and conf_type != "NONE":
            key_factors.append(f"Cross-Modality Conflict Detected: {conf_type} ({conflict.get('explanation', '')}). Prescribed action: {presc_action}.")

        # Dominance Prevention explanation
        if dom_prevented:
            key_factors.append("Single-Modality Dominance Prevented: Single uncorroborated noisy probe signal held to EARLY_WARNING to prevent false emergency shutoff.")

        # Missing / degraded modalities explanation
        if missing_mods:
            key_factors.append(f"Missing Modality Fallback: [{', '.join(missing_mods)}] offline; operating gracefully on available evidence channels.")

        if vis_ev and vis_ev.get("visual_state") == "BLOOM_EVIDENCE":
            conf = vis_ev.get("confidence", 0.0)
            qv = vis_ev.get("q_visual", 1.0)
            key_factors.append(f"Camera detected surface algal bloom scum (conf={conf:.2%}, Q_visual={qv:.2f}).")
        elif vis_ev and vis_ev.get("visual_state") == "NO_VISUAL_BLOOM":
            key_factors.append("Camera confirms clear water body (NO_VISUAL_BLOOM, disconfirming bloom scum).")
        elif vis_ev and vis_ev.get("visual_state") == "TURBID_DISCOLORATION":
            key_factors.append("Camera identified sediment turbidity without photosynthetic algal scum.")
        elif vis_ev and vis_ev.get("visual_state") in ["CAMERA_FAULT", "INFERENCE_FAILURE"]:
            key_factors.append(f"Optical modality degraded ({vis_ev.get('visual_state')}); reliance transferred to water chemistry sensors.")

        if temp_ev and temp_ev.get("lead_indicators"):
            for ind in temp_ev["lead_indicators"]:
                key_factors.append(f"Temporal Trend: {ind}")

        if ml_ev.get("dangerous_class"):
            key_factors.append(f"Supervised ML flagged dangerous water quality class ({ml_ev.get('predicted_class')}, conf={ml_ev.get('confidence', 0):.2%}).")

        if ais_ev.get("is_anomaly"):
            imm_type = ais_ev.get("immune_response_type", "PRIMARY_RESPONSE")
            if imm_type == "SECONDARY_RESPONSE":
                key_factors.append("Adaptive AIS triggered SECONDARY IMMUNE RESPONSE (matched established memory detectors).")
            else:
                key_factors.append(f"AIS flagged novelty anomaly (score={ais_ev.get('anomaly_score', 0):.2f}).")

        if not key_factors:
            key_factors.append("All ecological indicators within baseline operating limits.")

        summary = f"Threat State: {eco_state} (Risk: {risk_score:.2%}). Dominant modality: {max(modality_attribution, key=modality_attribution.get).replace('_pct', '').upper()}."
        if has_conflict:
            summary += f" Cross-modality conflict active: {conf_type}."

        return ExplanationResult(
            device_id=dev_id,
            timestamp=ts,
            state=eco_state,
            risk_score=risk_score,
            modality_attribution=modality_attribution,
            feature_attribution=feature_attribution,
            key_factors=key_factors,
            recovery_status="STABLE",
            recovery_cycles_confirmed=0,
            recovery_cycles_required=3,
            summary=summary,
            concordance_state=conc_state,
            concordance_score=conc_score,
            conflict_detected=has_conflict,
            conflict_type=conf_type if has_conflict else None,
            prescriptive_action=presc_action if has_conflict else None,
            dominance_prevented=dom_prevented,
            missing_modalities=missing_mods,
            degraded_modalities=degraded_mods,
            multimodal_explanation=state_res.get("explanation", "")
        )


class RecoveryHysteresisManager:
    """
    V5.6 Recovery Hysteresis Manager.
    Prevents alarm fluttering by enforcing that an elevated ecosystem state
    (HIGH_RISK, BLOOM_CONFIRMED, CRITICAL) requires K=3 consecutive verified
    NORMAL observations before clearing to NORMAL.
    """
    def __init__(self, required_normal_cycles: int = 3):
        self.required_normal_cycles = required_normal_cycles
        # Per-device tracking: {device_id: {"in_alarm": bool, "consecutive_normals": int, "highest_alarm": str}}
        self.device_recovery_state: Dict[str, Dict[str, Any]] = {}

    def _get_state(self, device_id: str) -> Dict[str, Any]:
        if device_id not in self.device_recovery_state:
            self.device_recovery_state[device_id] = {
                "in_alarm": False,
                "consecutive_normals": 0,
                "highest_alarm": "NORMAL",
                "active_state": "NORMAL"
            }
        return self.device_recovery_state[device_id]

    def reset_device(self, device_id: str):
        """Resets recovery hysteresis for a device."""
        if device_id in self.device_recovery_state:
            del self.device_recovery_state[device_id]

    def apply_hysteresis(
        self,
        device_id: str,
        observed_state: str,
        observed_risk: float = 0.0
    ) -> Tuple[str, str, int]:
        """
        Applies recovery hysteresis filter.
        Returns: (effective_state, recovery_status, consecutive_normals)
        where recovery_status in ["STABLE", "RECOVERY_HOLD", "RECOVERED"].
        """
        rec = self._get_state(device_id)
        is_threat = observed_state in ["HIGH_RISK", "BLOOM_CONFIRMED", "CRITICAL", "WARNING", "EARLY_WARNING"]

        if is_threat:
            rec["in_alarm"] = True
            rec["consecutive_normals"] = 0
            rec["highest_alarm"] = observed_state
            rec["active_state"] = observed_state
            return observed_state, "STABLE", 0

        # Observed state is NORMAL (or WATCH)
        if not rec["in_alarm"]:
            # Normal baseline, no hysteresis needed
            rec["consecutive_normals"] = 0
            rec["active_state"] = observed_state
            return observed_state, "STABLE", 0

        # Currently in alarm, attempting to recover to NORMAL
        rec["consecutive_normals"] += 1
        cnt = rec["consecutive_normals"]

        if cnt < self.required_normal_cycles:
            # Hold in recovery state (e.g. WATCH or previous warning level)
            hold_state = "WATCH" if rec["highest_alarm"] in ["WARNING", "EARLY_WARNING"] else "EARLY_WARNING"
            rec["active_state"] = hold_state
            return hold_state, "RECOVERY_HOLD", cnt
        else:
            # Recovery confirmed after K consecutive normal observations
            rec["in_alarm"] = False
            rec["consecutive_normals"] = 0
            rec["highest_alarm"] = "NORMAL"
            rec["active_state"] = "NORMAL"
            return "NORMAL", "RECOVERED", cnt
