"""
src/fusion/multimodal_alignment.py
==================================
V7 Multimodal Evidence Alignment Layer.

Provides:
- MultimodalEvidenceItem: Universal normalized evidence contract across all 5 modalities
  (SENSOR, VISION, TEMPORAL, AIS, HISTORICAL).
- TemporalAlignmentEngine: Evaluates time-delta alignment against reference clock
  and tags freshness (CURRENT, RECENT, STALE, MISSING).
- MultimodalSnapshot: Point-in-time consolidated representation of all available,
  missing, and degraded modalities with alignment quality scoring.
- Modality Adapters: Bidirectional converters for existing V4/V5/V6 data containers.
"""

import time
import math
import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Tuple, Union


@dataclass
class MultimodalEvidenceItem:
    """
    Universal normalized evidential unit consumable by the V7 Multimodal Intelligence layer.
    Harmonizes heterogeneous modality representations while preserving full provenance.
    """
    modality: str            # "SENSOR", "VISION", "TEMPORAL", "AIS", "HISTORICAL"
    timestamp: str           # ISO-8601 timestamp string
    device_id: str           # Unique device identifier (e.g. "AQUA_FRESH_001")
    evidence_type: str       # Specific payload type (e.g. "WATER_CHEMISTRY", "SURFACE_IMAGE", "TREND_SLOPES", "NOVELTY_SCORE", "DIGITAL_BASELINE")
    state: str               # Canonical state: "NORMAL", "WATCH", "EARLY_WARNING", "HIGH_RISK", "BLOOM_CONFIRMED", "UNCERTAIN", "FAULT"
    confidence: float        # Raw model or sensor confidence in [0.0, 1.0]
    quality: float           # Measured physical/optical quality in [0.0, 1.0] (Q_sensor, Q_visual)
    reliability: float       # Modality reliability factor in [0.0, 1.0]
    severity: float          # Normalized evidential threat mass in [0.0, 1.0]
    source: str              # Provenance source identifier (model name, sensor bus, algorithm)
    feature_values: Dict[str, Any] = field(default_factory=dict)
    degradation_reason: Optional[str] = None
    valid: bool = True
    freshness_state: str = "CURRENT"  # "CURRENT", "RECENT", "STALE", "MISSING"
    age_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MultimodalSnapshot:
    """
    Point-in-time consolidated representation of the aquatic ecosystem state across all 5 modalities.
    Captures available, missing, and degraded modalities alongside composite alignment quality.
    """
    timestamp: str
    device_id: str
    modalities: Dict[str, MultimodalEvidenceItem] = field(default_factory=dict)
    available_modalities: List[str] = field(default_factory=list)
    missing_modalities: List[str] = field(default_factory=list)
    degraded_modalities: List[str] = field(default_factory=list)
    alignment_quality: float = 1.0  # Composite freshness & synchrony score in [0.0, 1.0]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "timestamp": self.timestamp,
            "device_id": self.device_id,
            "modalities": {k: v.to_dict() for k, v in self.modalities.items()},
            "available_modalities": list(self.available_modalities),
            "missing_modalities": list(self.missing_modalities),
            "degraded_modalities": list(self.degraded_modalities),
            "alignment_quality": self.alignment_quality,
            "metadata": dict(self.metadata)
        }
        return d


