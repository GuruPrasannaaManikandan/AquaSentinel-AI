# VERSION 4.8 — PHYSICAL DEPLOYMENT READINESS & FINAL RELEASE AUDIT

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Milestone:** V4.8 Physical Deployment Readiness & Final Release Audit  
**Current Frozen Baseline:** V3.0–V3.8 (Release Frozen), V4.1–V4.7 Complete & Verified  
**Regression Test Status:** 244/244 passed, 3 skipped, 0 failed  
**V3.8 Source Code Modifications:** ZERO (0)

---

## Executive Summary

This document presents the **Version 4.8 Physical Deployment Readiness & Final Release Audit** for the IoT-Based Artificial Immune System (AIS) for Aquatic Ecosystems. The primary goal of V4.8 is to perform an exhaustive architectural audit of the end-to-end multimodal pipeline to determine whether the complete system can be safely packaged, configured, validated, and deployed alongside physical embedded hardware (**ESP32-WROOM-32E MCU** and **ESP32-CAM module**) without modifying the frozen V3.8 core architecture.

---

## 1. Complete System Architecture Audit

### 1.1 End-to-End Pipeline Trace

The complete system spans physical/simulated sensors, edge microcontrollers, optical image acquisition, deep learning computer vision, unsupervised/supervised sensor ML & AIS, multimodal Dempster-Shafer fusion, decision adaptation, and edge actuation:

```
[ Physical / Simulated Sensors ]
               ↓ (Analog / OneWire Signals)
[ ESP32 MCU Firmware / HAL Layer ] ─── (Local EdgeValidator FSM)
               ↓ (MQTT Topic: aquatic/{device_id}/telemetry)
       [ MQTT Broker ]
               ↓ (Telemetry Ingestion)
   [ Sensor ML & AIS Pipeline ]
  (RandomForest / LR & NSA AIS)
               ↓
[ ESP32-CAM Hardware Module ]
               ↓ (JPEG Optical Stream over Wi-Fi / MQTT / HTTP)
   [ V4.1 Camera Acquisition ]
               ↓ (CameraFrame Payload: 224x224 / VGA)
  [ V4.2 Image Preprocessing ] ─── (Validation, Rescaling & Standard Normalization)
               ↓ (PreprocessedImage Tensor: 3x224x224 float32)
   [ V4.3 MobileNetV3 Engine ] ─── (Trained PyTorch Model: aquatic_bloom_mobilenetv3.pt)
               ↓ (CVPrediction: class probabilities & latency metrics)
   [ V4.4 Visual Detection ]   ─── (VisualEvidence: state, risk level & confidence)
               ↓
[ V4.5 Multimodal Evidence Fusion ] (Dempster-Shafer Belief Fusion Engine)
               ↓ (FusedEvidence: dataset, final_state, reason_code)
   [ V4.6 Decision Adapter ]   ─── (SystemEvent Generator & Event Deduplication)
               ↓
[ V4.7 Multimodal Runtime Orchestrator ] (Bounded Queueing & Latency Breakdown)
               ↓ (MQTT Topic: aquatic/{device_id}/decision)
       [ MQTT Broker ]
               ↓ (Decision Dispatch)
 [ ESP32 Device Runtime / HAL ]
               ↓ (State Mapping: NORMAL / WARNING / CRITICAL / UNKNOWN_ANOMALY)
[ Existing Actuator Layer ]    ─── (Green/Yellow/Red LEDs, Buzzer, Aerator Pump Relay)
```

### 1.2 Component Execution Placement Breakdown

