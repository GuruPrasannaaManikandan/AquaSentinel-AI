import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

@dataclass
class MultimodalEvidence:
    """
    Container for unified multimodal evidence input combining sensor and visual modalities.
    """
    sensor_dataset: str
    ml_evidence: Dict[str, Any]
    ais_evidence: Dict[str, Any]
    visual_evidence: Optional[Dict[str, Any]] = None
    sensors_data: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FusedEvidence:
    """
    Structured output produced by the FusionEngine after executing multimodal Dempster-Shafer belief fusion.
    """
    dataset: str
    final_state: str  # "NORMAL", "WARNING", "CRITICAL", "UNKNOWN_ANOMALY"
    reason_code: str  # "ML_NORMAL_AIS_NORMAL", "MULTIMODAL_BLOOM_CONFIRMED", "VISUAL_EARLY_WARNING", "VISUAL_CAMERA_FAULT", etc.
    reasoning: str
    confidence_band: str  # "LOW", "MEDIUM", "HIGH"
    multimodal: bool  # True if visual evidence was fused
    ml_evidence: Dict[str, Any]
    ais_evidence: Dict[str, Any]
    visual_evidence: Optional[Dict[str, Any]] = None
    fusion_pipeline_time_ms: float = 0.0
    system_metadata: Dict[str, Any] = field(default_factory=dict)
