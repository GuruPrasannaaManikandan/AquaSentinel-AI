# Version 4.2 — Image Preprocessing Layer & Hardware-Readiness Documentation

**Date**: 2026-08-17  
**Module**: `src/cv/image_preprocessing.py`  
**Status**: **COMPLETE & FULLY FUNCTIONALLY VERIFIED (HARDWARE-READY)**

---

## 1. V4.2 Architecture & Hardware-Readiness Concept

The **Image Preprocessing Layer (V4.2)** acts as a production-oriented, hardware-independent data preparation bridge between **Camera Acquisition (V4.1 / ESP32-CAM)** and downstream **Computer Vision Model Inference (V4.3)**.

```
Virtual Camera (V4.1)                  ESP32-CAM / Physical Camera
         │                                            │
         └───> CameraFrame (Raw Acquired Payload) <───┘
                         │
                         ▼
             ImagePreprocessor (V4.2)
                         │
                         ▼
        PreprocessedImage (Model-Ready Input)
                         │
                         ▼
            [CV Model Inference (V4.3)]
```

### Key Hardware-Readiness Guarantees:
1. **Source Independence**: The preprocessor accepts generic `CameraFrame` instances. It has zero code dependency on `VirtualCameraDriver` and operates identically for physical ESP32-CAM frames.
2. **Raw Payload Preservation**: The original `CameraFrame` remains untouched for telemetry logging, debugging, and remote diagnostics.
3. **Transport Separation**: Image preprocessing contains zero network transport (Wi-Fi/MQTT) code.
4. **Memory Awareness**: On-the-fly single-pass frame execution without frame accumulation or unbounded memory buffering.

---

## 2. Preprocessing Contract & Data Structures

### `PreprocessedImage` Dataclass
Located in [`src/cv/image_preprocessing.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/cv/image_preprocessing.py):

| Field | Type | Description |
| :--- | :--- | :--- |
| `frame_id` | `str` | Provenance link to original `CameraFrame.frame_id` |
| `timestamp` | `str` | ISO-8601 timestamp inherited from `CameraFrame` |
| `original_width` | `int` | Raw acquired frame width (e.g., 1920 or 640) |
| `original_height` | `int` | Raw acquired frame height (e.g., 1080 or 480) |
| `processed_width` | `int` | Preprocessed output tensor width (e.g., 224) |
| `processed_height` | `int` | Preprocessed output tensor height (e.g., 224) |
| `channels` | `int` | Number of color channels (3) |
| `color_space` | `str` | `"RGB"` or `"BGR"` |
| `data_format` | `str` | `"HWC"` (Height-Width-Channel) or `"NHWC"` (Batch-Height-Width-Channel) |
| `dtype` | `str` | `"float32"` (normalized) or `"uint8"` (un-normalized) |
| `tensor_data` | `np.ndarray` | Formatted NumPy array/tensor ready for CV model consumption |
| `valid` | `bool` | `True` if preprocessing succeeded; `False` if failed/corrupted |
| `status` | `str` | `"OK"`, `"NULL_FRAME"`, `"EMPTY_PAYLOAD"`, `"CORRUPTED"`, `"DECODE_FAILURE"`, `"CAMERA_OFFLINE"` |
| `metadata` | `dict` | Includes `preprocessing_time_ms`, aspect ratio strategy, normalization parameters, and source hardware metadata |

---

## 3. Configurable Transformations & Model-Input Contract

The `ImagePreprocessor` supports:
- **Aspect Ratio Strategies (`aspect_ratio_mode`)**:
  - `"STRETCH"`: Direct bilinear scaling to `target_size`.
  - `"LETTERBOX"`: Aspect-ratio preserving scaling with neutral gray padding `(128, 128, 128)` (default for geometry-sensitive bloom pattern preservation).
  - `"CROP"`: Center crop preserving original aspect ratio.
- **Normalization Options (`normalization_type`)**:
  - `"RESCALE"`: Scaling pixel values to `[0.0, 1.0]`.
  - `"STANDARD"`: Z-score standardization `(x / 255.0 - mean) / std` using configurable `mean` and `std` vectors.
  - `"NONE"`: Unchanged integer pixel values `[0, 255]` (`uint8`).
- **Latency Measurement**: Captures wall-clock `preprocessing_time_ms` per frame for edge pipeline performance profiling.

---

## 4. Hardware Fault Handling & Reliability

Preprocessing failures yield structured `PreprocessedImage` objects (`valid=False`) without throwing unhandled runtime exceptions:
- `"NULL_FRAME"`: Input `CameraFrame` is `None`.
- `"EMPTY_PAYLOAD"`: Image byte stream is 0 bytes.
- `"CAMERA_OFFLINE"`: Camera sensor hardware offline.
- `"CORRUPTED"`: Non-decodable byte payload.
- `"DECODE_FAILURE"`: PIL image decoding failure.

---

## 5. Verification & Test Suite Summary

- **Focused Hardware-Readiness Unit Suite ([`tests/test_v4_2_image_preprocessing.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/tests/test_v4_2_image_preprocessing.py))**:
  - `test_valid_normal_frame_preprocessing`: **PASS**
  - `test_hardware_replacement_contract`: **PASS** (Constructs raw 1920x1080 physical ESP32-CAM frame; proves identical preprocessing behavior)
  - `test_raw_frame_non_mutation`: **PASS** (Proves `CameraFrame` payload is unchanged)
  - `test_aspect_ratio_strategies`: **PASS** (Tests `STRETCH`, `LETTERBOX`, `CROP`)
  - `test_normalization_types`: **PASS** (Tests `RESCALE`, `STANDARD`, `NONE`)
  - `test_sequential_frame_streaming_integrity`: **PASS**
  - `test_fault_handling_and_status_codes`: **PASS**
- **Full System Regression Suite (`python run_phase9.py`)**:
  - **198 Total Tests Executed** (195 passed, 3 skipped, 0 failed).
  - **100% Backward Compatibility** maintained with V4.1 and frozen V3.8 architecture. Zero V3.8 source files were modified.