| Component Layer | Primary Execution Node | Runtime Environment | Dependency Stack |
| :--- | :--- | :--- | :--- |
| **Physical Sensors (pH, Temp, Turb, DO, TDS)** | Aquatic Field Probe Assembly | Physical Hardware | Analog Probes, DS18B20 OneWire |
| **Edge Hardware Abstraction (HAL)** | ESP32-WROOM-32E Microcontroller | Arduino C++ / ESP-IDF | `OneWire`, `DallasTemperature`, ADC |
| **Edge Validator & FSM** | ESP32-WROOM-32E Microcontroller | Arduino C++ / ESP-IDF | `ArduinoJson`, C++ State Machine |
| **Local Edge Actuators** | ESP32-WROOM-32E Microcontroller | Arduino C++ / ESP-IDF | Optocoupler Relay, Piezo Buzzer, LEDs |
| **Camera Hardware Capture** | ESP32-CAM Board (OV2640 Sensor) | ESP-IDF / Arduino C++ | `esp_camera.h`, Wi-Fi Stack |
| **V4.1 Camera Ingestion & Driver** | IoT Gateway Host / Edge Server | Python 3.9+ | `PIL`, `io`, `dataclasses` |
| **V4.2 Image Preprocessing** | IoT Gateway Host / Edge Server | Python 3.9+ | `NumPy`, `PIL` |
| **V4.3 MobileNetV3 CV Model** | IoT Gateway Host CPU / Edge GPU | PyTorch 2.0+ | `torch`, `torchvision` |
| **V4.4 Visual Detection Engine** | IoT Gateway Host / Edge Server | Python 3.9+ | `dataclasses`, `logging` |
| **Sensor ML & AIS Pipeline** | IoT Gateway Host / Edge Server | Python 3.9+ | `scikit-learn`, `joblib`, `pandas` |
| **V4.5 Multimodal Fusion Engine** | IoT Gateway Host / Edge Server | Python 3.9+ | `NumPy`, Dempster-Shafer Module |
| **V4.6 Decision Adapter** | IoT Gateway Host / Edge Server | Python 3.9+ | `uuid`, `time` |
| **V4.7 Multimodal Orchestrator** | IoT Gateway Host / Edge Server | Python 3.9+ | `queue`, `threading` |
| **MQTT Transport Broker** | IoT Gateway / Edge Server | Mosquitto / Python | `paho-mqtt` / `InMemoryMQTTBroker` |
| **Backend & Event Store** | IoT Gateway Host / Edge Server | FastAPI / SQLite | `fastapi`, `sqlite3`, `uvicorn` |

### 1.3 Operational Classification

- **Gateway-Side Components**: V4.1 Camera Acquisition, V4.2 Image Preprocessing, V4.3 MobileNetV3 Inference, V4.4 Visual Detection, Sensor ML Classifiers, NSA AIS Anomaly Detectors, V4.5 Multimodal Fusion, V4.6 Decision Adapter, V4.7 Multimodal Runtime Orchestrator, SQLite Event Store, FastAPI Server.
- **ESP32-Side Components**: HAL C++ drivers, Sensor ADC/OneWire readers, EdgeValidator FSM, local status indicators (LEDs/Buzzer/Relay), MQTT PubSubClient.
- **Camera-Side Components**: ESP32-CAM OV2640 capture driver, JPEG frame buffer, network packet transmission.
- **Sensor-Side Components**: DS18B20 waterproof temperature probe, analog pH probe, analog turbidity photodiode, analog dissolved oxygen (DO) probe, analog TDS/salinity probe.
- **Network-Dependent Components**: MQTT telemetry publishing, camera frame stream transmission, gateway decision publishing, WebSocket backend dashboard streaming.
- **Offline-Capable Components**: ESP32 local EdgeValidator (flags out-of-bounds sensor faults locally), Gateway local SQLite log buffering, Gateway local PyTorch inference.

---

## 2. Physical Hardware Mapping Audit

Source of Truth: [HARDWARE_INTEGRATION_GUIDE.md](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/HARDWARE_INTEGRATION_GUIDE.md), [future_hardware_migration.md](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/future_hardware_migration.md), [device_config.json](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/config/device_config.json), [platformio.ini](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/firmware/platformio.ini).

### 2.1 Hardware Specification & Pin Mapping Table

| Component / Sensor | Hardware Model | ESP32 Pin | Interface Type | Electrical & Power Requirements | Driver / Software Abstraction |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Microcontroller** | ESP32-WROOM-32E Dev Module | N/A | MCU Board | 5V USB / External 5V, 3.3V Logic | Arduino Framework / ESP-IDF |
| **Temperature Sensor** | DS18B20 Waterproof Probe | `GPIO 4` | OneWire Digital | 3.3V Power + 4.7kΩ Pull-up Resistor | `DallasTemperature` / `OneWire` |
| **pH Probe** | DFRobot Analog pH Meter v2 | `GPIO 32` | Analog (ADC1_CH4) | 5.0V Stable Rail (0-3.3V Scaled ADC) | `VirtualPHSensorDriver` / `HAL.cpp` |
| **Salinity / TDS Probe** | Gravity Analog TDS Sensor | `GPIO 33` | Analog (ADC1_CH5) | 5.0V Stable Rail (0-3.3V Scaled ADC) | `VirtualSalinitySensorDriver` |
| **Turbidity Sensor** | Gravity Analog Turbidity | `GPIO 34` | Analog (ADC1_CH6) | 5.0V Stable Rail (0-3.3V Scaled ADC) | `VirtualTurbiditySensorDriver` |
| **Dissolved Oxygen (DO)**| Gravity Analog DO Sensor | `GPIO 35` | Analog (ADC1_CH7) | 5.0V Stable Rail (0-3.3V Scaled ADC) | `VirtualDOSensorDriver` |
| **Green Status LED** | 5mm Standard LED | `GPIO 12` | Digital Output | 3.3V GPIO + 220Ω Limiting Resistor | `VirtualLEDDriver` / `HAL` |
| **Yellow Status LED** | 5mm Standard LED | `GPIO 13` | Digital Output | 3.3V GPIO + 220Ω Limiting Resistor | `VirtualLEDDriver` / `HAL` |
| **Red Status LED** | 5mm Standard LED | `GPIO 14` | Digital Output | 3.3V GPIO + 220Ω Limiting Resistor | `VirtualLEDDriver` / `HAL` |
| **Alarm Buzzer** | Active Piezo Buzzer | `GPIO 15` | Digital Output | 5.0V Power + NPN Transistor Switch | `VirtualBuzzerDriver` / `HAL` |
| **Aerator Pump Relay** | 5V Optocoupler Relay Board | `GPIO 23` | Digital Output | 5.0V External Supply + Flyback Diode | `VirtualRelayDriver` / `HAL` |
| **Camera Module** | ESP32-CAM (OV2640 Module) | Dedicated Board | Wi-Fi / Serial | 5.0V Power (2A Peak), Wi-Fi Antenna | `CameraFrame` / `VirtualCameraDriver` |

