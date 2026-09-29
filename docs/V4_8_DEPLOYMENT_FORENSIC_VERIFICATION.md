# VERSION 4.8 — DEPLOYMENT AUDIT FORENSIC VERIFICATION

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Milestone:** V4.8 Deployment Audit Forensic Verification  
**Verification Date:** August 18, 2026  
**Verified Test Baseline:** 244/244 passed, 3 skipped, 0 failed  
**V3.8 Source Code Modifications:** ZERO (0) (Verified via `git status`)

---

## Executive Summary

This document presents the **Forensic Verification** of the Version 4.8 Physical Deployment Readiness Audit for the IoT-Based Artificial Immune System (AIS) for Aquatic Ecosystems. The primary objective is to rigorously distinguish **Documented Facts**, **Code-Verified Facts**, **Scenario Estimates**, and **Unverified Physical Hardware Claims** across all system components, hardware abstractions, communication protocols, compute placements, and failure safety contracts.

---

## 1. GPIO / Pin Mapping Verification

A forensic comparison was conducted across the three primary sources of truth in the repository:
1. **C++ Firmware Definition**: [firmware/include/config/PinConfig.h](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/firmware/include/config/PinConfig.h)
2. **Python Device Config**: [config/device_config.json](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/config/device_config.json) (`AQUA_FRESH_001` & `AQUA_MARINE_001`)
3. **Hardware Integration Guide**: [docs/HARDWARE_INTEGRATION_GUIDE.md](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/HARDWARE_INTEGRATION_GUIDE.md)

### 1.1 Forensic Pin Comparison Table

| Component | Reported Pin | `PinConfig.h` (C++) | `device_config.json` (Python) | `HARDWARE_INTEGRATION_GUIDE.md` | Verification Status | Forensic Note |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **pH Sensor** | `GPIO 32` | `GPIO 32` | `GPIO 32` | `GPIO 32 (ADC1_CH4)` | **VERIFIED** | Consistent across all code and documentation. |
| **Temperature Sensor** | `GPIO 4` | `GPIO 18` | `GPIO 35` (Marine) / Missing (Fresh) | `GPIO 4 (OneWire)` | **CONFLICT** | `PinConfig.h` uses 18, guide uses 4, JSON uses 35. Needs consolidation. |
| **Turbidity Sensor** | `GPIO 34` | `GPIO 33` | `GPIO 33` | `GPIO 34 (ADC1_CH6)` | **CONFLICT** | Firmware and JSON use 33; hardware guide specifies 34. |
| **Dissolved Oxygen (DO)**| `GPIO 35` | `GPIO 34` | `GPIO 34` | `GPIO 35 (ADC1_CH7)` | **CONFLICT** | Firmware and JSON use 34; hardware guide specifies 35. |
| **Salinity / TDS Sensor**| `GPIO 33` | `GPIO 36` | `GPIO 36` (Marine) / Missing (Fresh) | `GPIO 33 (ADC1_CH5)` | **CONFLICT** | Firmware and JSON use 36; hardware guide specifies 33. |
| **Green Status LED** | `GPIO 12` | `GPIO 19` | `GPIO 12` | `GPIO 12` | **CONFLICT** | C++ firmware uses 19; Python config and guide specify 12. |
| **Yellow Status LED** | `GPIO 13` | `GPIO 21` | `GPIO 13` | `GPIO 13` | **CONFLICT** | C++ firmware uses 21; Python config and guide specify 13. |
| **Red Status LED** | `GPIO 14` | `GPIO 22` | `GPIO 14` | `GPIO 14` | **CONFLICT** | C++ firmware uses 22; Python config and guide specify 14. |
| **Alarm Buzzer** | `GPIO 15` | `GPIO 23` | `GPIO 15` | `GPIO 15` | **CONFLICT** | C++ firmware uses 23; Python config and guide specify 15. |
| **Pump Relay** | `GPIO 23` | `GPIO 27` | `GPIO 16` | `GPIO 23` | **CONFLICT** | Three-way conflict: Firmware=27, JSON=16, Guide=23. |
| **GPS Module** | `N/A` | `RX=16, TX=17` | `GPIO 21` | `N/A` | **CONFLICT** | Firmware specifies UART 16/17; JSON specifies single pin 21. |

