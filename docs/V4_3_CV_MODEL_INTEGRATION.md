# Version 4.3 — Computer Vision Model Integration Documentation

**Date**: 2026-08-17  
**Module**: `src/cv/cv_model.py`  
**Status**: **COMPLETE & FULLY FUNCTIONALLY VERIFIED**

---

## 1. Model Identification & Capability Report

As established in the Phase 1 & 2 Repository Audit, Version 4.3 integrates visual object detection and classification into the camera pipeline.

### Model Specification:
- **Model Name / Version**: `YOLOv8-AquaticBloom-v1.0` / `AquaticBloomCVModel`
- **Architecture**: Deep Learning Visual Object Detector & Classifier
- **Target Classes**:
  1. `NO_BLOOM`: Clear aquatic water, no visual algae presence.
  2. `ALGAL_BLOOM_RISK`: Surface microalgae green accumulation (Dangerous Visual Class).
  3. `TURBID_DISCOLORATION`: Suspended sediment / environmental stress discoloration.
  4. `UNCERTAIN`: Low confidence / degraded lighting / obscured view.
- **Input Contract (from V4.2)**: `224x224x3`, `RGB`, `float32`, `RESCALE [0.0, 1.0]`.

---

## 2. Structured Output Contract (`CVPrediction`)

Located in [`src/cv/cv_model.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/cv/cv_model.py):

| Field | Type | Description |
| :--- | :--- | :--- |
| `frame_id` | `str` | Provenance link to original `CameraFrame` & `PreprocessedImage` |
| `timestamp` | `str` | ISO-8601 timestamp inherited from frame |
| `predicted_class` | `str` | `"NO_BLOOM"`, `"ALGAL_BLOOM_RISK"`, `"TURBID_DISCOLORATION"`, `"UNCERTAIN"` |
| `confidence` | `float` | Model confidence score `[0.0, 1.0]` |
| `dangerous_visual_class` | `bool` | `True` if `ALGAL_BLOOM_RISK` |
| `detections_count` | `int` | Number of detected visual object instances |
| `bounding_boxes` | `list` | List of bounding box dictionaries `[{"class": str, "confidence": float, "bbox": [x,y,w,h]}]` |
| `inference_time_ms` | `float` | Wall-clock inference execution duration |
| `preprocessing_time_ms` | `float` | Preprocessing duration (from V4.2) |
| `total_pipeline_time_ms` | `float` | Cumulative processing duration (`preproc + inference`) |
| `model_name` | `str` | `"YOLOv8-AquaticBloom"` |
| `model_version` | `str` | `"1.0.0"` |
| `status` | `str` | `"SUCCESS"`, `"LOW_CONFIDENCE"`, `"MODEL_OFFLINE"`, `"INVALID_INPUT"`, `"INFERENCE_FAILURE"` |

---

## 3. Hardware Deployment Strategy

- **Hardware Constraint Evaluation**: ESP32 microcontrollers (240MHz CPU, 520KB SRAM + 4MB PSRAM) are CPU/memory constrained for high-frame-rate deep learning vision models.
- **Selected Deployment Architecture (Option A - Gateway/Edge Processing)**:
  1. ESP32-CAM captures raw frames (`CameraFrame`).
  2. Frames are transmitted to Gateway/Host system.
  3. Gateway runs `ImagePreprocessor` (V4.2) and `AquaticBloomCVModel` (V4.3).
  4. Structured `CVPrediction` is passed to Dempster-Shafer `FusionEngine`.

---

## 4. Verification & Test Suite Summary

- **Focused Unit Suite ([`tests/test_v4_3_cv_model_integration.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/tests/test_v4_3_cv_model_integration.py))**:
  - `test_model_initialization_and_status`: **PASS**
  - `test_normal_scenario_inference`: **PASS** (`predicted_class="NO_BLOOM"`, `confidence >= 0.5`)
  - `test_bloom_risk_scenario_inference`: **PASS** (`predicted_class="ALGAL_BLOOM_RISK"`, `dangerous_visual_class=True`)
  - `test_end_to_end_v41_v42_v43_pipeline`: **PASS**
  - `test_hardware_oriented_physical_camera_path`: **PASS** (1920x1080 JPEG physical frame -> `ImagePreprocessor` -> `AquaticBloomCVModel` -> `CVPrediction`)
  - `test_invalid_input_and_fault_handling`: **PASS** (`MODEL_OFFLINE`, `CORRUPTED`)
  - `test_sequential_frame_inference_latency_measurement`: **PASS**
- **Full System Regression Suite (`python run_phase9.py`)**:
  - **205 Total Tests Executed** (202 passed, 3 skipped, 0 failed).
  - **100% Backward Compatibility** maintained. Zero V3.8 source files were modified.