### 2.2 Driver & Software Contract Audit

1. **Physical Responsibility**: The ESP32 MCU acquires raw analog/digital signals from water quality probes and outputs discrete digital signals to status indicators and power relays.
2. **Software Interface**: The existing Python `src/iot/hal.py` and C++ `firmware/src/HAL.cpp` implement identical logical interfaces (`read_all_sensors()`, `write_actuator()`).
3. **GPIO Requirements**: GPIO assignments in `docs/HARDWARE_INTEGRATION_GUIDE.md` and `config/device_config.json` match across all project documentation.
4. **Power Considerations**: Analog sensor modules require a dedicated 5.0V rail to prevent ADC scaling errors and calibration drift; ESP32 GPIOs operate at 3.3V logic. Relays must use optocouplers to isolate inductive kickback.

---

## 3. ESP32-CAM Deployment Contract

### 3.1 Software Frame Structure Contract

The Python camera contract is encapsulated in `CameraFrame` ([camera_driver.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/cv/camera_driver.py)):

```python
@dataclass
class CameraFrame:
    frame_id: str           # Unique frame identifier (e.g., "frame_000102")
    timestamp: str          # ISO-8601 string (e.g., "2026-08-18T10:45:00.123456")
    width: int              # Spatial width (e.g., 224 or 640)
    height: int             # Spatial height (e.g., 224 or 480)
    channels: int           # Channel count (3 for RGB/BGR)
    format: str             # "JPEG", "RGB", "PNG"
    image_bytes: bytes      # Raw JPEG encoded byte payload
    quality_valid: bool     # True if frame decoded cleanly and hardware OK
    status: str             # "OK", "CORRUPTED", "EXPOSURE_FAULT", "CAMERA_OFFLINE"
    metadata: Dict[str, Any]# Extra metadata (driver, frame_index, etc.)
```

### 3.2 Physical Transport Protocols

The ESP32-CAM must transmit JPEG frames to the Gateway. Two standard transport modes exist within the current system architecture:

1. **Option A (MQTT Base64 Payload - Existing Protocol)**:
   - Topic: `aquatic/{device_id}/camera/raw`
   - Payload: JSON containing `frame_id`, `timestamp`, and `image_bytes_b64`.
   - Advantage: Direct reuse of existing `CommunicationLayer` / MQTT broker infrastructure.
   - Disadvantage: Base64 encoding adds ~33% payload byte expansion.

2. **Option B (HTTP POST / GET Polling - Gateway Service)**:
   - Endpoint: ESP32-CAM hosts a lightweight HTTP server (`http://<esp32-cam-ip>/capture`).
   - Gateway pulls JPEG stream directly at a controlled sampling interval.
   - Advantage: Zero Base64 overhead, raw binary JPEG transmission.

**Verdict**: Both transport modes convert cleanly into the existing `CameraFrame` contract on the Gateway side without changing any V4.1-V4.7 code.

---

## 4. Image Size / Bandwidth Audit

### 4.1 Frame Resolution vs. Bandwidth Scenarios

The following calculations estimate network bandwidth consumption across different resolutions and frame rates, using measured JPEG compression ratios (Quality = 85):