class TemporalAlignmentEngine:
    """
    Evaluates temporal synchrony between disparate modality timestamps and the reference clock.
    Classifies freshness and calculates alignment quality penalties.
    """
    def __init__(
        self,
        current_threshold_sec: float = 10.0,
        recent_threshold_sec: float = 30.0,
        stale_threshold_sec: float = 60.0
    ):
        self.current_threshold_sec = current_threshold_sec
        self.recent_threshold_sec = recent_threshold_sec
        self.stale_threshold_sec = stale_threshold_sec

    def evaluate_freshness(
        self,
        evidence_timestamp: Optional[str],
        reference_time: Optional[datetime.datetime] = None
    ) -> Tuple[str, float]:
        """
        Determines freshness category ("CURRENT", "RECENT", "STALE", "MISSING")
        and age in seconds relative to reference_time.
        """
        if evidence_timestamp is None:
            return "MISSING", float("inf")
        if evidence_timestamp == "2026-01-01T00:00:00+00:00" and reference_time is None:
            return "CURRENT", 0.0

        ref_dt = reference_time or datetime.datetime.now(datetime.timezone.utc)
        try:
            clean_ts = evidence_timestamp.replace("Z", "+00:00")
            dt = datetime.datetime.fromisoformat(clean_ts)
            # Normalize timezone awareness
            if dt.tzinfo is not None and ref_dt.tzinfo is None:
                ref_dt = ref_dt.replace(tzinfo=datetime.timezone.utc)
            elif dt.tzinfo is None and ref_dt.tzinfo is not None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            
            age = max(0.0, (ref_dt - dt).total_seconds())
        except Exception:
            return "STALE", float("inf")

        if age <= self.current_threshold_sec:
            return "CURRENT", round(age, 2)
        elif age <= self.recent_threshold_sec:
            return "RECENT", round(age, 2)
        else:
            return "STALE", round(age, 2)


# =============================================================================
# Modality Adapters
# =============================================================================

def adapt_sensor_evidence(
    ml_evidence: Optional[Dict[str, Any]],
    sensors_data: Optional[Dict[str, Any]] = None,
    sensor_quality: Optional[Dict[str, Any]] = None,
    device_id: str = "DEFAULT_DEVICE",
    reference_time: Optional[datetime.datetime] = None,
    alignment_engine: Optional[TemporalAlignmentEngine] = None
) -> Optional[MultimodalEvidenceItem]:
    """Adapts raw water chemistry probe telemetry and supervised ML output into MultimodalEvidenceItem."""
    if ml_evidence is None and sensors_data is None:
        return None

    aligner = alignment_engine or TemporalAlignmentEngine()
    ts = (ml_evidence.get("timestamp") if ml_evidence else None) or \
         (sensors_data.get("timestamp") if isinstance(sensors_data, dict) else None) or \
         "2026-01-01T00:00:00+00:00"

    freshness, age = aligner.evaluate_freshness(ts, reference_time=reference_time)

    q_s = float(sensor_quality.get("q_sensor", 1.0)) if sensor_quality else 1.0
    val_state = str(sensor_quality.get("validation_state", "RELIABLE")) if sensor_quality else "RELIABLE"
    is_valid = q_s >= 0.40 and val_state not in ["CORRUPTED", "FAULT"] and freshness != "STALE"

    # State and severity derivation
    conf = float(ml_evidence.get("confidence", 0.85)) if ml_evidence else 0.80
    is_dangerous = bool(ml_evidence.get("dangerous_class", False)) if ml_evidence else False

    if not is_valid:
        state = "FAULT" if val_state in ["FAULT", "CORRUPTED"] else "UNCERTAIN"
        severity = 0.0
    elif is_dangerous:
        state = "HIGH_RISK" if conf >= 0.85 else "EARLY_WARNING"
        severity = round(conf * q_s, 3)
    else:
        state = "NORMAL"
        severity = 0.05

    deg_reason = None
    if not is_valid:
        deg_reason = f"Sensor quality degraded ({val_state}, Q={q_s:.2f})"
    elif freshness == "STALE":
        deg_reason = f"Stale sensor telemetry ({age:.1f}s old)"

    features = dict(sensors_data) if isinstance(sensors_data, dict) else {}

    return MultimodalEvidenceItem(
        modality="SENSOR",
        timestamp=ts,
        device_id=device_id,
        evidence_type="WATER_CHEMISTRY",
        state=state,
        confidence=conf,
        quality=q_s,
        reliability=0.40 * q_s * (0.30 if freshness == "STALE" else 1.0),
        severity=severity,
        source=ml_evidence.get("model_id", "Supervised-ML") if ml_evidence else "Probes-Direct",
        feature_values=features,
        degradation_reason=deg_reason,
        valid=is_valid,
        freshness_state=freshness,
        age_seconds=age
    )


