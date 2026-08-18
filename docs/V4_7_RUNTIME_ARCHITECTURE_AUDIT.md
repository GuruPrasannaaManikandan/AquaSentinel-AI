# Version 4.7 — Real-Time Multimodal Runtime & Reliability Architectural Audit

**Date**: 2026-08-17  
**Target Module**: [`src/fusion/runtime_orchestrator.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/fusion/runtime_orchestrator.py)  
**Status**: **PHASE 1 ARCHITECTURAL AUDIT & PROPOSAL (STOPPED FOR APPROVAL)**

---

## 1. Current Runtime Execution Model

- **Synchronous Pipelines**:
  - Camera acquisition: `VirtualCameraDriver.capture_frame()` $\rightarrow$ `CameraFrame`.
  - Image Preprocessing: `ImagePreprocessor.process()` (HWC/NHWC standard normalization).
  - CV Model Inference: `AquaticBloomCVModel.predict()` (PyTorch MobileNetV3 CPU execution).
  - Visual Detection: `VisualDetector.evaluate_prediction()` $\rightarrow$ `VisualEvidence`.
  - Multimodal Fusion: `FusionEngine.fuse()` $\rightarrow$ `FusedEvidence`.
  - Decision Adapter: `DecisionAdapter.adapt()` $\rightarrow$ `SystemEvent`.
- **Asynchronous / Task-Scheduled**:
  - `ESP32Device` RTOS `SimpleScheduler`: Manages tick-based `SensorTask` (poll & validate sensors) and `CommTask` (dequeue telemetry & publish to MQTT).
  - MQTT Client (`paho-mqtt` background network loop).

---

## 2. Existing Queues & Memory Boundaries

- **`src/iot/scheduler.py`**:
  - `telemetry_queue`: FreeRTOS `Queue` passing telemetry from `SensorTask` to `CommTask`.
  - `cycle_output_queue`: FreeRTOS `Queue` capturing published cycle output.
- **Gateway & Image Processing**:
  - Currently processes payloads synchronously. To prevent unbounded memory growth during high-rate camera streams, V4.7 will introduce bounded queues (`maxsize=5`) using a **drop-oldest / newest-frame-preservation** strategy.

---

## 3. Existing Scheduler Interaction

- `SimpleScheduler` in `src/iot/scheduler.py` handles task scheduling inside `ESP32Device` based on tick intervals and task priority (Priority 3: `HealthTask`, Priority 2: `SensorTask`, Priority 1: `CommTask`).
- Task execution is cooperative and non-blocking.

---

## 4. Camera & CV Model Lifecycle

- **`VirtualCameraDriver`**: Initialized once (`init()`), generates `CameraFrame` objects. Supports scenario switching (`NORMAL`, `KNOWN_BLOOM_RISK`) and fault injection (`CAMERA_OFFLINE`, `CORRUPTED_FRAME`).
- **`AquaticBloomCVModel`**: Initialized and loaded **ONCE** at startup (`load()`). Reuses trained PyTorch MobileNetV3 weights (`models/cv/aquatic_bloom_mobilenetv3.pt`) across all incoming frames without reloading weights.

---

## 5. Sensor Lifecycle & Edge Validation

- `AquaticSensorSimulator` generates raw telemetry values (temperature, pH, DO, salinity, turbidity).
- `VirtualEnvironment` updates environmental parameters.
- `HAL` reads sensor channels.
- `EdgeValidator` enforces physical bounds, setting `sensor_status` (`"OK"` or `"FAULT"`).

---

## 6. Fault & Recovery Mechanisms

- **Sensor Faults**: `sensor_status == "FAULT"` causes Gateway to bypass model inference, emitting `final_state = "SENSOR_FAULT"` and `reason_code = "SENSOR_FAULT_BYPASS"`.
- **Camera Faults / Offline**: `CameraFrame.status` in `["CAMERA_OFFLINE", "CORRUPTED", "CAMERA_FAULT"]` propagates cleanly to `VisualEvidence(visual_state="CAMERA_FAULT")`. `FusionEngine` returns `reason_code = "VISUAL_CAMERA_FAULT"`, preserving the base sensor decision without false `NO_BLOOM` alerts or system crashes.
- **Communication Interruption**: MQTT disconnects trigger `ESP32Device` transition to `ERROR` state. Calling `run_reconnection()` restores network connection and transitions back to `ONLINE`.

---

## 7. Location of V4.7 Runtime Orchestration

- **Module**: New class `MultimodalRuntimeOrchestrator` in [`src/fusion/runtime_orchestrator.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/fusion/runtime_orchestrator.py).
- **Responsibilities**:
  - Manages bounded ring-buffer queues for continuous camera frame streams (preserving the newest usable frame).
  - Controls single-instance model lifecycle (loads PyTorch weights once and reuses them).
  - Orchestrates real-time pipeline execution: `CameraFrame` + Telemetry $\rightarrow$ `ImagePreprocessor` $\rightarrow$ `AquaticBloomCVModel` $\rightarrow$ `VisualDetector` $\rightarrow$ `DecisionPipeline` $\rightarrow$ `FusionEngine` $\rightarrow$ `DecisionAdapter` $\rightarrow$ `SystemEvent`.
  - Measures pipeline latency breakdown (`camera_acquisition_ms`, `preprocessing_ms`, `inference_ms`, `detection_ms`, `fusion_ms`, `adapter_ms`, `total_pipeline_ms`) and throughput metrics across sustained processing runs.

---

## 8. Files to be Created / Modified

1. [`src/fusion/runtime_orchestrator.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/fusion/runtime_orchestrator.py) **[NEW]**: Bounded real-time multimodal runtime orchestrator.
2. [`tests/test_v4_7_runtime_reliability.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/tests/test_v4_7_runtime_reliability.py) **[NEW]**: Sustained 100+ observation reliability & fault injection test suite.
3. [`docs/V4_7_REAL_TIME_RUNTIME_RELIABILITY.md`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/V4_7_REAL_TIME_RUNTIME_RELIABILITY.md) **[NEW]**: Comprehensive runtime & reliability documentation report.

---

## 9. Protection of Frozen V3.8 Architecture

- **FROZEN SOURCE FILES (ZERO MODIFICATIONS)**:
  - `src/iot/esp32_device.py`
  - `src/iot/communication.py`
  - `src/iot/scheduler.py`
  - `src/iot/hal.py`
  - `src/iot/actuators.py`
  - Physical sensor/actuator drivers

---

## 10. Proposed Minimal Implementation Strategy

- Implement `MultimodalRuntimeOrchestrator` in `src/fusion/runtime_orchestrator.py` without modifying any frozen files.
- The orchestrator will reuse `DecisionPipeline`, `AquaticBloomCVModel`, `ImagePreprocessor`, `VisualDetector`, and `DecisionAdapter`.
- Model loading is performed **ONCE** upon orchestrator initialization (`self.cv_model.load()`).
- Bounded queues (`Queue(maxsize=5)`) ensure drop-oldest / drop-newest memory safety.
- Sustained simulation test in `tests/test_v4_7_runtime_reliability.py` will execute 100+ observations under continuous fault injections (camera offline, frame loss, sensor fault, recovery) to prove zero memory leaks, zero model reloads, and deterministic recovery.