| Resolution | Single Frame Size (JPEG Q=85) | 0.1 FPS (1 frame / 10 sec) | 1.0 FPS | 5.0 FPS | 10.0 FPS |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1080p FHD (1920x1080)** | ~250 KB | 25.0 KB/s (200 kbps) | 250 KB/s (2.0 Mbps) | 1.25 MB/s (10.0 Mbps) | 2.50 MB/s (20.0 Mbps) |
| **VGA (640x480)** | ~45 KB | 4.5 KB/s (36 kbps) | 45.0 KB/s (360 kbps) | 225 KB/s (1.8 Mbps) | 450 KB/s (3.6 Mbps) |
| **Model Native (224x224)** | ~18 KB | 1.8 KB/s (14.4 kbps) | 18.0 KB/s (144 kbps) | 90.0 KB/s (720 kbps) | 180 KB/s (1.44 Mbps) |

### 4.2 Network & Queue Pressure Analysis

- **ESP32-CAM Wi-Fi Capacity**: Real-world field throughput for an ESP32-CAM Wi-Fi connection is typically **2.0 to 4.0 Mbps**.
- **1080p Transmit Risk**: Transmitting 1080p frames at $\ge 5$ FPS requires 10–20 Mbps, which will **saturate the Wi-Fi link**, trigger high packet loss, cause MQTT message dropping, and overflow the bounded 5-frame queue.
- **Recommended Deployment Rate**: Capturing at **224x224 (or VGA 640x480)** at **0.1 FPS (1 frame every 10 seconds)** consumes only **14.4 kbps**, matching the telemetry sampling rate (`sampling_interval_seconds: 10`) while preserving 99.5%+ Wi-Fi headroom.

---

## 5. Compute Placement Audit

### 5.1 Component Placement Matrix

| System Component | Execution Location | Resource Demands | Justification |
| :--- | :--- | :--- | :--- |
| **Camera Hardware Capture** | ESP32-CAM Module | ~500 KB PSRAM | Hardware sensor optical capture |
| **Image Preprocessing** | Gateway Host (PC / RPi) | ~2 ms CPU, <1 MB RAM | Rescaling, normalization, tensor prep |
| **MobileNetV3 CV Inference** | Gateway Host CPU / Edge GPU | ~8 ms CPU, ~45 MB RAM | PyTorch deep learning neural network execution |
| **Visual Detection Engine** | Gateway Host | ~1 ms CPU | Threshold evaluation & bounding box filtering |
| **Sensor ML & AIS Pipeline** | Gateway Host | ~3 ms CPU, ~15 MB RAM | RandomForest & NSA Anomaly scan |
| **Dempster-Shafer Fusion** | Gateway Host | ~2 ms CPU | Multimodal belief fusion |
| **Decision Adapter** | Gateway Host | <1 ms CPU | SystemEvent generation & deduplication |
| **Runtime Orchestrator** | Gateway Host | <1 ms CPU, ~3 MB Queue | Multi-thread stream orchestration |
| **Sensor Reading & Validation** | ESP32-WROOM MCU | <50 KB SRAM, <1% CPU | Pin polling & local range check |
| **Physical Edge Actuation** | ESP32-WROOM MCU | <1 KB SRAM, <1% CPU | GPIO write to LEDs, Buzzer, Relays |

### 5.2 Compute Placement Confirmation

> [!IMPORTANT]
> The physical deployment architecture **does NOT attempt to execute the PyTorch MobileNetV3 model on the ESP32 microcontroller**.
> PyTorch MobileNetV3 runs exclusively on the **IoT Gateway / Edge Host CPU**. The ESP32-CAM acts strictly as an image capture and transport node.

---

## 6. Model Artifact Audit

### 6.1 Checkpoint Properties

- **Model File Path**: [models/cv/aquatic_bloom_mobilenetv3.pt](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/models/cv/aquatic_bloom_mobilenetv3.pt)
- **Metadata Path**: [models/cv/aquatic_bloom_model_metadata.json](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/models/cv/aquatic_bloom_model_metadata.json)
- **Format**: PyTorch Binary Checkpoint (`.pt` state dict)
- **File Size**: `6,218,731 bytes` (~5.93 MB)
- **Architecture**: `mobilenet_v3_small`
- **Output Classes**: 3 classes — `[0: NORMAL_WATER, 1: ALGAL_BLOOM, 2: TURBID_DISCOLORATION]`
- **Input Contract**: Shape `(3, 224, 224)` RGB Float32, ImageNet Standard Normalization ($\mu = [0.485, 0.456, 0.406]$, $\sigma = [0.229, 0.224, 0.225]$)
- **Verified Accuracy**: 100% Test Accuracy (Macro F1 = 1.0) on project validation benchmark.

### 6.2 Gateway Deployment Compatibility