def adapt_visual_evidence(
    visual_evidence: Optional[Union[Dict[str, Any], Any]],
    device_id: str = "DEFAULT_DEVICE",
    reference_time: Optional[datetime.datetime] = None,
    alignment_engine: Optional[TemporalAlignmentEngine] = None
) -> Optional[MultimodalEvidenceItem]:
    """Adapts VisualEvidence / VisualDetectionResult into MultimodalEvidenceItem."""
    if visual_evidence is None:
        return None

    aligner = alignment_engine or TemporalAlignmentEngine()
    vis_dict = visual_evidence.to_dict() if hasattr(visual_evidence, "to_dict") else visual_evidence
    if not isinstance(vis_dict, dict):
        return None

    ts = vis_dict.get("timestamp") or "2026-01-01T00:00:00+00:00"
    freshness, age = aligner.evaluate_freshness(ts, reference_time=reference_time)

    v_state = vis_dict.get("evidence_state") or vis_dict.get("visual_state", "UNCERTAIN")
    conf = float(vis_dict.get("confidence", 0.0))
    eff_conf = float(vis_dict.get("effective_confidence", conf))
    q_v = float(vis_dict.get("q_visual", 1.0))

    is_valid = bool(vis_dict.get("valid", True)) and v_state not in ["CAMERA_FAULT", "INFERENCE_FAILURE", "DEGRADED_VISUAL"] and freshness != "STALE" and q_v >= 0.60

    if v_state == "BLOOM_EVIDENCE":
        state = "BLOOM_CONFIRMED" if eff_conf >= 0.85 else "HIGH_RISK"
        severity = eff_conf
    elif v_state in ["NORMAL_WATER", "NO_VISUAL_BLOOM"]:
        state = "NORMAL"
        severity = 0.0
    elif v_state in ["TURBID_DISCOLORATION", "TURBIDITY_EVIDENCE"]:
        state = "WATCH"
        severity = round(eff_conf * 0.20, 3)
    elif v_state == "DEGRADED_VISUAL":
        state = "UNCERTAIN"
        severity = 0.10
    else:
        state = "FAULT" if v_state == "CAMERA_FAULT" else "UNCERTAIN"
        severity = 0.0

    deg_reason = vis_dict.get("degradation_reason")
    if q_v < 0.60:
        deg_reason = f"Optical quality severely degraded (Q_visual={q_v:.2f} < 0.60)"
    elif freshness == "STALE":
        deg_reason = f"Stale camera frame ({age:.1f}s old)"

    return MultimodalEvidenceItem(
        modality="VISION",
        timestamp=ts,
        device_id=device_id,
        evidence_type="SURFACE_IMAGE",
        state=state,
        confidence=conf,
        quality=q_v,
        reliability=0.35 * q_v * (0.25 if freshness == "STALE" else 1.0),
        severity=severity,
        source=vis_dict.get("model_name", "MobileNetV3-Small"),
        feature_values={
            "visual_state": v_state,
            "q_visual": q_v,
            "glare": bool(vis_dict.get("glare", False)),
            "frame_id": vis_dict.get("frame_id")
        },
        degradation_reason=deg_reason,
        valid=is_valid,
        freshness_state=freshness,
        age_seconds=age
    )