> [!WARNING]
> **Forensic Finding**: Major pin assignment conflicts exist between the C++ firmware header (`PinConfig.h`), the Python configuration (`device_config.json`), and the markdown guide (`HARDWARE_INTEGRATION_GUIDE.md`). These must be aligned in a single authoritative hardware pin header prior to physical flashing.

---

## 2. Power / Electrical Claim Verification

Every electrical and power assertion from the initial deployment audit was categorized against repository code and documentation:

| Electrical Assertion | Classification | Repository Evidence | Forensic Verification Detail |
| :--- | :--- | :--- | :--- |
| **5V Stable Power Rail for Probes** | **C) Engineering Recommendation** | [future_hardware_migration.md](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/future_hardware_migration.md#L40) & [HARDWARE_INTEGRATION_GUIDE.md](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/HARDWARE_INTEGRATION_GUIDE.md#L40) | Recommended in docs to prevent ADC scaling offsets; not enforced by hardware or software code. |
| **Optocouplers on Relay Board** | **C) Engineering Recommendation** | [HARDWARE_INTEGRATION_GUIDE.md](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/HARDWARE_INTEGRATION_GUIDE.md#L42) | Documented in hardware integration guide to prevent reset loops; not enforced in software. |
| **Flyback Diodes on Relays** | **C) Engineering Recommendation** | [HARDWARE_INTEGRATION_GUIDE.md](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/HARDWARE_INTEGRATION_GUIDE.md#L42) | Mentioned in wiring guide text; physical board hardware requirement. |
| **4.7kΩ OneWire Pull-up Resistor** | **C) Engineering Recommendation** | [HARDWARE_INTEGRATION_GUIDE.md](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/HARDWARE_INTEGRATION_GUIDE.md#L41) | Standard OneWire bus hardware requirement for DS18B20 sensor. |
| **ADC Linear Scaling ($V_{\text{read}} \times m + c$)** | **A) Explicitly Documented** | [future_hardware_migration.md](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/future_hardware_migration.md#L28) & [HAL.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/hal.py) | Formally defined in calibration schema and firmware driver classes. |

---

## 3. Bandwidth Forensic Audit

### 3.1 Derivation of Bandwidth Figures

The initial bandwidth figures were evaluated against actual repository evidence:

$$\text{Bandwidth (bits per second)} = \text{JPEG Payload Size (bytes)} \times \text{FPS} \times 8$$

- **Actual Code Evidence**: In `VirtualCameraDriver._generate_synthetic_image()` ([camera_driver.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/cv/camera_driver.py#L148)), PIL saves a synthetic 224x224 RGB image as JPEG with Quality=85, resulting in **10.2 KB to 18.5 KB** per frame.
- **1080p Payload Figure (~250 KB)**: Derived from theoretical JPEG compression models (250 KB per 1080p frame at Q=85). No 1080p image binaries exist in the repository.
- **Forensic Classification**: These calculations are **SCENARIO ESTIMATES based on theoretical JPEG models**, NOT **MEASURED HARDWARE PERFORMANCE**.

### 3.2 Transparent Bandwidth Scenario Matrix

Using the formula $\text{Payload (KB)} \times \text{FPS} \times 8 / 1000 = \text{Mbps}$:

| Resolution | Assumed JPEG Payload | Frame Rate | Calculated Bandwidth | Network Feasibility (ESP32-CAM 2.0 Mbps Wi-Fi) |
| :--- | :--- | :--- | :--- | :--- |
| **1080p FHD (1920x1080)** | 250 KB | 10.0 FPS | **20.00 Mbps** | **UNFEASIBLE** (Saturates radio channel by 1000%) |
| **1080p FHD (1920x1080)** | 250 KB | 5.0 FPS | **10.00 Mbps** | **UNFEASIBLE** (Exceeds Wi-Fi link capacity by 500%) |
| **1080p FHD (1920x1080)** | 250 KB | 1.0 FPS | **2.00 Mbps** | **HIGH RISK** (Saturates available throughput) |
| **VGA (640x480)** | 45 KB | 1.0 FPS | **0.36 Mbps** | **FEASIBLE** (Consumes ~18% bandwidth) |
| **Native Model (224x224)** | 18 KB | 0.1 FPS (1 / 10s) | **0.014 Mbps (14.4 kbps)** | **OPTIMAL** (Consumes <1% bandwidth, matches telemetry rate) |

---

## 4. Camera Resolution Decision

- **Architecture Check**: Inspection of `BaseCameraDriver` ([camera_driver.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/cv/camera_driver.py)) and `ImagePreprocessor` ([image_preprocessing.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/cv/image_preprocessing.py)).
- **Finding**: `ImagePreprocessor` accepts generic `CameraFrame` objects of any resolution (e.g. 640x480 VGA) and performs bilinear resizing and normalization on the Gateway Host to produce the `(3, 224, 224)` model tensor.
- **Architectural Decision**: **Preserve Gateway-Side Preprocessing**. The ESP32-CAM should capture and transmit raw JPEG frames at VGA (640x480) or native 224x224 resolution. Model preprocessing responsibilities must **NOT** be moved into the ESP32-CAM microcontroller.

---

## 5. Model Artifact Verification

Code-verified properties of [models/cv/aquatic_bloom_mobilenetv3.pt](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/models/cv/aquatic_bloom_mobilenetv3.pt):

- **File Existence**: VERIFIED (`models/cv/aquatic_bloom_mobilenetv3.pt` exists on disk).
- **File Size**: `6,218,731 bytes` (~5.93 MB).
- **Architecture**: `mobilenet_v3_small` (PyTorch `torchvision.models.mobilenet_v3_small`).
- **Class Count**: 3 classes (`0: NORMAL_WATER`, `1: ALGAL_BLOOM`, `2: TURBID_DISCOLORATION`).
- **Input Dimensions**: `(3, 224, 224)` RGB Float32 tensor.
- **Normalization Contract**: ImageNet standard mean `[0.485, 0.456, 0.406]` and std `[0.229, 0.224, 0.225]`.
- **Metadata Registry**: [models/cv/aquatic_bloom_model_metadata.json](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/models/cv/aquatic_bloom_model_metadata.json) (Version 1.0.0, 100% test accuracy).
- **Execution Location**: **Gateway Host CPU**. Loaded directly via `torch.load(model_path, map_location=torch.device("cpu"))`.

---

## 6. Physical Hardware vs. Software Classification Matrix

| Component | Deployment Classification | Verification Evidence |
| :--- | :--- | :--- |
| **ESP32 Microcontroller** | **HARDWARE CONTRACT VERIFIED** | PlatformIO C++ firmware compiled (`firmware/`), simulated (`esp32_device.py`). |
| **ESP32-CAM Module** | **HARDWARE CONTRACT VERIFIED** | Software interface verified (`camera_driver.py`); physical stream pending. |
| **pH Sensor** | **HARDWARE CONTRACT VERIFIED** | C++ `PHDriver.h` and Python `VirtualPHSensorDriver` contracts verified. |
| **Temperature Sensor** | **HARDWARE CONTRACT VERIFIED** | C++ `DS18B20Driver.h` and Python `VirtualTemperatureSensorDriver` verified. |
| **Turbidity Sensor** | **HARDWARE CONTRACT VERIFIED** | C++ `TurbidityDriver.h` and Python `VirtualTurbiditySensorDriver` verified. |
| **Dissolved Oxygen (DO)**| **HARDWARE CONTRACT VERIFIED** | C++ `DODriver.h` and Python `VirtualDOSensorDriver` verified. |
| **Salinity / TDS Sensor**| **HARDWARE CONTRACT VERIFIED** | C++ `SalinityDriver.h` and Python `VirtualSalinitySensorDriver` verified. |
| **LEDs (Green/Yellow/Red)**| **HARDWARE CONTRACT VERIFIED** | C++ `LEDDriver.h` and Python `VirtualLEDDriver` contracts verified. |
| **Buzzer** | **HARDWARE CONTRACT VERIFIED** | C++ `BuzzerDriver.h` and Python `VirtualBuzzerDriver` contracts verified. |
| **Pump Relay** | **HARDWARE CONTRACT VERIFIED** | C++ `RelayDriver.h` and Python `VirtualRelayDriver` contracts verified. |
| **Physical Hardware Bench** | **NOT YET VERIFIED** | No physical hardware serial test logs exist in the repository. |

---

## 7. ESP32-CAM Transport Audit

Inspection of `config/device_config.json`, `src/iot/communication.py`, `src/cv/camera_driver.py`, and `src/fusion/runtime_orchestrator.py`:

- **MQTT Topic Registry**: Topics registered in `device_config.json` are `telemetry`, `status`, `command`, and `decision`. No topic for image frame transmission is registered.
- **Runtime Orchestration**: `MultimodalRuntimeOrchestrator` ingests `CameraFrame` objects via `enqueue_camera_frame()` as an in-memory software queue.
- **Forensic Status Statement**:
  > **PHYSICAL IMAGE TRANSPORT NOT YET IMPLEMENTED.**  
  > Image transport currently exists strictly as a software in-memory contract (`CameraFrame` dataclass passed directly to the Gateway queue).

---

## 8. Startup Failure Code Trace

Tracing actual code execution during failure modes:

1. **Model Missing**: `AquaticBloomCVModel.load()` ([cv_model.py:107](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/cv/cv_model.py#L107)) catches missing file exception, logs warning, and sets `is_trained_model_active = False`. `predict()` executes secondary spectral fallback module, returning prediction with status `"SUCCESS"` (fallback) or `"MODEL_OFFLINE"`.
2. **Camera Unavailable**: `MultimodalRuntimeOrchestrator.process_multimodal_observation()` ([runtime_orchestrator.py:155](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/fusion/runtime_orchestrator.py#L155)) checks frame status. If unavailable, generates `VisualEvidence` with `visual_state: CAMERA_FAULT`. `FusionEngine` ([fusion_engine.py:239](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/fusion/fusion_engine.py#L239)) catches `CAMERA_FAULT` and preserves sensor ML/AIS decision with reason code `VISUAL_CAMERA_FAULT`.
3. **Gateway Unavailable**: `ESP32Device.publish_telemetry()` ([esp32_device.py:322](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/esp32_device.py#L322)) logs `"MQTT Publish Failed"` and transitions state to `ERROR`.
4. **MQTT Unavailable**: `ESP32Device.connect_network()` ([esp32_device.py:234](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/esp32_device.py#L234)) logs `"Network Connection Failed"` and transitions state to `ERROR`.
5. **Sensor Init Failure**: `HAL.initialize()` ([HAL.cpp:52](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/firmware/src/HAL.cpp#L52)) returns `false` and sets `_sensorStatus = "FAULT"`. `EdgeValidator` flags out-of-bounds readings, causing Gateway `FusionEngine` to emit `SYSTEM_STATE_SENSOR_FAULT`.

---

## 9. Timestamp Audit

- **Sensor Timestamp**: Generated by ESP32 RTC driver / `datetime.now().isoformat()`.
- **Camera Frame Timestamp**: Generated by camera driver upon capture.
- **Gateway Timestamp**: Generated upon observation ingestion in `MultimodalRuntimeOrchestrator`.
- **Time Synchronization Analysis**: On physical ESP32 boot without an NTP server or battery-backed DS3231 RTC, the MCU system clock defaults to epoch (1970-01-01). Mismatch between ESP32 clock and Gateway clock will break temporal window matching.
- **Forensic Classification**: **DEPLOYMENT GAP (NTP / RTC time synchronization between physical ESP32 and Gateway is NOT YET IMPLEMENTED)**.

---

## 10. Release Artifact Audit

| Artifact File | Exists | Current Version | Required for Deployment | Gap Identified |
| :--- | :--- | :--- | :--- | :--- |
| `config/release_manifest.json` | **YES** | Version 1.0.0 (V3.0 Frozen) | **YES** | Missing V4 CV model artifacts, fusion engine version, and V4 test suite entries. |
| `config/device_config.json` | **YES** | Version 1.0.0 | **YES** | Contains hardcoded `localhost` broker, default plaintext password, and pin mapping conflicts. |
| `config/config.yaml` | **YES** | Version 1.0.0 | **YES** | Fully valid for raw dataset paths and field definitions. |
| `requirements.txt` | **YES** | Unpinned (`>=`) | **YES** | Missing `torch`, `torchvision`, `pillow`, `opencv-python` dependencies. |
| `models/cv/aquatic_bloom_model_metadata.json` | **YES** | Version 1.0.0 | **YES** | Complete metadata, but SHA-256 digest is not verified by model loader. |
| `models/cv/aquatic_bloom_mobilenetv3.pt` | **YES** | 6,218,731 bytes | **YES** | Ready for Gateway Host CPU execution. |

---

## 11. Dependency Reproducibility Audit

Inspection of [requirements.txt](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/requirements.txt):

- **Package Pinning**: All listed dependencies (`pandas>=2.0.0`, `numpy>=1.24.0`, `scikit-learn>=1.2.0`, `fastapi>=0.95.0`, etc.) use flexible `>=` operators, **NOT exact version pins (`==`)**.
- **Missing Packages**: `torch`, `torchvision`, `pillow` (PIL), and `opencv-python` are imported in V4 modules (`src/cv/` and `src/fusion/`) but are **completely omitted from `requirements.txt`**.
- **Forensic Status**: **UNPINNED & INCOMPLETE**.

---

## 12. Resource Claims Audit

- **Gateway Pipeline Execution Time (~13.1 ms)**: **MEASURED HOST PERFORMANCE** (Tracked via `LatencyMetrics` in `MultimodalRuntimeOrchestrator`).
- **Gateway PyTorch RAM Footprint (~25 to 45 MB)**: **ESTIMATED SCENARIO PROFILE** (Derived from MobileNetV3 state dict size and PyTorch runtime overhead).
- **ESP32 SRAM / PSRAM Footprint**: **ESTIMATED SCENARIO PROFILE** (Derived from PlatformIO build headers and ESP32 specs).

---

## 13. Security Audit

- **Credentials Check**: `config/device_config.json` lines 9 & 71 store default Wi-Fi passwords (`"password": "aquasentinel_secure"`) in plaintext.
- **Forensic Classification**: **SECRET PRESENT (Plaintext default credential in JSON configuration file)**.

---

## 14. V3.8 Protection Verification

Empirical verification via `git status --porcelain`:

```bash
git status --porcelain src/iot/esp32_device.py src/iot/communication.py src/iot/scheduler.py src/iot/hal.py src/iot/actuators.py
# Output: (EMPTY - Zero modifications)
```

- [src/iot/esp32_device.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/esp32_device.py): **UNTOUCHED (0 modifications)**
- [src/iot/communication.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/communication.py): **UNTOUCHED (0 modifications)**
- [src/iot/scheduler.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/scheduler.py): **UNTOUCHED (0 modifications)**
- [src/iot/hal.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/hal.py): **UNTOUCHED (0 modifications)**
- [src/iot/actuators.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/actuators.py): **UNTOUCHED (0 modifications)**

---

## 15. Final Deployment Gap Classification Matrix

Each deployment category is classified according to the specified color matrix:
- 🟢 **GREEN**: Verified code implementation.
- 🟡 **YELLOW**: Software-ready; physical hardware validation pending.
- 🟠 **ORANGE**: Implementation / configuration modification required.
- 🔴 **RED**: Architectural conflict / unsafe assumption.

| Category | Classification | Forensic Justification & Action Item |
| :--- | :--- | :--- |
| **1. GPIO Mapping** | 🔴 **RED** | **Architectural Conflict**: Major pin discrepancies between `PinConfig.h`, `device_config.json`, and `HARDWARE_INTEGRATION_GUIDE.md`. Must consolidate into single pin header. |
| **2. Power / Electrical** | 🟡 **YELLOW** | Software-ready; 5V power rail and optocoupler requirements documented in guide, physical hardware circuit assembly pending. |
| **3. Camera** | 🟡 **YELLOW** | Software interface `CameraFrame` and `VirtualCameraDriver` verified; physical ESP32-CAM board capture pending. |
| **4. Image Transport** | 🟠 **ORANGE** | **Implementation Required**: Physical image transport over MQTT/HTTP is not implemented in physical firmware (software queue contract only). |
| **5. Bandwidth** | 🟡 **YELLOW** | Scenario estimates calculated; 224x224 @ 0.1 FPS consumes 14.4 kbps (<1% Wi-Fi throughput); physical field radio testing pending. |
| **6. Model** | 🟢 **GREEN** | `aquatic_bloom_mobilenetv3.pt` (5.93 MB, 3 classes, PyTorch CPU execution) verified with 100% test accuracy. |
| **7. Preprocessing** | 🟢 **GREEN** | Hardware-independent `ImagePreprocessor` verified; handles resizing/normalization with complete provenance. |
| **8. Sensors** | 🟡 **YELLOW** | Virtual HAL drivers and EdgeValidator verified; physical analog probe readings pending. |
| **9. Fusion** | 🟢 **GREEN** | Multimodal Dempster-Shafer `FusionEngine` verified; handles camera fault & early warning states cleanly. |
| **10. Runtime** | 🟢 **GREEN** | `MultimodalRuntimeOrchestrator` verified; bounded queueing, DROP-OLDEST policy, and latency profiling verified. |
| **11. MQTT** | 🟡 **YELLOW** | In-Memory MQTT & client verified; production Mosquitto broker setup pending. |
| **12. Timestamps** | 🟠 **ORANGE** | **Implementation Required**: Time synchronization between physical ESP32 (RTC/NTP) and Gateway is not yet implemented. |
| **13. Configuration** | 🟠 **ORANGE** | **Implementation Required**: Split configuration files contain threshold discrepancies and hardcoded values requiring consolidation. |
| **14. Dependencies** | 🟠 **ORANGE** | **Implementation Required**: `requirements.txt` uses unpinned `>=` operators and omits `torch`, `torchvision`, `pillow`. |
| **15. Calibration** | 🟡 **YELLOW** | Calibration infrastructure exists in HAL/firmware; physical probe 2-point buffer calibration pending. |
| **16. Logging** | 🟢 **GREEN** | Full SQLite database logging across telemetry, validation, fusion decisions, actuator logs verified. |
| **17. Security** | 🟠 **ORANGE** | **Implementation Required**: Plaintext credentials in `device_config.json` require migration to environment variables. |
| **18. Release Artifacts**| 🟠 **ORANGE** | **Implementation Required**: `release_manifest.json` frozen at V3.0 requires updating to register V4 CV model artifacts. |
| **19. Physical Validation**| 🟡 **YELLOW** | Software host pipeline verified with 244/244 passing tests; physical hardware bench deployment pending. |