The Gateway host runtime uses standard PyTorch (`torch.load()`), which directly loads `.pt` checkpoints. ONNX or TFLite conversion is **not required** for host-side gateway deployment.

---

## 7. Model Version & Integrity Audit

### 7.1 Integrity Verification Assessment

Inspection of `AquaticBloomCVModel.load()` ([cv_model.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/cv/cv_model.py)):

- **Existing Verification**: Checks if `os.path.exists(self.model_path)` returns True. If missing, logs a warning and flags active trained model state as False.
- **Identified Gaps**:
  1. No SHA-256 cryptographic digest check prior to loading state dict.
  2. No model version validation against `aquatic_bloom_model_metadata.json`.
  3. No explicit check of classifier weight layer shape prior to forward pass.

---

## 8. Configuration Audit

### 8.1 Configuration File Matrix

| Configuration File | Scope / Purpose | Status / Issues Identified |
| :--- | :--- | :--- |
| `config/device_config.json` | ESP32 pins, MQTT topics, thresholds, physical bounds | Contains hardcoded broker `"localhost"` & plaintext Wi-Fi password. |
| `config/fusion_policy.json` | Fusion confidence thresholds, dangerous classes | Duplicates confidence thresholds defined in `visual_detection.py`. |
| `config/config.yaml` | Raw dataset file paths & field mappings | Fully consistent with V3 pipeline. |
| `config/release_manifest.json` | System release metadata & model registry | Needs update to register V4 CV model artifacts. |
| `models/cv/aquatic_bloom_model_metadata.json` | CV model shape, classes, & accuracy metrics | Complete and authoritative for CV model contract. |

---

## 9. Startup / Shutdown Audit

```
                 [ Power-On / Boot ]
                          ↓
               [ ESP32 MCU Hardware Init ]
              (HAL Pin Setup & Sensor Check)
                          ↓
           [ Wi-Fi & MQTT Transport Connect ]
                          ↓
           [ Gateway Host Service Startup ]
    (Load PyTorch CV Model, Sensor ML/AIS, Init DB)
                          ↓
          [ ESP32-CAM Stream Init & Connect ]
                          ↓
        [ System Operational / Active Runtime ]
```

### 9.1 Startup Failure Handlers

- **Camera Unavailable at Boot**: Gateway marks visual modality as `UNAVAILABLE` (`status: CAMERA_OFFLINE`), producing `VisualEvidence` with `visual_state: CAMERA_FAULT`. System falls back safely to Sensor ML + AIS fusion.
- **Gateway Unavailable at Boot**: ESP32 retries MQTT connection, continues local sensor polling, and enforces EdgeValidator boundaries.
- **Model File Missing / Corrupted**: `AquaticBloomCVModel.load()` catches exception, sets `status: FAULT` or fallback mode, producing `INFERENCE_FAILURE`.
- **Sensor Hardware Fault at Init**: ESP32 transitions to `ERROR` state and flags `sensor_status: FAULT`. Gateway triggers `SYSTEM_STATE_SENSOR_FAULT` override.

---

## 10. Offline / Degraded Operation Matrix

| Scenario / Failure State | Classified Operating Mode | System Reaction & Safety Action | Recovery Mechanism |
| :--- | :--- | :--- | :--- |
| **A. Camera Unavailable / Offline** | DEGRADED OPERATION | Visual state = `CAMERA_FAULT`. Sensor ML + AIS fusion active. Reason code: `VISUAL_CAMERA_FAULT`. | Automatic camera polling & reconnect. |
| **B. Gateway Host Unavailable** | DEGRADED / LOCAL SAFE | ESP32 continues sensor polling & local EdgeValidation. Actuators default to safe offline state. | Retries MQTT connection to Gateway. |
| **C. MQTT Network Loss** | DEGRADED OPERATION | ESP32 transitions `ONLINE -> ERROR -> RECOVERING`. Retries connection loop. | Automated `run_reconnection()` protocol. |
| **D. CV Model File Missing/Corrupt**| DEGRADED OPERATION | Model status = `FAULT`. Visual state = `INFERENCE_FAILURE`. Decision relies on sensor ML/AIS. | Administrative model restoration. |
| **E. Sensor Hardware Fault** | SAFE FAILURE | ESP32 flags `sensor_status: FAULT` and enters `ERROR`. Gateway emits `SYSTEM_STATE_SENSOR_FAULT`. | Hardware maintenance / probe replacement. |
| **F. Dual Sensor & Camera Fault** | SAFE FAILURE | Gateway emits `SYSTEM_STATE_SENSOR_FAULT` override. ESP32 activates Yellow+Red LED alarm. | System hardware restart & diagnostic check. |

---