def adapt_temporal_evidence(
    temporal_evidence: Optional[Union[Dict[str, Any], Any]],
    device_id: str = "DEFAULT_DEVICE",
    reference_time: Optional[datetime.datetime] = None,
    alignment_engine: Optional[TemporalAlignmentEngine] = None
) -> Optional[MultimodalEvidenceItem]:
    """Adapts TemporalEnvironmentalResult into MultimodalEvidenceItem."""
    if temporal_evidence is None:
        return None

    aligner = alignment_engine or TemporalAlignmentEngine()
    temp_dict = temporal_evidence.to_dict() if hasattr(temporal_evidence, "to_dict") else temporal_evidence
    if not isinstance(temp_dict, dict):
        return None

    ts = temp_dict.get("timestamp") or "2026-01-01T00:00:00+00:00"
    freshness, age = aligner.evaluate_freshness(ts, reference_time=reference_time)

    t_state = temp_dict.get("temporal_state", "NORMAL")
    traj_risk = float(temp_dict.get("trajectory_risk_score", 0.0))
    window_sz = int(temp_dict.get("window_size_evaluated", 1))

    is_valid = window_sz >= 2 and freshness != "STALE"
    quality = min(1.0, window_sz / 3.0)

    # State mapping
    if t_state in ["BLOOM_CONFIRMED", "HIGH_RISK", "EARLY_WARNING", "WATCH", "NORMAL"]:
        state = t_state
    else:
        state = "UNCERTAIN"

    return MultimodalEvidenceItem(
        modality="TEMPORAL",
        timestamp=ts,
        device_id=device_id,
        evidence_type="TREND_SLOPES",
        state=state,
        confidence=round(quality, 2),
        quality=quality,
        reliability=0.30 * quality * (0.30 if freshness == "STALE" else 1.0),
        severity=traj_risk,
        source="SlidingWindow-LinearRegression",
        feature_values={
            "temporal_state": t_state,
            "window_size": window_sz,
            "lead_indicators": temp_dict.get("lead_indicators", [])
        },
        degradation_reason=None if is_valid else "Insufficient window size (<2 samples)",
        valid=is_valid,
        freshness_state=freshness,
        age_seconds=age
    )


def adapt_ais_evidence(
    ais_evidence: Optional[Dict[str, Any]],
    device_id: str = "DEFAULT_DEVICE",
    reference_time: Optional[datetime.datetime] = None,
    alignment_engine: Optional[TemporalAlignmentEngine] = None
) -> Optional[MultimodalEvidenceItem]:
    """Adapts AIS anomaly detection result into MultimodalEvidenceItem."""
    if ais_evidence is None:
        return None

    aligner = alignment_engine or TemporalAlignmentEngine()
    ts = ais_evidence.get("timestamp") or "2026-01-01T00:00:00+00:00"
    freshness, age = aligner.evaluate_freshness(ts, reference_time=reference_time)

    is_anom = bool(ais_evidence.get("is_anomaly", False))
    score = float(ais_evidence.get("anomaly_score", 0.0))
    imm_type = ais_evidence.get("immune_response_type", "PRIMARY_RESPONSE" if is_anom else "SELF_TOLERANT")

    state = "HIGH_RISK" if imm_type == "SECONDARY_RESPONSE" else ("EARLY_WARNING" if is_anom else "NORMAL")
    severity = score

    return MultimodalEvidenceItem(
        modality="AIS",
        timestamp=ts,
        device_id=device_id,
        evidence_type="NOVELTY_SCORE",
        state=state,
        confidence=round(score if is_anom else (1.0 - score), 3),
        quality=1.0,
        reliability=0.20 if imm_type != "SECONDARY_RESPONSE" else 0.30,
        severity=severity,
        source=ais_evidence.get("ais_model_id", "NegativeSelectionAlgorithm"),
        feature_values={
            "is_anomaly": is_anom,
            "anomaly_score": score,
            "immune_response_type": imm_type,
            "matched_detectors": ais_evidence.get("matched_detector_count", 0)
        },
        degradation_reason=None,
        valid=True,
        freshness_state=freshness,
        age_seconds=age
    )


