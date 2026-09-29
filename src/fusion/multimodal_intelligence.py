"""
src/fusion/multimodal_intelligence.py
=====================================
V7 Multimodal Intelligence, Concordance, Conflict & Ecological Reasoning Layer.

Provides:
- ConcordanceEngine & ConcordanceResult: Evaluates multi-modality agreement across available streams.
- ConflictDetector & ConflictResult: Detects disagreements between modalities and prescribes safe handling.
- MultimodalStateEstimator & MultimodalStateResult: Synthesizes final ecological state with strict
  single-modality dominance prevention.
"""

import math
import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Tuple

from src.fusion.multimodal_alignment import MultimodalEvidenceItem, MultimodalSnapshot


@dataclass
class ConcordanceResult:
    """
    Evaluation of evidential agreement across all available modalities.
    """
    concordance_state: str       # "CONCORDANT", "PARTIALLY_CONCORDANT", "INCONCLUSIVE"
    agreement_score: float       # Degree of alignment in [0.0, 1.0]
    dominant_state: str          # The state supported by majority evidential mass
    supporting_modalities: List[str] = field(default_factory=list)
    dissenting_modalities: List[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConflictResult:
    """
    Diagnostic identification and prescribed resolution for inter-modality disagreements.
    """
    conflict_detected: bool
    modalities_in_conflict: List[str] = field(default_factory=list)
    conflict_type: str = "NONE"  # "NONE", "SENSOR_VS_VISION", "TURBIDITY_VS_SEDIMENT", "AIS_NOVELTY_VS_SENSORS", "TEMPORAL_DIVERGENCE", "MULTIPLE_CONFLICTS"
    severity: str = "NONE"       # "NONE", "LOW", "MEDIUM", "HIGH"
    explanation: str = "No conflicts detected across active modalities."
    recommended_handling: str = "STANDARD_FUSION"  # "STANDARD_FUSION", "CONSERVATIVE_HOLD", "SUPPRESS_EMERGENCY", "DEWEIGHT_DEGRADED"

    @property
    def has_conflict(self) -> bool:
        return self.conflict_detected

    @property
    def prescriptive_action(self) -> str:
        return self.recommended_handling

    @property
    def details(self) -> str:
        return self.explanation

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["has_conflict"] = self.has_conflict
        d["prescriptive_action"] = self.prescriptive_action
        return d


@dataclass
class MultimodalStateResult:
    """
    Consolidated V7 multimodal ecological state estimation output.
    """
    ecological_state: str        # "NORMAL", "WATCH", "EARLY_WARNING", "HIGH_RISK", "BLOOM_CONFIRMED", "UNCERTAIN"
    composite_confidence: float  # [0.0, 1.0]
    evidence_strength: float     # Combined evidential mass
    supporting_modalities: List[str] = field(default_factory=list)
    conflicting_modalities: List[str] = field(default_factory=list)
    missing_modalities: List[str] = field(default_factory=list)
    degraded_modalities: List[str] = field(default_factory=list)
    uncertainty: float = 0.0     # Metric in [0.0, 1.0] capturing incomplete or conflicting data
    dominance_prevented: bool = False  # True if single uncorroborated noisy modality was blocked from escalating
    reason_codes: List[str] = field(default_factory=list)
    explanation: str = ""
    timestamp: str = ""

    @property
    def effective_risk_score(self) -> float:
        return self.evidence_strength

    @property
    def confidence_score(self) -> float:
        return self.composite_confidence

    @property
    def diagnostic_rationale(self) -> str:
        return self.explanation

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["effective_risk_score"] = self.effective_risk_score
        d["confidence_score"] = self.confidence_score
        d["diagnostic_rationale"] = self.diagnostic_rationale
        return d


# =============================================================================
# Concordance Engine
# =============================================================================

class ConcordanceEngine:
    """
    Analyzes inter-modality concordance to determine whether independent sensory streams
    mutually reinforce an ecological diagnosis.
    """
    def __init__(self):
        self.threat_states = {"EARLY_WARNING", "HIGH_RISK", "BLOOM_CONFIRMED"}
        self.benign_states = {"NORMAL", "WATCH"}

    def evaluate_concordance(self, snapshot: MultimodalSnapshot) -> ConcordanceResult:
        """
        Evaluates agreement across valid available modalities in snapshot.
        """
        valid_items = {
            m: item for m, item in snapshot.modalities.items()
            if item.valid and item.freshness_state != "STALE"
        }

        if len(valid_items) < 2:
            single_mod = list(valid_items.keys())
            state = valid_items[single_mod[0]].state if single_mod else "UNCERTAIN"
            return ConcordanceResult(
                concordance_state="INCONCLUSIVE",
                agreement_score=0.50 if single_mod else 0.0,
                dominant_state=state,
                supporting_modalities=single_mod,
                dissenting_modalities=[],
                explanation=f"Insufficient active modalities ({len(valid_items)} < 2) to establish concordance."
            )

        # Categorize votes: Threat vs Benign vs Uncertain
        threat_mods = []
        benign_mods = []
        uncertain_mods = []

        total_rel = 0.0
        threat_mass = 0.0
        benign_mass = 0.0

        for m, item in valid_items.items():
            r = item.reliability
            total_rel += r
            if item.state in self.threat_states:
                threat_mods.append(m)
                threat_mass += r * item.severity
            elif item.state in self.benign_states:
                benign_mods.append(m)
                benign_mass += r * (1.0 - item.severity)
            else:
                uncertain_mods.append(m)

        n_valid = len(valid_items)
        if len(threat_mods) == n_valid:
            # 100% concordance on threat
            return ConcordanceResult(
                concordance_state="CONCORDANT",
                agreement_score=1.0,
                dominant_state="BLOOM_CONFIRMED" if len(threat_mods) >= 3 else "HIGH_RISK",
                supporting_modalities=threat_mods,
                dissenting_modalities=[],
                explanation=f"All {n_valid} active modalities concordantly indicate elevated ecosystem threat."
            )
        elif len(benign_mods) == n_valid:
            # 100% concordance on normal/benign
            return ConcordanceResult(
                concordance_state="CONCORDANT",
                agreement_score=1.0,
                dominant_state="NORMAL",
                supporting_modalities=benign_mods,
                dissenting_modalities=[],
                explanation=f"All {n_valid} active modalities concordantly confirm normal ecosystem baseline."
            )
        else:
            # Divided evidence
            maj_is_threat = threat_mass >= benign_mass
            dom_state = "HIGH_RISK" if maj_is_threat else "NORMAL"
            supp = threat_mods if maj_is_threat else benign_mods
            diss = benign_mods if maj_is_threat else threat_mods

            supp_rel = sum(valid_items[m].reliability for m in supp)
            score = supp_rel / max(0.001, total_rel)
            score = round(min(1.0, score), 3)

            if len(supp) >= 3 and len(diss) <= 1:
                state_cat = "CONCORDANT"
            elif (len(supp) >= 2 and len(diss) <= 1) or score >= 0.60:
                state_cat = "PARTIALLY_CONCORDANT"
            else:
                state_cat = "INCONCLUSIVE"
            expl = f"{state_cat} (agreement={score:.1%}): {len(supp)} supporting vs {len(diss)} dissenting modalities."

            return ConcordanceResult(
                concordance_state=state_cat,
                agreement_score=score,
                dominant_state=dom_state,
                supporting_modalities=supp,
                dissenting_modalities=diss,
                explanation=expl
            )

    evaluate = evaluate_concordance


# =============================================================================
# Conflict Detector
# =============================================================================

class ConflictDetector:
    """
    Identifies evidential disagreements between modalities and prescribes safe conservative handling.
    """
    def __init__(self):
        pass

    def detect_conflicts(self, snapshot: MultimodalSnapshot) -> ConflictResult:
        """
        Scans modalities for contradictory ecological signals.
        """
        mods = snapshot.modalities
        s_item = mods.get("SENSOR")
        v_item = mods.get("VISION")
        t_item = mods.get("TEMPORAL")
        a_item = mods.get("AIS")
        h_item = mods.get("HISTORICAL")

        conflicts = []
        c_types = []
        severity = "NONE"
        rec_handling = "STANDARD_FUSION"

        # Check 1: SENSOR vs VISION Conflict
        if s_item and v_item and s_item.valid and v_item.valid:
            s_threat = s_item.state in ["EARLY_WARNING", "HIGH_RISK", "BLOOM_CONFIRMED"]
            v_threat = v_item.state in ["EARLY_WARNING", "HIGH_RISK", "BLOOM_CONFIRMED"]
            s_clear = s_item.state in ["NORMAL", "WATCH"]
            v_clear = v_item.state in ["NORMAL", "WATCH"]

            # Case 1A: Sensor flags bloom risk while camera observes clear water
            if s_threat and v_clear:
                conflicts.append("SENSOR_VS_VISION")
                c_types.append("SENSOR_VS_VISION")
                severity = "MEDIUM" if v_item.quality >= 0.75 else "LOW"
                rec_handling = "SUPPRESS_EMERGENCY"

            # Case 1B: Camera flags bloom scum while chemistry sensors are normal
            elif v_threat and s_clear:
                conflicts.append("SENSOR_VS_VISION")
                c_types.append("SENSOR_VS_VISION")
                severity = "MEDIUM"
                rec_handling = "CONSERVATIVE_HOLD"

            # Case 1C: Turbidity Sensor spike vs Visual Sediment Turbidity (No scum)
            turb_val = float(s_item.feature_values.get("turbidity_ntu", 0.0))
            vis_state = str(v_item.feature_values.get("visual_state", ""))
            if turb_val > 30.0 and vis_state in ["TURBID_DISCOLORATION", "TURBIDITY_EVIDENCE"]:
                conflicts.append("TURBIDITY_VS_SEDIMENT")
                c_types.append("TURBIDITY_VS_SEDIMENT")
                rec_handling = "STANDARD_FUSION"
                severity = "LOW"

        # Check 2: AIS Novelty vs Supervised Sensors & Vision
        if a_item and a_item.valid and a_item.state in ["HIGH_RISK", "BLOOM_CONFIRMED"]:
            is_s_normal = s_item and s_item.valid and s_item.state == "NORMAL"
            is_v_normal = v_item and v_item.valid and v_item.state == "NORMAL"
            if is_s_normal and is_v_normal:
                conflicts.append("AIS_NOVELTY_VS_SENSORS")
                c_types.append("AIS_NOVELTY_VS_SENSORS")
                severity = "LOW"
                if rec_handling == "STANDARD_FUSION":
                    rec_handling = "CONSERVATIVE_HOLD"

        # Check 3: Temporal Trajectory Divergence
        if t_item and t_item.valid:
            if t_item.state in ["HIGH_RISK", "BLOOM_CONFIRMED"] and s_item and s_item.valid and s_item.state == "NORMAL":
                conflicts.append("TEMPORAL_DIVERGENCE")
                c_types.append("TEMPORAL_DIVERGENCE")
                severity = "MEDIUM"
                if rec_handling == "STANDARD_FUSION":
                    rec_handling = "CONSERVATIVE_HOLD"

        # Resolve primary conflict classification
        if len(c_types) > 1:
            primary_type = "MULTIPLE_CONFLICTS"
            severity = "HIGH"
            rec_handling = "CONSERVATIVE_HOLD"
        elif len(c_types) == 1:
            primary_type = c_types[0]
        else:
            primary_type = "NONE"

        mods_in_conflict = set()
        if "SENSOR_VS_VISION" in c_types:
            mods_in_conflict.update(["SENSOR", "VISION"])
        if "TURBIDITY_VS_SEDIMENT" in c_types:
            mods_in_conflict.update(["SENSOR", "VISION"])
        if "AIS_NOVELTY_VS_SENSORS" in c_types:
            mods_in_conflict.update(["AIS", "SENSOR", "VISION"])
        if "TEMPORAL_DIVERGENCE" in c_types:
            mods_in_conflict.update(["TEMPORAL", "SENSOR"])

        if conflicts:
            expl = f"Conflict detected ({primary_type}, severity={severity}): Disagreement between {', '.join(sorted(list(mods_in_conflict)))}. Recommended handling: {rec_handling}."
        else:
            expl = "No evidential conflicts detected across active modalities."

        return ConflictResult(
            conflict_detected=len(conflicts) > 0,
            modalities_in_conflict=sorted(list(mods_in_conflict)),
            conflict_type=primary_type,
            severity=severity,
            explanation=expl,
            recommended_handling=rec_handling
        )

    detect = detect_conflicts


# =============================================================================
# Ecological State Estimator with Dominance Prevention
# =============================================================================

class MultimodalStateEstimator:
    """
    Synthesizes normalized evidence, concordance analysis, and conflict diagnostics
    into a final robust ecological state.
    Enforces strict Single-Modality Dominance Prevention.
    """
    def __init__(self):
        self.state_ranks = {
            "NORMAL": 0,
            "WATCH": 1,
            "EARLY_WARNING": 2,
            "HIGH_RISK": 3,
            "BLOOM_CONFIRMED": 4
        }
        self.rank_to_state = {v: k for k, v in self.state_ranks.items()}

    def estimate_state(
        self,
        snapshot: MultimodalSnapshot,
        concordance: ConcordanceResult,
        conflict: ConflictResult
    ) -> MultimodalStateResult:
        """
        Computes final MultimodalStateResult.
        """
        valid_mods = {
            m: item for m, item in snapshot.modalities.items()
            if item.valid and item.freshness_state != "STALE"
        }

        # Calculate weighted threat mass
        total_rel = sum(item.reliability for item in valid_mods.values())
        if total_rel > 0:
            composite_threat = sum(item.reliability * item.severity for item in valid_mods.values()) / total_rel
        else:
            composite_threat = 0.0

        composite_threat = round(float(composite_threat), 4)

        # Baseline provisional state from composite threat
        if composite_threat >= 0.72:
            prov_state = "BLOOM_CONFIRMED"
        elif composite_threat >= 0.50:
            prov_state = "HIGH_RISK"
        elif composite_threat >= 0.30:
            prov_state = "EARLY_WARNING"
        elif composite_threat >= 0.15:
            prov_state = "WATCH"
        else:
            prov_state = "NORMAL"

        dominance_prevented = False
        reasons = []

        # ---------------------------------------------------------------------
        # DOMINANCE PREVENTION RULE:
        # A single modality cannot unilaterally force HIGH_RISK or BLOOM_CONFIRMED
        # without corroboration from at least one other independent valid modality.
        # ---------------------------------------------------------------------
        threat_mods_list = [
            m for m, item in valid_mods.items()
            if item.state in ["EARLY_WARNING", "HIGH_RISK", "BLOOM_CONFIRMED"]
        ]

        if len(threat_mods_list) == 1:
            lone_mod = threat_mods_list[0]
            lone_item = valid_mods[lone_mod]

            # Check if lone modality is low-quality or in conflict with others
            if lone_item.quality < 0.70 or conflict.conflict_detected or len(valid_mods) == 1:
                if prov_state in ["HIGH_RISK", "BLOOM_CONFIRMED"]:
                    prov_state = "EARLY_WARNING"
                dominance_prevented = True
                reasons.append(f"Dominance Prevention: Single uncorroborated modality ({lone_mod}) prevented from elevating system state.")

        # ---------------------------------------------------------------------
        # Conflict Resolutions
        # ---------------------------------------------------------------------
        if conflict.conflict_detected:
            reasons.append(conflict.explanation)
            if conflict.recommended_handling == "SUPPRESS_EMERGENCY":
                # Camera confirms clear water or sediment turbidity -> suppress critical lockout
                if prov_state in ["HIGH_RISK", "BLOOM_CONFIRMED"]:
                    prov_state = "WATCH" if "TURBIDITY" in conflict.conflict_type else "EARLY_WARNING"
                    reasons.append("Emergency alarm suppressed due to visual disconfirmation.")
            elif conflict.recommended_handling == "CONSERVATIVE_HOLD":
                if prov_state == "BLOOM_CONFIRMED":
                    prov_state = "HIGH_RISK"
                elif prov_state == "HIGH_RISK":
                    prov_state = "EARLY_WARNING"
                reasons.append("State dampened conservatively due to active inter-modality conflict.")

        # ---------------------------------------------------------------------
        # Concordance Reinforcement
        # ---------------------------------------------------------------------
        if concordance.concordance_state == "CONCORDANT":
            if concordance.dominant_state in ["HIGH_RISK", "BLOOM_CONFIRMED"] and len(concordance.supporting_modalities) >= 2:
                prov_state = "BLOOM_CONFIRMED"
                reasons.append("Multi-modality concordance elevated decision to BLOOM_CONFIRMED.")
            elif concordance.dominant_state == "NORMAL":
                prov_state = "NORMAL"
                reasons.append("Full multi-modality concordance confirms NORMAL state.")

        # ---------------------------------------------------------------------
        # Uncertainty Calculation
        # Incomplete modalities or stale feeds elevate uncertainty
        # ---------------------------------------------------------------------
        missing_count = len(snapshot.missing_modalities)
        degraded_count = len(snapshot.degraded_modalities)
        conflict_penalty = 0.25 if conflict.conflict_detected else 0.0

        uncertainty = (missing_count * 0.15) + (degraded_count * 0.10) + conflict_penalty
        uncertainty = round(float(max(0.0, min(1.0, uncertainty))), 3)

        confidence = round(float(max(0.10, min(1.0, (1.0 - uncertainty) * max(0.40, snapshot.alignment_quality)))), 3)

        supporting = [m for m, item in valid_mods.items() if item.state == prov_state or (prov_state in ["HIGH_RISK", "BLOOM_CONFIRMED"] and item.severity >= 0.50)]
        conflicting = list(conflict.modalities_in_conflict)

        expl = f"Ecological State: {prov_state} (Confidence: {confidence:.1%}, Threat: {composite_threat:.2f}). {'; '.join(reasons) if reasons else 'Nominal evidential synthesis.'}"

        return MultimodalStateResult(
            ecological_state=prov_state,
            composite_confidence=confidence,
            evidence_strength=composite_threat,
            supporting_modalities=supporting,
            conflicting_modalities=conflicting,
            missing_modalities=list(snapshot.missing_modalities),
            degraded_modalities=list(snapshot.degraded_modalities),
            uncertainty=uncertainty,
            dominance_prevented=dominance_prevented,
            reason_codes=reasons or ["MULTIMODAL_EVALUATED_OK"],
            explanation=expl,
            timestamp=snapshot.timestamp
        )

    estimate = estimate_state