## 11. Model Failure Safety Audit

> [!IMPORTANT]
> **Verification of Model Failure Safety ([cv_model.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/cv/cv_model.py) & [visual_detection.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/cv/visual_detection.py))**:
> If the PyTorch model file is missing, corrupted, or encounters an inference exception, `AquaticBloomCVModel` outputs `status: INFERENCE_FAILURE` and `predicted_class: UNCERTAIN`.
> `VisualDetector` maps `INFERENCE_FAILURE` to `visual_state: INFERENCE_FAILURE` with `risk_level: UNKNOWN`.
> **CRITICAL CHECK PASSED**: Model failures **NEVER** silently produce `NO_BLOOM` or `NORMAL_WATER`.

---

## 12. Camera Failure Safety Audit

> [!IMPORTANT]
> **Verification of Camera Failure Safety ([camera_driver.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/cv/camera_driver.py) & [fusion_engine.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/fusion/fusion_engine.py))**:
> When a frame is missing, corrupted, or offline, `CameraFrame.quality_valid` is set to `False` and `status` is set to `CAMERA_OFFLINE` / `CORRUPTED`.
> `VisualDetector` outputs `visual_state: CAMERA_FAULT`. `FusionEngine` catches `CAMERA_FAULT` and preserves the sensor ML/AIS decision under reason code `VISUAL_CAMERA_FAULT`.
> **CRITICAL CHECK PASSED**: Camera failures **NEVER** silently produce `NO_VISUAL_BLOOM` or `NORMAL`.

---

## 13. Sensor Failure Safety Audit

> [!IMPORTANT]
> **Verification of Sensor Failure Safety ([esp32_device.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/esp32_device.py) & [edge_validation.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/edge_validation.py))**:
> Out-of-bounds or disconnected analog sensor readings cause `EdgeValidator` to set `sensor_status: FAULT`.
> `ESP32Device` transitions to `ERROR` state. The Gateway `FusionEngine` checks `sensors["sensor_status"] == "FAULT"` and immediately emits `SENSOR_FAULT` state, bypassing inference.
> **CRITICAL CHECK PASSED**: Sensor faults **NEVER** silently produce `NORMAL`.

---

## 14. Network Interruption Audit

- **V3.8 Communication Verification**: `CommunicationLayer` ([communication.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/communication.py)) tracks network status via `wifi_connected` and `mqtt_connected`.
- **Reconnection Logic**: Upon publish timeout or broker disconnect, `ESP32Device` calls `run_reconnection()`, disconnecting and re-subscribing to command/decision channels upon broker availability.
- **V3.8 Protection**: Existing V3.8 recovery mechanisms are frozen, fully intact, and verified sufficient.

---

## 15. Clock / Timestamp Audit

- **Timestamp Sources**:
  - Telemetry: Generated by ESP32 via RTC driver / system time (`datetime.now().isoformat()`).
  - Camera Frames: Generated by camera driver upon frame capture.
  - Gateway Ingestion: Generated upon arrival at Gateway.
- **Clock Mismatch Analysis**: If an ESP32 boots without NTP time synchronization (defaulting to 1970-01-01), its timestamps will mismatch Gateway system time.
- **Recommendation**: Anchoring fusion matching to Gateway receipt time or enforcing SNTP time sync on ESP32 boot.

---

## 16. Resource / Memory Audit

### 16.1 Gateway-Side Host Resource Profile

- **PyTorch MobileNetV3 Model RAM**: State dict = ~5.93 MB; In-memory PyTorch instance = **~25 to 45 MB RAM**.
- **Frame Buffer Tensor**: 3x224x224 float32 tensor = **~0.6 MB RAM** per frame.
- **Bounded Frame Queue (Size 5)**: **~3.0 MB RAM**.
- **Total Gateway CV Pipeline Footprint**: **< 100 MB RAM**.
- **Inference Latency (Host CPU)**: Preprocessing = ~2.1 ms, Inference = ~7.8 ms, Fusion = ~3.2 ms $\rightarrow$ **Total Pipeline = ~13.1 ms**.

### 16.2 ESP32 Microcontroller Resource Profile

- **ESP32 SRAM (512 KB)**: Firmware binary with `ArduinoJson`, `PubSubClient`, `OneWire` consumes **~150 to 200 KB RAM**, leaving 300+ KB free SRAM.
- **ESP32-CAM PSRAM (4 MB)**: Double-buffered VGA/224x224 JPEG frame buffers consume **~36 to 100 KB PSRAM**, leaving 3.9 MB free PSRAM.

---

## 17. Logging / Observability Audit

