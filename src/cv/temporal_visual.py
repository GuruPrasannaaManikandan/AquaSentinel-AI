import os
import json
import logging
import datetime
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Tuple
from collections import deque


@dataclass
class FrameInferenceRecord:
    """Historical record of an individual camera frame's inference and optical quality."""
    frame_id: str
    timestamp: str
    predicted_class: str
    raw_confidence: float
    q_visual: float
    effective_confidence: float
    quality_state: str


@dataclass
class TemporalVisualConsistencyResult:
    """
    Outcome of evaluating temporal visual consistency across the multi-frame buffer (K=3).
    Determines whether visual evidence is consistent, transient, or ambiguous.
    """
    temporal_consistency: float  # in [0.0, 1.0]
    consistency_state: str        # "CONSISTENT_BLOOM", "CONSISTENT_NORMAL", "CONSISTENT_TURBID", "TRANSIENT_BLOOM", "AMBIGUOUS", "SINGLE_FRAME", "DEGRADED"
    frames_evaluated: int
    consensus_class: str
    mean_q_visual: float
    mean_raw_confidence: float
    effective_confidence: float
    is_consistent: bool
    is_transient: bool
    reasons: List[str] = field(default_factory=list)
    consecutive_count: int = 1
    persistence_score: float = 0.5
    fault_recovered: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TemporalVisualBuffer:
    """
    Lightweight sliding-window temporal consistency engine for visual evidence.
    Buffers the last K=3 consecutive inference records to verify temporal persistence,
    preventing single transient frames or corrupted glitches from causing false bloom alarms.
    """
    def __init__(
        self,
        window_size_k: int = 3,
        max_frame_age_seconds: float = 30.0,
        transient_evidence_discount: float = 0.35
    ):
        self.window_size_k = window_size_k
        self.max_frame_age_seconds = max_frame_age_seconds
        self.transient_evidence_discount = transient_evidence_discount
        self.buffer: deque[FrameInferenceRecord] = deque(maxlen=window_size_k)
        self.consecutive_count: int = 0
        self.last_seen_class: Optional[str] = None
        self.was_in_fault: bool = False
        self.latest_fault_recovered: bool = False

    def clear(self) -> None:
        """Resets the historical frame buffer."""
        self.buffer.clear()
        self.consecutive_count = 0
        self.last_seen_class = None
        self.was_in_fault = False
        self.latest_fault_recovered = False

    def record_fault(self, fault_type_or_frame_id: str = "CAMERA_FAULT", fault_type: Optional[str] = None) -> None:
        """Flags that camera experienced hardware or temporal fault."""
        self.was_in_fault = True
        self.consecutive_count = 0

    def get_persistence_boost(self, consistency_state: str) -> float:
        """Calculates evidential persistence boost or discount."""
        if consistency_state == "CONSISTENT_BLOOM":
            return 1.20
        elif consistency_state == "TRANSIENT_BLOOM":
            return self.transient_evidence_discount
        elif consistency_state == "CONSISTENT_NORMAL":
            return 1.0
        return 0.85

    def add_frame(
        self,
        frame_id: str,
        timestamp: str,
        predicted_class: str,
        raw_confidence: float,
        q_visual: float,
        quality_state: str = "RELIABLE"
    ) -> TemporalVisualConsistencyResult:
        """
        Adds a new frame inference record to the temporal buffer and evaluates multi-frame consistency.
        """
        effective_conf = round(float(raw_confidence * q_visual), 4)
        rec = FrameInferenceRecord(
            frame_id=frame_id,
            timestamp=timestamp,
            predicted_class=predicted_class,
            raw_confidence=raw_confidence,
            q_visual=q_visual,
            effective_confidence=effective_conf,
            quality_state=quality_state
        )
        self.buffer.append(rec)

        # Fault recovery detection
        self.latest_fault_recovered = self.was_in_fault
        self.was_in_fault = False

        # Consecutive agreement
        if self.last_seen_class == predicted_class:
            self.consecutive_count += 1
        else:
            self.consecutive_count = 1
        self.last_seen_class = predicted_class

        return self.evaluate_consistency()

    def evaluate_consistency(self) -> TemporalVisualConsistencyResult:
        """
        Evaluates temporal consistency across currently buffered frames.
        """
        if len(self.buffer) == 0:
            return TemporalVisualConsistencyResult(
                temporal_consistency=0.0,
                consistency_state="EMPTY_BUFFER",
                frames_evaluated=0,
                consensus_class="UNCERTAIN",
                mean_q_visual=0.0,
                mean_raw_confidence=0.0,
                effective_confidence=0.0,
                is_consistent=False,
                is_transient=False,
                reasons=["No frames in temporal buffer"]
            )

        # Single frame behavior
        c_count = max(1, self.consecutive_count)
        p_score = min(1.0, round(c_count / 3.0, 3))
        f_recovered = self.latest_fault_recovered

        if len(self.buffer) == 1:
            f = self.buffer[0]
            is_bloom = f.predicted_class in ["ALGAL_BLOOM", "ALGAL_BLOOM_RISK"]
            p_score = round(f.q_visual, 3) if is_bloom else 0.0
            # Single bloom frame cannot claim multi-frame confirmation yet
            init_state = "SINGLE_FRAME"
            reasons = ["Single frame observation; awaiting multi-frame confirmation"]
            return TemporalVisualConsistencyResult(
                temporal_consistency=round(f.q_visual, 4),
                consistency_state=init_state,
                frames_evaluated=1,
                consensus_class=f.predicted_class,
                mean_q_visual=f.q_visual,
                mean_raw_confidence=f.raw_confidence,
                effective_confidence=f.effective_confidence,
                is_consistent=False,
                is_transient=is_bloom,
                reasons=reasons,
                consecutive_count=c_count,
                persistence_score=p_score,
                fault_recovered=f_recovered
            )

        # Multi-frame evaluation (2 or 3 frames)
        records = list(self.buffer)
        n = len(records)
        classes = [r.predicted_class for r in records]
        q_vals = [r.q_visual for r in records]
        raw_confs = [r.raw_confidence for r in records]
        eff_confs = [r.effective_confidence for r in records]

        # Quality-weighted bloom persistence score P_bloom
        bloom_aliases = {"ALGAL_BLOOM", "ALGAL_BLOOM_RISK"}
        bloom_weights = [r.q_visual for r in records if r.predicted_class in bloom_aliases]
        p_score = round(float(sum(bloom_weights) / max(1, n)), 3)

        mean_q = float(np.mean(q_vals)) if hasattr(np, 'mean') else sum(q_vals) / n
        mean_raw = sum(raw_confs) / n
        mean_eff = sum(eff_confs) / n

        # Check temporal spacing / age delta
        age_exceeded = False
        try:
            t_first = datetime.datetime.fromisoformat(records[0].timestamp)
            t_last = datetime.datetime.fromisoformat(records[-1].timestamp)
            delta_sec = abs((t_last - t_first).total_seconds())
            if delta_sec > self.max_frame_age_seconds:
                age_exceeded = True
        except Exception:
            pass

        reasons = []
        if age_exceeded:
            reasons.append(f"Buffered frames span {delta_sec:.1f}s (> {self.max_frame_age_seconds:.1f}s max age)")

        # Normalization of bloom classes
        bloom_aliases = {"ALGAL_BLOOM", "ALGAL_BLOOM_RISK"}
        normal_aliases = {"NORMAL_WATER", "NO_BLOOM"}
        turbid_aliases = {"TURBID_DISCOLORATION"}

        def map_category(c: str) -> str:
            if c in bloom_aliases:
                return "BLOOM"
            elif c in normal_aliases:
                return "NORMAL"
            elif c in turbid_aliases:
                return "TURBID"
            return "OTHER"

        categories = [map_category(c) for c in classes]
        unique_cats = set(categories)

        # Case 1: Perfect Agreement across all buffered frames
        if len(unique_cats) == 1:
            cat = categories[-1]
            if cat == "BLOOM":
                if mean_q >= 0.65:
                    consistency_state = "CONSISTENT_BLOOM"
                    temp_consistency = 1.0
                    is_consistent = True
                    is_transient = False
                    reasons.append(f"Confirmed persistent bloom detection across {n} consecutive frames")
                else:
                    consistency_state = "DEGRADED"
                    temp_consistency = 0.50
                    is_consistent = False
                    is_transient = False
                    reasons.append(f"Bloom detected across {n} frames, but optical quality is degraded (mean Q_visual={mean_q:.2f})")
            elif cat == "NORMAL":
                consistency_state = "CONSISTENT_NORMAL"
                temp_consistency = 1.0
                is_consistent = True
                is_transient = False
                reasons.append(f"Consistent clear water confirmed across {n} frames")
            elif cat == "TURBID":
                consistency_state = "CONSISTENT_TURBID"
                temp_consistency = 1.0
                is_consistent = True
                is_transient = False
                reasons.append(f"Consistent turbidity discoloration confirmed across {n} frames")
            else:
                consistency_state = "CONSISTENT_OTHER"
                temp_consistency = 0.80
                is_consistent = True
                is_transient = False

            eff_conf = records[-1].effective_confidence * temp_consistency
            if age_exceeded:
                temp_consistency *= 0.80

            return TemporalVisualConsistencyResult(
                temporal_consistency=round(temp_consistency, 4),
                consistency_state=consistency_state,
                frames_evaluated=n,
                consensus_class=records[-1].predicted_class,
                mean_q_visual=round(mean_q, 4),
                mean_raw_confidence=round(mean_raw, 4),
                effective_confidence=round(eff_conf, 4),
                is_consistent=is_consistent,
                is_transient=is_transient,
                reasons=reasons,
                consecutive_count=c_count,
                persistence_score=p_score,
                fault_recovered=f_recovered
            )

        # Case 2: Transient Bloom (e.g. [NORMAL, BLOOM, NORMAL] or [NORMAL, BLOOM])
        bloom_count = categories.count("BLOOM")
        if bloom_count == 1 and ("NORMAL" in categories or "TURBID" in categories):
            consistency_state = "TRANSIENT_BLOOM"
            temp_consistency = self.transient_evidence_discount
            reasons.append("Single isolated bloom frame observed within normal sequence (transient artifact discounted)")
            # Consensus falls back to majority or previous stable state
            majority_class = "NORMAL_WATER" if categories.count("NORMAL") >= categories.count("TURBID") else "TURBID_DISCOLORATION"
            eff_conf = records[-1].effective_confidence * temp_consistency
            return TemporalVisualConsistencyResult(
                temporal_consistency=round(temp_consistency, 4),
                consistency_state=consistency_state,
                frames_evaluated=n,
                consensus_class=majority_class,
                mean_q_visual=round(mean_q, 4),
                mean_raw_confidence=round(mean_raw, 4),
                effective_confidence=round(eff_conf, 4),
                is_consistent=False,
                is_transient=True,
                reasons=reasons,
                consecutive_count=c_count,
                persistence_score=p_score,
                fault_recovered=f_recovered
            )

        # Case 3: Mixed / Conflicting / Ambiguous sequence (e.g. [BLOOM, NORMAL, BLOOM])
        consistency_state = "AMBIGUOUS"
        temp_consistency = 0.33
        reasons.append(f"Conflicting visual predictions across buffer: {classes}")
        eff_conf = records[-1].effective_confidence * temp_consistency

        return TemporalVisualConsistencyResult(
            temporal_consistency=round(temp_consistency, 4),
            consistency_state=consistency_state,
            frames_evaluated=n,
            consensus_class="UNCERTAIN",
            mean_q_visual=round(mean_q, 4),
            mean_raw_confidence=round(mean_raw, 4),
            effective_confidence=round(eff_conf, 4),
            is_consistent=False,
            is_transient=False,
            reasons=reasons,
            consecutive_count=c_count,
            persistence_score=p_score,
            fault_recovered=f_recovered
        )
