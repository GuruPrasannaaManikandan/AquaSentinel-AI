import time
import logging
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Tuple
from scipy.spatial.distance import cdist

from src.ais.negative_selection import NegativeSelectionAlgorithm


@dataclass
class MemoryCell:
    """
    Immunological memory detector representing an established, reinforced non-self antigen pattern.
    Provides rapid secondary immune response upon recurrent exposure.
    """
    center: np.ndarray
    affinity_radius: float
    encounter_count: int
    first_seen_timestamp: float
    last_seen_timestamp: float
    reinforcement_weight: float = 1.0
    dataset_key: str = "generic"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "center": self.center.tolist() if isinstance(self.center, np.ndarray) else list(self.center),
            "affinity_radius": round(float(self.affinity_radius), 4),
            "encounter_count": int(self.encounter_count),
            "reinforcement_weight": round(float(self.reinforcement_weight), 3),
            "dataset_key": self.dataset_key
        }


@dataclass
class AdaptiveAISResult:
    """
    Structured outcome of adaptive artificial immune system anomaly evaluation.
    Distinguishes primary immune responses (naive base detectors) from secondary
    immune responses (reinforced memory detectors).
    """
    is_anomaly: bool
    anomaly_score: float  # [0.0, 1.0]
    matched_detector_count: int
    nearest_detector_distance: float
    memory_cell_matches: int
    immune_response_type: str  # "SECONDARY_RESPONSE", "PRIMARY_RESPONSE", "SELF_TOLERANT"
    dynamic_radius_used: float
    active_memory_cells_count: int
    execution_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AdaptiveAIS:
    """
    V5.4 Adaptive Artificial Immune System.
    Wraps the frozen/verified NegativeSelectionAlgorithm base model and introduces:
    1. Secondary Immune Response via Memory Cells (clonal selection principles).
    2. Dynamic Affinity Radius based on local antigen density.
    3. Repeated Anomaly Reinforcement (recurrent threats trigger faster with higher confidence).
    4. Deterministic baseline preservation (base detectors are never mutated).
    """
    def __init__(
        self,
        base_nsa: Optional[NegativeSelectionAlgorithm] = None,
        max_memory_cells: int = 50,
        memory_radius_multiplier: float = 1.25,
        memory_formation_threshold: int = 2,
        density_sensitivity_factor: float = 0.85,
        dataset_key: str = "generic"
    ):
        self.base_nsa = base_nsa
        self.max_memory_cells = max_memory_cells
        self.memory_radius_multiplier = memory_radius_multiplier
        self.memory_formation_threshold = memory_formation_threshold
        self.density_sensitivity_factor = density_sensitivity_factor
        self.dataset_key = dataset_key

        # Memory cells storage: list of MemoryCell
        self.memory_cells: List[MemoryCell] = []
        # Transient antigen tracker for memory formation: list of (antigen, count, last_ts)
        self.candidate_antigens: List[Dict[str, Any]] = []

    def set_base_nsa(self, nsa: NegativeSelectionAlgorithm):
        """Attaches pre-trained base NegativeSelectionAlgorithm model."""
        self.base_nsa = nsa

    def clear_memory(self):
        """Clears adaptive memory cells, resetting to baseline NSA state."""
        self.memory_cells.clear()
        self.candidate_antigens.clear()

    def _compute_dynamic_radius(self, X: np.ndarray, base_radius: float) -> float:
        """
        Adjusts affinity matching radius dynamically based on sample dispersion.
        Denser regions use a tighter radius to prevent false alarms, while sparse
        regions expand slightly.
        """
        if len(X) < 2:
            return base_radius

        std_dev = float(np.mean(np.std(X, axis=0)))
        if std_dev < 1e-4:
            return base_radius

        scaling = np.clip(1.0 + (std_dev - 0.20) * self.density_sensitivity_factor, 0.70, 1.35)
        return float(base_radius * scaling)

    def _match_memory_cells(self, antigen: np.ndarray) -> Tuple[int, float]:
        """
        Matches an individual antigen vector against active memory cells.
        Returns (memory_matches_count, min_memory_distance).
        """
        if not self.memory_cells:
            return 0, float("inf")

        centers = np.array([m.center for m in self.memory_cells])
        dists = cdist(antigen.reshape(1, -1), centers, metric="euclidean")[0]

        matches = 0
        min_dist = float("inf")
        for i, d in enumerate(dists):
            if d < min_dist:
                min_dist = float(d)
            if d <= self.memory_cells[i].affinity_radius:
                matches += 1
                # Reinforce memory cell on match
                self.memory_cells[i].encounter_count += 1
                self.memory_cells[i].last_seen_timestamp = time.time()
                self.memory_cells[i].reinforcement_weight = min(2.0, self.memory_cells[i].reinforcement_weight + 0.1)

        return matches, min_dist

    def _update_memory_formation(self, antigen: np.ndarray, base_radius: float):
        """
        Tracks recurrent non-self antigens and forms new MemoryCells upon repeated exposure.
        """
        now = time.time()
        # Check if antigen is already close to an existing candidate
        found = False
        for cand in self.candidate_antigens:
            dist = float(np.linalg.norm(antigen - cand["vector"]))
            if dist <= base_radius * 0.5:
                cand["count"] += 1
                cand["last_ts"] = now
                found = True

                # Check if threshold reached to promote to MemoryCell
                if cand["count"] >= self.memory_formation_threshold and not cand.get("promoted", False):
                    cand["promoted"] = True
                    self._add_memory_cell(
                        center=cand["vector"],
                        radius=base_radius * self.memory_radius_multiplier,
                        count=cand["count"]
                    )
                break

        if not found:
            self.candidate_antigens.append({
                "vector": antigen.copy(),
                "count": 1,
                "first_ts": now,
                "last_ts": now,
                "promoted": False
            })

        # Cap candidates list to prevent memory bloat
        if len(self.candidate_antigens) > 100:
            self.candidate_antigens.sort(key=lambda c: c["last_ts"])
            self.candidate_antigens = self.candidate_antigens[-50:]

    def _add_memory_cell(self, center: np.ndarray, radius: float, count: int):
        """Instantiates and inserts a new memory cell, evicting oldest if full."""
        now = time.time()
        cell = MemoryCell(
            center=center.copy(),
            affinity_radius=radius,
            encounter_count=count,
            first_seen_timestamp=now,
            last_seen_timestamp=now,
            reinforcement_weight=1.2,
            dataset_key=self.dataset_key
        )

        if len(self.memory_cells) >= self.max_memory_cells:
            # Evict least recently used cell
            self.memory_cells.sort(key=lambda m: m.last_seen_timestamp)
            self.memory_cells.pop(0)

        self.memory_cells.append(cell)
        logging.info(f"AdaptiveAIS: Created MemoryCell #{len(self.memory_cells)} for {self.dataset_key} (r={radius:.3f}).")

    def predict_adaptive(
        self,
        X: np.ndarray,
        base_radius: Optional[float] = None
    ) -> List[AdaptiveAISResult]:
        """
        Executes adaptive anomaly detection across batch or single antigen array X.
        Evaluates memory cells first (Secondary Response), then falls back to base NSA (Primary Response).
        """
        t0 = time.perf_counter()
        X_arr = np.asarray(X, dtype=np.float32)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)

        N, D = X_arr.shape
        default_r = base_radius if base_radius is not None else (self.base_nsa.self_radius if self.base_nsa else 0.1)
        dynamic_r = self._compute_dynamic_radius(X_arr, default_r)

        results = []

        # Run base NSA if available
        base_anom = np.zeros(N, dtype=bool)
        base_scores = np.zeros(N, dtype=np.float32)
        base_matches = np.zeros(N, dtype=int)
        base_dists = np.full(N, np.inf, dtype=np.float32)

        if self.base_nsa is not None:
            b_anom, b_scores, b_matches, b_dists = self.base_nsa.predict_anomaly(X_arr, matching_radius=dynamic_r)
            base_anom = b_anom
            base_scores = b_scores
            base_matches = b_matches
            base_dists = b_dists

        for i in range(N):
            antigen = X_arr[i]
            # 1. Match against immunological memory cells (Secondary Immune Response)
            mem_matches, mem_dist = self._match_memory_cells(antigen)

            b_is_anom = bool(base_anom[i])
            b_score = float(base_scores[i])
            b_match_cnt = int(base_matches[i])
            b_dist = float(base_dists[i])

            nearest_dist = min(b_dist, mem_dist)

            if mem_matches > 0:
                # Secondary Immune Response: Faster, higher confidence
                immune_type = "SECONDARY_RESPONSE"
                is_anom = True
                # Boost confidence from memory reinforcement
                anom_score = min(1.0, max(b_score, 0.85) + 0.10 * min(mem_matches, 3))
                total_matches = b_match_cnt + mem_matches
            elif b_is_anom:
                # Primary Immune Response: Matched naive base detector
                immune_type = "PRIMARY_RESPONSE"
                is_anom = True
                anom_score = b_score
                total_matches = b_match_cnt
                # Track for prospective memory formation
                self._update_memory_formation(antigen, default_r)
            else:
                # Tolerant (Self)
                immune_type = "SELF_TOLERANT"
                is_anom = False
                anom_score = b_score
                total_matches = 0

            elapsed_ms = (time.perf_counter() - t0) * 1000.0 / N

            results.append(AdaptiveAISResult(
                is_anomaly=is_anom,
                anomaly_score=round(float(anom_score), 4),
                matched_detector_count=total_matches,
                nearest_detector_distance=round(float(nearest_dist), 4),
                memory_cell_matches=mem_matches,
                immune_response_type=immune_type,
                dynamic_radius_used=round(dynamic_r, 4),
                active_memory_cells_count=len(self.memory_cells),
                execution_time_ms=round(elapsed_ms, 3),
                metadata={
                    "dataset_key": self.dataset_key,
                    "base_anomaly": b_is_anom,
                    "memory_distance": round(mem_dist, 4) if mem_dist != float("inf") else None
                }
            ))

        return results