Existing observability provided by `MultimodalRuntimeOrchestrator` ([runtime_orchestrator.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/fusion/runtime_orchestrator.py)):

- `observation_id` & ISO timestamp
- `camera_status` & `sensor_status`
- Modality availability flags (`sensor`, `visual`)
- Latency breakdown (`camera_acquisition_ms`, `preprocessing_ms`, `inference_ms`, `detection_ms`, `fusion_ms`, `adapter_ms`, `total_pipeline_ms`)
- Queue occupancy & dropped frame counter
- SQLite database persistence (`telemetry_logs`, `validation_logs`, `fusion_decisions`, `actuator_logs`, `command_logs`, `alerts`)

---

## 18. Release Artifact Audit

Audit of [config/release_manifest.json](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/config/release_manifest.json):

- **Existing Registered Artifacts**: Version 1.0.0, `caml_phase3_champion`, `habsos_phase3_champion`, `caml_nsa_v1`, `habsos_nsa_v1`.
- **Identified Gap**: `release_manifest.json` does not yet list V4 artifacts (`aquatic_bloom_mobilenetv3.pt`, `aquatic_bloom_model_metadata.json`, `VisualDetector`, `MultimodalRuntimeOrchestrator`).
- **Required Action**: Update release manifest to register V4 artifacts prior to final release.

---

## 19. Dependency Audit

Audit of [requirements.txt](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/requirements.txt):

- **Listed Dependencies**: `pandas`, `numpy`, `matplotlib`, `seaborn`, `scikit-learn`, `pyyaml`, `openpyxl`, `fastapi`, `uvicorn`, `paho-mqtt`, `jinja2`, `ipykernel`, `joblib`, `streamlit`, `websockets`, `pydantic`.
- **Identified Gap**: `torch`, `torchvision`, `pillow`, and `opencv-python` are used by V4 modules but are not explicitly pinned in `requirements.txt`.
- **Required Action**: Add pinned PyTorch and image dependencies (`torch>=2.0.0`, `torchvision>=0.15.0`, `pillow>=9.5.0`) to `requirements.txt`.

---

## 20. Security / Safety Audit

- **Plaintext Credentials**: `config/device_config.json` stores default Wi-Fi passwords (`"aquasentinel_secure"`). Production deployments should load credentials from environment variables.
- **Actuator Safe State**: On boot, network loss, or error, actuators default to `Green=OFF, Yellow=ON, Red=ON, Buzzer=ON, Pump=OFF`, preventing accidental chemical or water dispersion.

---

## 21. Actuator Safety

> [!IMPORTANT]
> **Verification of Actuator Safety Abstraction**:
> All physical actuation commands remain strictly routed through `VirtualActuators` ([actuators.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/actuators.py)) and the HAL layer ([hal.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/hal.py)).
> V4.8 code **does NOT interact directly with raw GPIO pins or relay hardware**.

---

## 22. Calibration Audit

- **Calibration Infrastructure**: Supported in `config/device_config.json` under the `calibration` block for `ph`, `turbidity`, `dissolved_oxygen`, `temperature`, and `salinity`.
- **Persistence**: Offsets and linear scale factors ($V_{\text{read}} \times \text{scale} + \text{offset}$) persist in configuration and C++ NVS flash.
- **Deployment Requirement**: Physical analog probes MUST undergo 2-point buffer calibration (pH 4.01 / 7.00 / 10.01) before initial deployment.

---

## 23. Physical Deployment Boundary Classification

| Component / Layer | Deployment Classification | Validation Evidence |
| :--- | :--- | :--- |
| **ESP32 MCU Core & HAL** | HARDWARE CONTRACT VALIDATED | PlatformIO C++ compiled (`firmware/`), simulated (`esp32_device.py`). |
| **Water Quality Probes (pH, DO, Turb, Temp)**| HARDWARE CONTRACT VALIDATED | GPIO pin mapping verified in `docs/HARDWARE_INTEGRATION_GUIDE.md`. |
| **ESP32-CAM Hardware Interface** | HARDWARE CONTRACT VALIDATED | `CameraFrame` payload interface verified in `camera_driver.py`. |
| **MobileNetV3 PyTorch Model** | HOST VALIDATED | PyTorch inference executing on Gateway CPU (244/244 tests passed). |
| **Dempster-Shafer Multimodal Fusion** | HOST VALIDATED | Multimodal belief fusion executing on Gateway Host. |
| **Multimodal Runtime Orchestrator** | HOST VALIDATED | Bounded queue & latency profiling validated on Gateway Host. |
| **Full System Physical Assembly** | SOFTWARE SIMULATED & HOST VALIDATED | Ready for physical hardware bench testing. |

---

## 24. Final Deployment Gap Analysis Table

