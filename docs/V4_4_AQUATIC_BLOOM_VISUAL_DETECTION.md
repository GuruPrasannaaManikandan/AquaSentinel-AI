# Version 4.4 — Aquatic Bloom Visual Detection Documentation

**Date**: 2026-08-17  
**Module**: `src/cv/visual_detection.py`  
**Status**: **COMPLETE & FULLY FUNCTIONALLY VERIFIED**

---

## 1. Visual Detection Architecture & Purpose

The **Aquatic Bloom Visual Detection Layer (V4.4)** converts raw computer vision model outputs (`CVPrediction`) into structured, interpretable visual evidence (`VisualEvidence`).

```
ESP32-CAM / Physical Camera
           │
           ▼
 CameraFrame (Raw Acquisition - V4.1)
           │
           ▼
 PreprocessedImage (Hardware-Ready Preprocessor - V4.2)
           │
           ▼
 CVPrediction (Inference Engine - V4.3)
           │
           ▼
 VisualEvidence (Visual Detection & Evidence Layer - V4.4)
           │
           ▼
 [Future V4.5 Dempster-Shafer Multi-Modal Fusion Engine]
```

### Key Separation of Responsibilities:
- **V4.3 (`CVPrediction`)**: Raw output directly from the CV model (e.g. `class="ALGAL_BLOOM_RISK"`, `confidence=0.91`).
- **V4.4 (`VisualEvidence`)**: High-level evidence interpretation (e.g. `visual_state="BLOOM_EVIDENCE"`, `risk_level="HIGH"`, `evidence_strength=0.91`).
- **Control Flow Protection**: V4.4 produces evidence only and does **not** directly trigger hardware actuators or modify the finite state machine (FSM).

---

## 2. Structured Output Contract (`VisualEvidence`)

Located in [`src/cv/visual_detection.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/cv/visual_detection.py):

| Field | Type | Description |
| :--- | :--- | :--- |
| `frame_id` | `str` | Provenance link to source `CameraFrame`, `PreprocessedImage`, and `CVPrediction` |
| `timestamp` | `str` | ISO-8601 timestamp string inherited from frame |
| `source` | `str` | `"COMPUTER_VISION"` |
| `predicted_visual_class` | `str` | `"NO_BLOOM"`, `"ALGAL_BLOOM_RISK"`, `"TURBID_DISCOLORATION"`, `"UNCERTAIN"` |
| `confidence` | `float` | Raw model confidence score `[0.0, 1.0]` |
| `visual_state` | `str` | `"NO_VISUAL_BLOOM"`, `"BLOOM_EVIDENCE"`, `"TURBID_DISCOLORATION"`, `"UNCERTAIN"`, `"CAMERA_FAULT"`, `"INFERENCE_FAILURE"` |
| `risk_level` | `str` | `"NONE"`, `"LOW"`, `"MEDIUM"`, `"HIGH"`, `"CRITICAL"`, `"UNKNOWN"` |
| `evidence_strength` | `float` | Normalized evidence strength `[0.0, 1.0]` for future Dempster-Shafer mass assignment |
| `detections_count` | `int` | Total number of visual object detections |
| `bounding_boxes` | `list` | List of detected bounding box dictionaries |
| `highest_confidence_detection` | `dict` | Details of the highest confidence detection box |
| `model_name` | `str` | `"YOLOv8-AquaticBloom"` |
| `model_version` | `str` | `"1.0.0"` |
| `inference_status` | `str` | `"SUCCESS"`, `"LOW_CONFIDENCE"`, `"CAMERA_OFFLINE"`, `"CORRUPTED"`, `"MODEL_OFFLINE"` |
| `preprocessing_time_ms` | `float` | V4.2 preprocessing latency |
| `inference_time_ms` | `float` | V4.3 model inference latency |
| `visual_pipeline_time_ms` | `float` | Cumulative processing duration (`preproc + infer + evaluation`) |

---

## 3. Configurable Confidence Thresholds & Fault Handling

- **Confidence Thresholds**:
  - `high_confidence_threshold = 0.85`: High risk visual bloom evidence.
  - `medium_confidence_threshold = 0.60`: Medium risk visual bloom or turbidity evidence.
  - `low_confidence_threshold = 0.40`: Low risk / uncertain visual evidence.
- **Hardware & Software Fault Handling**:
  - **Camera Hardware Fault** (`CAMERA_OFFLINE`, `CORRUPTED`, `EMPTY_PAYLOAD`): Returns `visual_state="CAMERA_FAULT"`, `risk_level="UNKNOWN"`, `evidence_strength=0.0`.
  - **Inference Engine Failure** (`MODEL_OFFLINE`, `INFERENCE_FAILURE`): Returns `visual_state="INFERENCE_FAILURE"`, `risk_level="UNKNOWN"`, `evidence_strength=0.0`.
  - **Critical Distinction**: `"CAMERA_FAULT"` and `"NO_VISUAL_BLOOM"` are explicitly NOT equivalent. A failed camera cannot prove absence of bloom.

---

## 4. Verification & Test Suite Summary

- **Focused Visual Detection Unit Suite ([`tests/test_v4_4_visual_detection.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/tests/test_v4_4_visual_detection.py))**:
  - `test_no_bloom_prediction_evaluation`: **PASS** (`visual_state="NO_VISUAL_BLOOM"`, `risk_level="NONE"`)
  - `test_bloom_risk_prediction_evaluation`: **PASS** (`visual_state="BLOOM_EVIDENCE"`, `risk_level="HIGH"`)
  - `test_turbid_discoloration_evaluation`: **PASS** (`visual_state="TURBID_DISCOLORATION"`, `risk_level="MEDIUM"`)
  - `test_high_vs_low_confidence_interpretation`: **PASS**
  - `test_camera_fault_and_inference_failure`: **PASS** (`CAMERA_FAULT` and `INFERENCE_FAILURE` correctly differentiated)
  - `test_full_v41_v42_v43_v44_pipeline`: **PASS**
  - `test_hardware_oriented_physical_camera_end_to_end_path`: **PASS** (Simulated physical 1920x1080 JPEG frame -> `CameraFrame` -> `ImagePreprocessor` -> `AquaticBloomCVModel` -> `CVPrediction` -> `VisualDetector` -> `VisualEvidence`)
- **Full System Regression Suite (`python run_phase9.py`)**:
  - **212 Total Tests Executed** (209 passed, 3 skipped, 0 failed).
  - **100% Backward Compatibility** maintained. Zero V3.8 source files were modified.