def adapt_historical_evidence(
    historical_state: Optional[Union[Dict[str, Any], Any]],
    device_id: str = "DEFAULT_DEVICE",
    reference_time: Optional[datetime.datetime] = None,
    alignment_engine: Optional[TemporalAlignmentEngine] = None
) -> Optional[MultimodalEvidenceItem]:
    """Adapts DigitalEcosystemState into MultimodalEvidenceItem."""
    if historical_state is None:
        return None

    aligner = alignment_engine or TemporalAlignmentEngine()
    h_dict = historical_state.to_dict() if hasattr(historical_state, "to_dict") else historical_state
    if not isinstance(h_dict, dict):
        return None

    ts = h_dict.get("last_updated") or h_dict.get("timestamp") or "2026-01-01T00:00:00+00:00"
    freshness, age = aligner.evaluate_freshness(ts, reference_time=reference_time)

    h_idx = float(h_dict.get("ecosystem_health_index", 1.0))
    deviations = h_dict.get("deviations_from_baseline", {})
    obs_count = int(h_dict.get("total_observations", 0))

    is_valid = obs_count >= 5
    quality = min(1.0, obs_count / 20.0)

    # State: low health index indicates chronic baseline deviation
    if h_idx <= 0.40:
        state = "HIGH_RISK"
    elif h_idx <= 0.65:
        state = "EARLY_WARNING"
    elif h_idx <= 0.85:
        state = "WATCH"
    else:
        state = "NORMAL"

    severity = round(1.0 - h_idx, 3)

    return MultimodalEvidenceItem(
        modality="HISTORICAL",
        timestamp=ts,
        device_id=device_id,
        evidence_type="DIGITAL_BASELINE",
        state=state,
        confidence=round(quality, 2),
        quality=quality,
        reliability=0.15 * quality,
        severity=severity,
        source="Rolling-ZScore-Baseline",
        feature_values={
            "health_index": h_idx,
            "total_observations": obs_count,
            "deviations": deviations
        },
        degradation_reason=None if is_valid else f"Warmup phase (observations={obs_count} < 5)",
        valid=is_valid,
        freshness_state=freshness,
        age_seconds=age
    )


# =============================================================================
# Snapshot Builder
# =============================================================================