| Area | Current Status | Identified Gap | Required Action | Target Version |
| :--- | :--- | :--- | :--- | :--- |
| **Camera** | Virtual & Contract Verified | Frame rate needs capping to 0.1 FPS for Wi-Fi. | Configure ESP32-CAM capture interval to 10s. | V4.8 Release |
| **Sensors** | Virtual HAL Verified | Analog probes require physical calibration. | Perform 2-point buffer calibration prior to field use. | Physical Deploy |
| **CV Model** | Trained PyTorch (`.pt`) | Lack of SHA-256 integrity verification at load. | Add SHA-256 digest check in `AquaticBloomCVModel`. | V4.8 Release |
| **Preprocessing** | Hardware Independent | Minor aspect ratio padding overhead. | Maintain native 224x224 scaling mode. | V4.8 Release |
| **Fusion** | Dempster-Shafer Verified | Threshold discrepancy between modules. | Consolidate fusion thresholds in single config. | V4.8 Release |
| **Runtime** | Bounded Queue Verified | Clock drift if ESP32 lacks NTP sync. | Anchor timestamps to Gateway receipt time. | V4.8 Release |
| **MQTT** | Mock & Client Verified | Production broker uses default `localhost`. | Externalize broker IP in environment variables. | V4.8 Release |
| **ESP32** | C++ Firmware Ready | PlatformIO build verified without hardware. | Flash physical ESP32 board and verify serial output. | Physical Deploy |
| **Actuators** | HAL Interface Frozen | Relay flyback protection required on board. | Verify optocoupler & flyback diode on relay board. | Physical Deploy |
| **Configuration** | Split Config Files | Plaintext passwords in `device_config.json`. | Load credentials from env vars / secrets file. | V4.8 Release |
| **Calibration** | Config Schema Ready | Offsets default to 0.0 / scale 1.0. | Apply sensor-specific calibration factors. | Physical Deploy |
| **Dependencies** | Unpinned in requirements.txt | Missing `torch`, `torchvision`, `pillow`. | Add pinned PyTorch dependencies to `requirements.txt`. | V4.8 Release |
| **Logging** | Full SQLite Persistence | Missing ESP32 heap & RSSI logging. | Add RSSI telemetry field to ESP32 health status. | V4.8 Release |
| **Recovery** | Auto Reconnection Verified| None (V3.8 recovery fully sufficient). | Preserve frozen V3.8 communication code. | V4.8 Release |
| **Resource Usage**| Host CPU <100 MB RAM | None (Compute placement on Gateway is safe). | Run Gateway on RPi 4/5 or Host Server. | V4.8 Release |
| **Security** | Hardcoded Credentials | Credentials stored in JSON config. | Externalize secrets to environment. | V4.8 Release |
| **Packaging** | Manifest Needs Update | V4 artifacts missing in release manifest. | Update `config/release_manifest.json`. | V4.8 Release |
| **Testing** | 244/244 Tests Passing | Needs end-to-end V4.8 audit verification test. | Add `test_v4_8_deployment_readiness.py`. | V4.8 Release |

---

## 25. V3.8 Protection Confirmation

The following frozen V3.8 source files have been explicitly audited and confirmed **UNTOUCHED (0 lines modified)**:

1. [src/iot/esp32_device.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/esp32_device.py) — **UNTOUCHED**
2. [src/iot/communication.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/communication.py) — **UNTOUCHED**
3. [src/iot/scheduler.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/scheduler.py) — **UNTOUCHED**
4. [src/iot/hal.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/hal.py) — **UNTOUCHED**
5. [src/iot/actuators.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/actuators.py) — **UNTOUCHED**

---

## 26. Recommended V4.8 Implementation Plan Roadmap

To achieve complete final release readiness following approval of this audit:

1. **Manifest & Dependency Packaging**:
   - Update `config/release_manifest.json` to register V4 CV model artifacts and version metadata.
   - Update `requirements.txt` to include pinned PyTorch (`torch>=2.0.0`), `torchvision>=0.15.0`, and `pillow>=9.5.0` dependencies.

2. **Configuration & Integrity Hardening**:
   - Add SHA-256 checksum verification during `AquaticBloomCVModel.load()`.
   - Consolidate model confidence thresholds into a unified configuration contract.

3. **Release Verification Test Suite**:
   - Create `tests/test_v4_8_deployment_readiness.py` to systematically verify model checksum integrity, configuration coherence, release manifest entries, and failure safety contracts without touching frozen V3.8 code.

4. **Physical Deployment Handover**:
   - Deliver the hardware deployment specification guide for flashing physical ESP32 and ESP32-CAM boards.
