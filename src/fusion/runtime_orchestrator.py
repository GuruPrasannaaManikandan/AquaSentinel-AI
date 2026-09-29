import time
import queue
import logging
import datetime
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List

from src.cv.camera_driver import CameraFrame, BaseCameraDriver
from src.cv.image_preprocessing import ImagePreprocessor, PreprocessedImage
from src.cv.cv_model import AquaticBloomCVModel, CVPrediction
from src.cv.visual_detection import VisualDetector, VisualEvidence
from src.fusion.fusion_engine import FusionEngine
from src.fusion.decision_pipeline import DecisionPipeline
from src.fusion.decision_adapter import DecisionAdapter, SystemEvent

@dataclass
class LatencyMetrics:
    """Breakdown of processing timings in milliseconds."""
    camera_acquisition_ms: float = 0.0
    preprocessing_ms: float = 0.0
    inference_ms: float = 0.0
    detection_ms: float = 0.0
    fusion_ms: float = 0.0
    adapter_ms: float = 0.0
    total_pipeline_ms: float = 0.0

@dataclass
class MultimodalObservationResult:
    """Container for the output of a single real-time multimodal observation."""
    observation_id: str
    timestamp: str
    decision_payload: Dict[str, Any]
    system_event: Dict[str, Any]
    latency: LatencyMetrics
    camera_status: str = "OK"
    sensor_status: str = "OK"
    modality_availability: Dict[str, bool] = field(default_factory=dict)
    queue_occupancy: int = 0