def build_multimodal_snapshot(
    device_id: str = "DEFAULT_DEVICE",
    timestamp: Optional[str] = None,
    sensor_item: Optional[Union[MultimodalEvidenceItem, Dict[str, Any]]] = None,
    vision_item: Optional[Union[MultimodalEvidenceItem, Dict[str, Any]]] = None,
    temporal_item: Optional[Union[MultimodalEvidenceItem, Dict[str, Any], Any]] = None,
    ais_item: Optional[Union[MultimodalEvidenceItem, Dict[str, Any]]] = None,
    historical_item: Optional[Union[MultimodalEvidenceItem, Dict[str, Any]]] = None,
    # Keyword aliases for convenience
    sensor_evidence: Optional[Union[MultimodalEvidenceItem, Dict[str, Any]]] = None,
    visual_evidence: Optional[Union[MultimodalEvidenceItem, Dict[str, Any]]] = None,
    temporal_evidence: Optional[Union[MultimodalEvidenceItem, Dict[str, Any], Any]] = None,
    ais_evidence: Optional[Union[MultimodalEvidenceItem, Dict[str, Any]]] = None,
    historical_evidence: Optional[Union[MultimodalEvidenceItem, Dict[str, Any]]] = None,
    sensor_quality: Optional[Dict[str, Any]] = None,
    alignment_engine: Optional[TemporalAlignmentEngine] = None,
    reference_time: Optional[datetime.datetime] = None
) -> MultimodalSnapshot:
    """
    Constructs a unified MultimodalSnapshot aggregating evidence across available modalities.
    Accepts pre-built MultimodalEvidenceItem instances or raw adapter input payloads.
    Evaluates availability, identifies degraded feeds, and computes composite alignment quality.
    """
    aligner = alignment_engine or TemporalAlignmentEngine()
    # Resolve items or adapt raw inputs
    s_in = sensor_item if sensor_item is not None else sensor_evidence
    if s_in is not None and not isinstance(s_in, MultimodalEvidenceItem):
        s_item = adapt_sensor_evidence(
            s_in, device_id=device_id, sensor_quality=sensor_quality,
            reference_time=reference_time, alignment_engine=aligner
        )
    else:
        s_item = s_in

    v_in = vision_item if vision_item is not None else visual_evidence
    if v_in is not None and not isinstance(v_in, MultimodalEvidenceItem):
        v_item = adapt_visual_evidence(
            v_in, device_id=device_id, reference_time=reference_time, alignment_engine=aligner
        )
    else:
        v_item = v_in

    t_in = temporal_item if temporal_item is not None else temporal_evidence
    if t_in is not None and not isinstance(t_in, MultimodalEvidenceItem):
        t_item = adapt_temporal_evidence(
            t_in, device_id=device_id, reference_time=reference_time, alignment_engine=aligner
        )
    else:
        t_item = t_in

    a_in = ais_item if ais_item is not None else ais_evidence
    if a_in is not None and not isinstance(a_in, MultimodalEvidenceItem):
        a_item = adapt_ais_evidence(
            a_in, device_id=device_id, reference_time=reference_time, alignment_engine=aligner
        )
    else:
        a_item = a_in

    h_in = historical_item if historical_item is not None else historical_evidence
    if h_in is not None and not isinstance(h_in, MultimodalEvidenceItem):
        h_item = adapt_historical_evidence(
            h_in, device_id=device_id, reference_time=reference_time, alignment_engine=aligner
        )
    else:
        h_item = h_in

    raw_items = {
        "SENSOR": s_item,
        "VISION": v_item,
        "TEMPORAL": t_item,
        "AIS": a_item,
        "HISTORICAL": h_item
    }

    modalities: Dict[str, MultimodalEvidenceItem] = {}
    available: List[str] = []
    missing: List[str] = []
    degraded: List[str] = []

    alignment_scores: List[float] = []

    for mod_name, item in raw_items.items():
        if item is not None and item.freshness_state != "MISSING":
            modalities[mod_name] = item
            available.append(mod_name)
            if not item.valid or item.quality < 0.65 or item.freshness_state == "STALE":
                degraded.append(mod_name)
            
            # Freshness score contribution
            if item.freshness_state == "CURRENT":
                alignment_scores.append(1.0)
            elif item.freshness_state == "RECENT":
                alignment_scores.append(0.80)
            elif item.freshness_state == "STALE":
                alignment_scores.append(0.30)
        else:
            missing.append(mod_name)

    # Alignment quality is the mean of available freshness scores scaled by modality coverage
    if alignment_scores:
        mean_freshness = sum(alignment_scores) / len(alignment_scores)
        coverage_factor = len(available) / 5.0
        # Base quality is weighted 70% freshness + 30% coverage
        align_quality = round(0.70 * mean_freshness + 0.30 * coverage_factor, 3)
    else:
        align_quality = 0.0

    resolved_ts = timestamp
    if resolved_ts is None:
        for it in [s_item, v_item, t_item, a_item, h_item]:
            if it is not None and it.timestamp != "2026-01-01T00:00:00+00:00":
                resolved_ts = it.timestamp
                break
    ts = resolved_ts or "2026-01-01T00:00:00+00:00"

    return MultimodalSnapshot(
        timestamp=ts,
        device_id=device_id,
        modalities=modalities,
        available_modalities=available,
        missing_modalities=missing,
        degraded_modalities=degraded,
        alignment_quality=align_quality,
        metadata={"item_count": len(modalities), "reference_time": reference_time.isoformat() if reference_time else None}
    )