class MultimodalRuntimeOrchestrator:
    """
    Real-time Multimodal Runtime Orchestrator (V4.7).
    Coordinates continuous stream ingestion, bounded buffering, model lifecycle management,
    fault propagation/recovery, latency profiling, and system event generation.
    """
    def __init__(
        self,
        workspace_dir: Optional[str] = None,
        max_queue_size: int = 5,
        target_size: tuple = (224, 224)
    ):
        self.workspace_dir = workspace_dir
        self.max_queue_size = max_queue_size
        self.camera_frame_queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        
        # Instantiate and initialize components ONCE at startup
        self.preprocessor = ImagePreprocessor(target_size=target_size, color_space="RGB", normalization_type="RESCALE")
        self.cv_model = AquaticBloomCVModel()
        self.cv_model.load() # Single model load call
        self.model_load_count = 1
        
        self.visual_detector = VisualDetector()
        self.decision_pipeline = DecisionPipeline(workspace_dir=workspace_dir)
        self.decision_adapter = self.decision_pipeline.decision_adapter

        # Performance counters
        self.total_observations = 0
        self.processed_frames = 0
        self.dropped_frames = 0
        self.failed_frames = 0
        self.max_queue_occupancy = 0
        self.latencies: List[LatencyMetrics] = []
        self.start_time = time.time()

    def enqueue_camera_frame(self, frame: CameraFrame) -> bool:
        """
        Enqueues incoming camera frame into bounded queue.
        Enforces DROP-OLDEST (NEWEST-FRAME PRESERVATION) policy if queue is full.
        """
        queue_full = False
        if self.camera_frame_queue.full():
            try:
                dropped = self.camera_frame_queue.get_nowait()
                self.dropped_frames += 1
                queue_full = True
            except queue.Empty:
                pass
        
        self.camera_frame_queue.put(frame)
        current_occ = self.camera_frame_queue.qsize()
        if current_occ > self.max_queue_occupancy:
            self.max_queue_occupancy = current_occ
        return not queue_full

    def process_multimodal_observation(
        self,
        dataset_key: str,
        X_df,
        sensors: Optional[Dict[str, Any]] = None,
        camera_frame: Optional[CameraFrame] = None,
        matching_radius: Optional[float] = None
    ) -> MultimodalObservationResult:
        """
        Processes a single continuous multimodal observation with full latency tracking and fault safety.
        """
        t0 = time.perf_counter()
        obs_id = f"obs_{self.total_observations + 1:06d}"
        self.total_observations += 1
        
        # If camera frame is passed directly, enqueue it
        if camera_frame is not None:
            self.enqueue_camera_frame(camera_frame)
        
        # Dequeue latest frame if available
        active_frame = None
        if not self.camera_frame_queue.empty():
            active_frame = self.camera_frame_queue.get()
            
        current_occ = self.camera_frame_queue.qsize()
        t1 = time.perf_counter()
        acq_ms = (t1 - t0) * 1000.0

        # Execute CV pipeline if frame is present and valid
        preproc_ms = 0.0
        infer_ms = 0.0
        detect_ms = 0.0
        visual_ev = None
        camera_status = "UNAVAILABLE"

        if active_frame is not None:
            camera_status = active_frame.status
            if active_frame.quality_valid and active_frame.status == "OK":
                # Preprocessing
                t_p0 = time.perf_counter()
                preproc_img = self.preprocessor.process(active_frame)
                t_p1 = time.perf_counter()
                preproc_ms = (t_p1 - t_p0) * 1000.0

                # Inference using loaded model
                t_i0 = time.perf_counter()
                pred = self.cv_model.predict(preproc_img)
                t_i1 = time.perf_counter()
                infer_ms = (t_i1 - t_i0) * 1000.0

                # Visual detection interpretation
                t_d0 = time.perf_counter()
                visual_ev = self.visual_detector.evaluate_prediction(pred)
                t_d1 = time.perf_counter()
                detect_ms = (t_d1 - t_d0) * 1000.0
                
                self.processed_frames += 1
            else:
                # Camera fault, temporal fault, or offline
                self.failed_frames += 1
                reason_code = active_frame.metadata.get("reason_code") or f"VISUAL_{active_frame.status}"
                visual_ev = VisualEvidence(
                    frame_id=active_frame.frame_id,
                    timestamp=active_frame.timestamp,
                    predicted_visual_class="UNCERTAIN",
                    confidence=0.0,
                    visual_state="CAMERA_FAULT",
                    risk_level="UNKNOWN",
                    q_visual=0.0,
                    quality_state="CORRUPTED",
                    effective_confidence=0.0,
                    metadata={"reason_code": reason_code, **active_frame.metadata}
                )
        else:
            visual_ev = None

        # Execute Fusion Pipeline
        t_f0 = time.perf_counter()
        decision_result = self.decision_pipeline.run_pipeline(
            dataset_key=dataset_key,
            X=X_df,
            matching_radius=matching_radius,
            sensors=sensors,
            visual_evidence=visual_ev
        )
        t_f1 = time.perf_counter()
        fusion_ms = (t_f1 - t_f0) * 1000.0

        sys_evt = decision_result.get("system_event", {})
        adapter_ms = sys_evt.get("adapter_time_ms", 0.0)
        
        t_end = time.perf_counter()
        total_ms = (t_end - t0) * 1000.0

        latency_metrics = LatencyMetrics(
            camera_acquisition_ms=acq_ms,
            preprocessing_ms=preproc_ms,
            inference_ms=infer_ms,
            detection_ms=detect_ms,
            fusion_ms=fusion_ms,
            adapter_ms=adapter_ms,
            total_pipeline_ms=total_ms
        )
        self.latencies.append(latency_metrics)

        sensor_status = sensors.get("sensor_status", "OK") if isinstance(sensors, dict) else "OK"
        modality_avail = {
            "sensor": sensor_status != "FAULT",
            "visual": active_frame is not None and active_frame.quality_valid and active_frame.status == "OK"
        }

        return MultimodalObservationResult(
            observation_id=obs_id,
            timestamp=datetime.datetime.now().isoformat(),
            decision_payload=decision_result,
            system_event=sys_evt,
            latency=latency_metrics,
            camera_status=camera_status,
            sensor_status=sensor_status,
            modality_availability=modality_avail,
            queue_occupancy=current_occ
        )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculates and returns HOST/GATEWAY CPU latency and throughput metrics.
        """
        if not self.latencies:
            return {"status": "NO_DATA"}

        totals = [m.total_pipeline_ms for m in self.latencies]
        preprocs = [m.preprocessing_ms for m in self.latencies if m.preprocessing_ms > 0]
        infers = [m.inference_ms for m in self.latencies if m.inference_ms > 0]
        fusions = [m.fusion_ms for m in self.latencies]

        elapsed_sec = time.time() - self.start_time

        return {
            "benchmark_environment": "GATEWAY/HOST_CPU",
            "total_observations": self.total_observations,
            "processed_frames": self.processed_frames,
            "dropped_frames": self.dropped_frames,
            "failed_frames": self.failed_frames,
            "model_load_count": self.model_load_count,
            "max_queue_occupancy": self.max_queue_occupancy,
            "throughput_obs_per_sec": round(self.total_observations / max(0.001, elapsed_sec), 2),
            "latency_ms": {
                "total_mean": round(float(np.mean(totals)), 3),
                "total_median": round(float(np.median(totals)), 3),
                "total_p95": round(float(np.percentile(totals, 95)), 3),
                "total_max": round(float(np.max(totals)), 3),
                "preprocessing_mean": round(float(np.mean(preprocs)), 3) if preprocs else 0.0,
                "inference_mean": round(float(np.mean(infers)), 3) if infers else 0.0,
                "fusion_mean": round(float(np.mean(fusions)), 3)
            }
        }
