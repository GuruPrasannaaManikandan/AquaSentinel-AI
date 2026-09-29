# SOFTWARE ARCHITECTURE & INTEGRATION READINESS AUDIT REPORT

**Project:** AquaSentinel-AI — IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Audit Milestone:** Pre-Integration Forensic Software Baseline  
**Date:** September 29, 2026  
**Auditor:** Antigravity Forensic Audit Engine  
**Operational Scope:** READ-ONLY Forensic Audit — Zero Modifications Permitted  

---

## 1. Executive Summary

A comprehensive forensic audit of the entire codebase was conducted across firmware (C++), edge/IoT services (Python), computer vision (PyTorch), evidence fusion (AIS/Dempster-Shafer), backend (FastAPI), and frontend (Streamlit). 

The software repository demonstrates advanced architectural maturity in its simulation, statistical validation, and mathematical modeling pipelines (comprising over 35 automated integration tests). However, **the production software is currently running in a purely simulated / mock operational state**:
1. Main ESP32 production firmware (`firmware/src/main.cpp`) hardcodes `ACTIVE_MODE = DriverMode::MOCK`, utilizing in-memory mock drivers, mock Wi-Fi, and mock MQTT.
2. ESP32-CAM production firmware (`firmware/esp32_cam/main_esp32_cam.cpp`) still contains hardcoded **OmniVision OV2640** configurations (`PIXFORMAT_JPEG`), incompatible with the physical **GalaxyCore GC2145** sensor.
3. Central Gateway (`src/iot/gateway.py`) and Backend (`src/backend/services.py`) default to `use_mock=True`, relying on `InMemoryMQTTBroker` and synthetic generator scripts (`sensor_simulator.py`).
4. Pin definitions in `firmware/include/config/PinConfig.h` and `config/device_config.json` reflect a legacy proposal and fundamentally conflict with the physically verified wiring on the breadboard.

---

## 2. Complete Software Architecture Map

The software architecture is partitioned across four operational planes:

```text
+===================================================================================================+
|                                    AQUASENTINEL SOFTWARE PLANES                                   |
+===================================================================================================+

 1. PHYSICAL & BRING-UP PLANE
    ├── firmware/bringup/01_led_buzzer_relay/    (Discrete Actuator Bring-up)
    ├── firmware/bringup/02_led_verification/    (P25, P26, P27 Physical LED Bring-up)
    ├── firmware/bringup/03_buzzer_verification/ (P14 Acoustic Bring-up)
    ├── firmware/bringup/04_ds18b20_verification/(P33 OneWire Temperature Bring-up)
    ├── firmware/bringup/05_ph_power_verification/(P32 Analog pH Bring-up)
    ├── firmware/bringup/06_esp32_cam_verification/(ESP32-CAM Boot Monitor)
    ├── firmware/bringup/07_ov2640_camera_verification/ (GC2145 Optical Bring-up & Python Verifier)
    ├── firmware/bringup/08_turbidity_verification/ (P34 Analog Turbidity Bring-up & Live Monitor)
    └── firmware/bringup/port_config.py          (Centralized COM3/COM4 Serial Tooling Resolver)

 2. EMBEDDED PRODUCTION PLANE (FIRMWARE)
    ├── firmware/src/main.cpp                    (Production Microcontroller Entry Point & Loop)
    ├── firmware/src/HAL.cpp                     (Hardware Abstraction Layer Coordinator)
    ├── firmware/src/DriverFactory.cpp           (Sensor/Actuator Factory: Physical vs. Mock)
    ├── firmware/include/config/PinConfig.h      (GPIO Pin Definitions Struct)
    ├── firmware/lib/PhysicalDrivers/            (Hardware Drivers: PH, Turbidity, DS18B20, LEDs...)
    ├── firmware/lib/MockDrivers/                (In-Memory Simulation Drivers)
    ├── firmware/lib/Calibration/                (Polynomial & Linear Calibration Decorators)
    ├── firmware/lib/Scheduler/                  (Cooperative Non-Preemptive Multi-Tasking Engine)
    ├── firmware/lib/FSM/                        (10-State Deterministic Finite State Machine)
    ├── firmware/lib/WiFi/                       (Wi-Fi State Machine & Connection Policy Manager)
    ├── firmware/lib/MQTT/                       (MQTT Client Manager & QoS Queue Dispatcher)
    ├── firmware/lib/Backend/                    (Telemetry JSON Serializer & Remote Dispatcher)
    └── firmware/esp32_cam/main_esp32_cam.cpp    (Standalone Camera Node Firmware - Draft)

 3. GATEWAY & REASONING PLANE (PYTHON)
    ├── src/iot/gateway.py                       (Central Edge Gateway Coordinator)
    ├── src/iot/sensor_quality.py                (V5.1 Physical Sensor Quality Evaluator Q_sensor)
    ├── src/cv/camera_transport.py               (MQTT Base64 Image Deserializer & SNTP Validator)
    ├── src/cv/image_preprocessing.py            (224x224 RGB Tensor Normalization Pipeline)
    ├── src/cv/optical_quality.py                (V5.2 Optical Quality Assessment Q_visual)
    ├── src/cv/cv_model.py                       (MobileNetV3 PyTorch Deep Learning Classifier)
    ├── src/fusion/temporal_intelligence.py      (V5.3 Temporal Trajectory & Trend Engine)
    ├── src/ais/ais_loader.py                    (V3 Negative Selection Algorithm Classifier)
    ├── src/ais/adaptive_ais.py                  (V5.4 Clonal Selection & Immune Memory Engine)
    ├── src/fusion/multimodal_alignment.py       (V7 5-Modality Snapshot Alignment Layer)
    ├── src/fusion/multimodal_intelligence.py    (V7 Concordance, Conflict, & Dominance Estimator)
    ├── src/fusion/fusion_engine.py              (Dempster-Shafer & Continuous Threat Fusion)
    ├── src/fusion/autonomous_response.py        (V5.8 Dynamic Safety Gate Actuator Controller)
    └── src/iot/event_store.py                   (SQLite Relational Persistence Layer)

 4. APPLICATION & INTERFACE PLANE
    ├── src/backend/app.py                       (FastAPI REST API & WebSocket Server)
    ├── src/backend/services.py                  (Backend Runtime Service Singleton)
    └── dashboard/app.py                         (Streamlit Multi-Page Interactive Dashboard)
```

---

## 3. Main ESP32 Software Trace (Boot to Telemetry)

The execution flow of the Main ESP32 production firmware was traced from entry point to network dispatch:

```text
[Arduino Reset]
       ↓
  setup() [firmware/src/main.cpp:293]
       ↓
  Calibration Database Init [firmware/src/main.cpp:313]
       │ File: firmware/lib/Calibration/CalibrationRepository.cpp
       │ Storage: MockStorage (In-Memory RAM)
       ↓
  HAL Construction & Initialization [firmware/src/main.cpp:318]
       │ File: firmware/src/HAL.cpp:36
       │ Invokes: DriverFactory::create... [firmware/src/DriverFactory.cpp:12-72]
       │ Mode Check: ACTIVE_MODE == DriverMode::MOCK [firmware/src/main.cpp:36]
       │ Drivers Instantiated: MockTemperatureSensor, MockPHSensor, MockTurbiditySensor, etc.
       │ Status: hal.initialize() -> "OK"
       ↓
  FSM Boot Initialization [firmware/src/main.cpp:339]
       │ File: firmware/lib/FSM/FSM.cpp:35
       │ Transition: State::BOOT -> State::INITIALIZING
       ↓
  Network Stack Initialization [firmware/src/main.cpp:344, 349]
       │ WiFi: MockWiFiService (Bypasses real ESP32 radio)
       │ MQTT: MockMQTTService (Bypasses real network TCP socket)
       ↓
  Cooperative Scheduler Task Registration [firmware/src/main.cpp:368-388]
       │ Registered Tasks:
       │   - SENSOR_POLLING (5000 ms, Priority: CRITICAL)
       │   - FSM_UPDATE     (1000 ms, Priority: CRITICAL)
       │   - LED_UPDATE     (1000 ms, Priority: LOW)
       │   - BUZZER_UPDATE  (2000 ms, Priority: NORMAL)
       │   - HEARTBEAT      (3000 ms, Priority: BACKGROUND)
       │   - WIFI_UPDATE    (1000 ms, Priority: NORMAL)
       │   - MQTT_UPDATE    (1000 ms, Priority: NORMAL)
       │   - BACKEND_UPDATE (1000 ms, Priority: NORMAL)
       │   - DIAGNOSTICS    (5000 ms, Priority: NORMAL)
       ↓
  loop() [firmware/src/main.cpp:398]
       │ File: firmware/lib/Scheduler/Scheduler.cpp:45
       │ Method: scheduler.execute()
       ↓
  Periodic Task Execution: sensorPollingTask() [firmware/src/main.cpp:166]
       │ 1. hal.readAllSensors() [firmware/src/HAL.cpp:56]
       │    Calls CalibratedSensor::read() [firmware/lib/Calibration/CalibratedSensor.cpp:18]
       │    Applies CalibrationManager::calibrate() [firmware/lib/Calibration/CalibrationManager.cpp:18]
       │ 2. BackendGateway::publishTelemetry(telemetry) [firmware/lib/Backend/BackendGateway.cpp:364]
       │ 3. TelemetryPublisher::publishTelemetry() [firmware/lib/Backend/TelemetryPublisher.cpp:15]
       │    Serializes JSON payload (schema_version 1.0)
       │    Publishes to MQTT topic: "aquatic/AQUA_FRESH_001/telemetry"
```

---

## 4. Sensor Software Trace (Per Physical Sensor)

Each water-quality sensing channel was traced from raw hardware pin to central database logging:

### 4.1 pH Sensing Channel
- **Physical Pin:** `GPIO 32` (ADC1_CH4).
- **Physical Driver:** `firmware/lib/PhysicalDrivers/PHDriver.cpp`
  - Function: `read()` measures `analogRead(_pin)`, checks saturation (`raw < 10 || raw > 4080`), computes `voltage = raw * (3.3 / 4095.0)`.
  - **Trace Status:** ⚠️ **DISCONNECTED IN PRODUCTION**. `DriverFactory.cpp:26` instantiates `MockPHSensor` because `ACTIVE_MODE = DriverMode::MOCK`.
  - **Voltage Divider Defect:** `PHDriver.cpp:26` does not account for the 33k/22k divider ($0.400\times$). It outputs the junction voltage ($V_{\text{P32}}$) rather than probe output ($V_{\text{Po}} = 2.500 \times V_{\text{P32}}$).
- **Calibration Layer:** `firmware/lib/Calibration/CalibrationProfiles.cpp:9`
  - Formula: `pH = 3.5 * V`. (Assumes direct 0–3.3V input where 2.0V = pH 7.0).
- **HAL Layer:** `firmware/src/HAL.cpp:61` assigns `data.ph = _phSensor->read()`.
- **Telemetry Serializer:** `firmware/lib/Backend/TelemetryPublisher.cpp:32` serializes `sensors["ph"]`.
- **Gateway Ingestion:** `src/iot/gateway.py:212` passes `payload["sensors"]` to `SensorQualityEvaluator::evaluate()`.
- **Quality Evaluation:** `src/iot/sensor_quality.py:326` checks bounds $[0.0, 14.0]$, drift $\le 0.8$, noise $\le 0.35$.
- **Temporal Trajectory:** `src/fusion/temporal_intelligence.py:180` calculates rate of change $\Delta \text{pH}/\Delta t$.
- **Model / AIS Input:** ❌ **NOT INCLUDED IN ML/AIS INPUT VECTOR**. Neither CAML Random Forest nor CAML NSA accepts pH in their input feature vectors.
- **Rule-Based Fusion:** `src/fusion/autonomous_response.py:145` monitors pH bounds to trigger aerator/relay overrides.

### 4.2 Turbidity Sensing Channel
- **Physical Pin:** `GPIO 34` (ADC1_CH6).
- **Physical Driver:** `firmware/lib/PhysicalDrivers/TurbidityDriver.cpp`
  - Function: `read()` measures `analogRead(_pin)`, checks bounds, computes `voltage = raw * (3.3 / 4095.0)`.
  - **Trace Status:** ⚠️ **DISCONNECTED IN PRODUCTION**. `DriverFactory.cpp:33` instantiates `MockTurbiditySensor`.
  - **Pin Mismatch:** Driver is constructed with `pinConfig.turbidityPin` which equals **33** in `PinConfig.h`, whereas physical hardware is on **GPIO 34**.
  - **Voltage Divider Defect:** Returns $V_{\text{P34}}$ instead of sensor $V_{\text{OUT}}$ ($2.500\times$).
- **Calibration Layer:** `firmware/lib/Calibration/CalibrationMath.cpp:13`
  - Formula: $\text{NTU} = -1120.4 \times V^2 + 5742.3 \times V - 4352.9$.
  - **Defect:** With a $0.400\times$ divider, a $1.8\,\text{V}$ pin reading computes to $\text{NTU} \le 0.0$ (clamped to 0.0).
- **Quality & Fusion:** Evaluated in `SensorQualityEvaluator` (bounds $[0, 500]$ NTU) and `TemporalEnvironmentalEngine`.

### 4.3 Temperature Sensing Channel (DS18B20)
- **Physical Pin:** `GPIO 33` (Designed) / `GPIO 18` (in `PinConfig.h`).
- **Physical Driver:** `firmware/lib/PhysicalDrivers/DS18B20Driver.cpp`
  - Function: Wraps `DallasTemperature` and `OneWire`.
  - **Trace Status:** ⚠️ **HARDWARE NOT OPERATIONAL & DISCONNECTED IN PRODUCTION**.
  - Production uses `MockTemperatureSensor`. Physical bring-up in Stage 04 found 0 ROM devices.

### 4.4 Dissolved Oxygen (DO) Channel
- **Physical Pin:** `GPIO 34` (in `PinConfig.h`).
- **Physical Driver:** `firmware/lib/PhysicalDrivers/DODriver.cpp`.
  - **Trace Status:** ❌ **HARDWARE NOT AVAILABLE**. Sensor does not exist physically. Pin 34 is occupied by Turbidity. Production uses `MockDOSensor`.

---

## 5. Actuator Software Trace (Decisions to Physical Outputs)

```text
  [Fusion Engine / Autonomous Response]
       │ File: src/fusion/autonomous_response.py:110
       │ Evaluates: Multimodal threat score & safety gate
       │ Generates: ActuatorDecision("ACTIVATE_PUMP", "APPROVED")
       ↓
  [Central Gateway MQTT Dispatch]
       │ File: src/iot/gateway.py:345
       │ Publishes: Topic "aquatic/AQUA_FRESH_001/command"
       │ Payload: {"command": "ACTIVATE_PUMP", "target": "pump_relay"}
       ↓
  [Main ESP32 MQTT Receiver]
       │ File: firmware/lib/MQTT/MQTTManager.cpp:180
       │ Topic Callback: onMessageReceived()
       │ Dispatches to: MQTTCommandDispatcher [firmware/lib/MQTT/MQTTCommandDispatcher.cpp:45]
       ↓
  [FSM State Update]
       │ File: firmware/lib/FSM/FSM.cpp:177
       │ State Transition: MONITORING -> ALERT
       │ Entry Action: hal.writeActuator("pump_relay", "ON")
       │               hal.writeActuator("red_led", "ON")
       │               hal.writeActuator("green_led", "OFF")
       ↓
  [HAL Actuator Routing]
       │ File: firmware/src/HAL.cpp:75
       │ Invokes: _pumpRelay->writeState("ON")
       │ Invokes: _redLed->writeState("ON")
       ↓
  [Physical Driver Execution]
       │ LEDs: LEDDriver::writeState() [firmware/lib/PhysicalDrivers/LEDDriver.cpp:21]
       │       digitalWrite(_pin, HIGH);
       │ Relay: RelayDriver::writeState() [firmware/lib/PhysicalDrivers/RelayDriver.cpp:21]
       │       digitalWrite(_pin, LOW); (Active-low board)
```

**CRITICAL ACTUATOR CONFLICT FOUND IN FIRMWARE:**
In `firmware/src/main.cpp`:
- `greenLed` uses `pinConfig.greenLedPin` = **19** (Physical pin is **25**).
- `yellowLed` uses `pinConfig.yellowLedPin` = **21** (Physical pin is **26**).
- `redLed` uses `pinConfig.redLedPin` = **22** (Physical pin is **27**).
- `buzzer` uses `pinConfig.buzzerPin` = **23** (Physical pin is **14**).
- `pumpRelay` uses `pinConfig.pumpRelayPin` = **27** (Physically wired to the **Red LED**!).
If `ACTIVE_MODE` were flipped to `PHYSICAL` without correcting `PinConfig.h`, activating the pump relay would toggle `GPIO 27`, flashing the Red LED instead of energizing the relay!

---

## 6. ESP32-CAM & Computer Vision Execution Trace

```text
  [Physical Sensor: GC2145]
       │ Interface: 8-bit DVP parallel bus + SCCB I2C
       │ Sensor Silicon ID: 0x2145
       ↓
  [ESP32-CAM Firmware Capture]
       │ Status: ⚠️ INCOMPATIBILITY IN PRODUCTION FIRMWARE
       │ Production File: firmware/esp32_cam/main_esp32_cam.cpp:101
       │   - Requests: PIXFORMAT_JPEG, FRAMESIZE_224X224 (OV2640 assumes hardware JPEG)
       │   - GC2145 lacks hardware JPEG! This initialization FAILS on GC2145.
       │ Verified Bring-Up File: firmware/bringup/07_ov2640_camera_verification/
       │   - Uses: PIXFORMAT_RGB565 -> PSRAM -> fmt2jpg() software compression
       │   - Proven: Captures valid 224x224 JPEGs in 5,618 Bytes
       ↓
  [MQTT Frame Transport]
       │ File: firmware/esp32_cam/main_esp32_cam.cpp:70
       │ Encodes: Base64 string of JPEG bytes
       │ Schema: CameraMessageContract (Version 1.1)
       │ Topic: "aquatic/AQUA_FRESH_001/camera/raw"
       ↓
  [Gateway Ingestion & Transport Receiver]
       │ File: src/cv/camera_transport.py:155
       │ Class: CameraTransportReceiver
       │ Subscribes: "aquatic/+/camera/raw"
       │ Deserializes: CameraMessageContract.from_mqtt_payload()
       │ Checks: Payload size (< 500 KB), JPEG magic bytes (0xFF 0xD8), SNTP sync
       │ Emits: CameraFrame object
       ↓
  [Optical Quality Assessment (V5.2)]
       │ File: src/cv/optical_quality.py:38
       │ Class: OpticalQualityEvaluator
       │ Calculates: Contrast, brightness, blur/sharpness (Laplacian variance), exposure
       │ Emits: OpticalQualityResult with composite score Q_visual in [0.0, 1.0]
       ↓
  [Image Preprocessing Pipeline]
       │ File: src/cv/image_preprocessing.py:35
       │ Class: ImagePreprocessor
       │ Converts: JPEG -> PIL -> NumPy RGB float32 (224, 224, 3)
       │ Normalization: Standard ImageNet (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
       │ Emits: PreprocessedImage tensor
       ↓
  [MobileNetV3 Deep Learning Inference]
       │ File: src/cv/cv_model.py:62
       │ Class: AquaticBloomCVModel
       │ Model Weights: models/cv/aquatic_bloom_mobilenetv3.pt (5.93 MB)
       │ Execution: Gateway CPU/GPU (PyTorch) - NOT on ESP32-CAM!
       │ Outputs: Class probabilities across 3 classes:
       │   0: NORMAL_WATER
       │   1: ALGAL_BLOOM
       │   2: TURBID_DISCOLORATION
       │ Emits: CVPrediction
       ↓
  [Visual Evidence Generation]
       │ File: src/cv/visual_detection.py:58
       │ Class: VisualDetector
       │ Fuses: Prediction confidence with Optical Quality Q_visual
       │ Emits: VisualEvidence(visual_state, effective_confidence, q_visual)
       ↓
  [V7 Multimodal Evidence Alignment & Fusion]
       │ File: src/fusion/multimodal_alignment.py:172
       │ Fuses: VisualEvidence into composite risk score alongside Sensor & AIS evidence
```

---

## 7. Software Architecture Inventory & Readiness

| Subsystem | Architectural Location | Implementation Status | Real Hardware Ready? | Evidence / File Reference |
| :--- | :--- | :--- | :--- | :--- |
| **Main C++ Firmware** | `firmware/src/main.cpp` | **EXISTS** | 🔴 NO (Hardcoded MOCK) | `main.cpp:36`: `const DriverMode ACTIVE_MODE = DriverMode::MOCK;` |
| **C++ HAL** | `firmware/src/HAL.cpp` | **EXISTS** | 🟡 PARTIAL (Pin mismatches) | `HAL.cpp:4`: Depends on `PinConfig` with conflicting GPIO numbers |
| **Physical Drivers** | `firmware/lib/PhysicalDrivers/` | **EXISTS** | 🟡 PARTIAL (Unit/divider defects)| `PHDriver.cpp`, `TurbidityDriver.cpp` missing 0.4x divider scale |
| **C++ Scheduler** | `firmware/lib/Scheduler/` | **PRODUCTION READY** | 🟢 YES | Cooperative scheduler tested; handles 11 tasks with < 2% CPU load |
| **C++ FSM** | `firmware/lib/FSM/` | **PRODUCTION READY** | 🟡 PARTIAL (Logic gap) | FSM transitions work, but `HAL::readAllSensors` never sets CRITICAL |
| **C++ Wi-Fi Manager** | `firmware/lib/WiFi/` | **EXISTS** | 🔴 NO (Uses MockWiFiService)| `main.cpp:84`: Instantiates `MockWiFiService mockWiFi;` |
| **C++ MQTT Manager** | `firmware/lib/MQTT/` | **EXISTS** | 🔴 NO (Uses MockMQTTService)| `main.cpp:92`: Instantiates `MockMQTTService mockMQTT;` |
| **ESP32-CAM Firmware**| `firmware/esp32_cam/` | **STUB / DRAFT** | 🔴 NO (OV2640 assumption) | `main_esp32_cam.cpp:101`: Requests hardware JPEG (crashes GC2145) |
| **Camera Bring-Up** | `firmware/bringup/07_...`| **PRODUCTION READY** | 🟢 YES (GC2145 tested) | `07_ov2640_camera_verification.ino`: Fully working GC2145 driver |
| **Camera Transport** | `src/cv/camera_transport.py`| **PRODUCTION READY** | 🟢 YES | Tested against live MQTT payloads in `test_v4_8_2_camera_transport.py` |
| **Image Preprocessor**| `src/cv/image_preprocessing.py`| **PRODUCTION READY** | 🟢 YES | Validated: 224x224 RGB float32 normalization |
| **Optical Quality** | `src/cv/optical_quality.py` | **PRODUCTION READY** | 🟢 YES | Computes blur, contrast, brightness, exposure Q_visual |
| **CV Inference Model**| `src/cv/cv_model.py` | **PRODUCTION READY** | 🟢 YES | Executes MobileNetV3-Small binary weights (`models/cv/*.pt`) |
| **Supervised ML Model**| `src/models/deployment_loader.py`| **PRODUCTION READY** | 🟢 YES | Loads CAML/HABSOS Random Forest joblib pipelines |
| **AIS Anomaly Engine**| `src/ais/ais_loader.py` | **PRODUCTION READY** | 🟢 YES | Negative Selection Algorithm with 1000 Euclidean detectors |
| **Evidence Fusion** | `src/fusion/fusion_engine.py` | **PRODUCTION READY** | 🟢 YES | Continuous threat weighting: $(w_s t_s + w_{ais} t_{ais} + w_t t_t + w_v t_v)/\sum w$ |
| **Temporal Engine** | `src/fusion/temporal_intelligence.py`| **PRODUCTION READY** | 🟢 YES | Evaluates rate-of-change and multi-step trajectory slopes |
| **Safety Gate Actuator**| `src/fusion/autonomous_response.py`| **PRODUCTION READY** | 🟢 YES | Multi-barrier cooldown and quality protection gate |
| **Central IoT Gateway**| `src/iot/gateway.py` | **EXISTS** | 🟡 PARTIAL (Defaults to mock) | Ingests MQTT, routes features; `use_mock=True` by default |
| **Backend API** | `src/backend/app.py` | **PRODUCTION READY** | 🟡 PARTIAL (Runs mock sim) | FastAPI REST & WebSockets operational, wired to simulated devices |
| **Dashboard** | `dashboard/app.py` | **PRODUCTION READY** | 🟡 PARTIAL (Monitors mock)| Streamlit UI operational, polling FastAPI at `localhost:8000` |
| **Event Persistence** | `src/iot/event_store.py` | **PRODUCTION READY** | 🟢 YES | SQLite relational database schema fully implemented |

---

## 8. Data Contract & Representation Audit

The representation of water-quality parameters was audited across the entire pipeline:

```text
[Physical Probe] ──> [Divider (0.4x)] ──> [ESP32 ADC] ──> [HAL Telemetry] ──> [MQTT Payload] ──> [Gateway / Models]
```

### Forensic Mismatches Identified:
1. **pH Unit Inconsistency:**
   - Physical output: $V_{\text{Po}} \approx 2.500 \times V_{\text{P32}}$.
   - `PHDriver.cpp`: Returns raw pin voltage ($V_{\text{P32}} \approx 1.25\,\text{V}$ in water).
   - `CalibrationProfiles.cpp`: Applies $\text{pH} = 3.5 \times V_{\text{raw}} = 3.5 \times 1.25 = 4.375$.
   - Real mineral water is $\approx 7.0 - 7.4$. The $0.400\times$ divider artificially suppresses the reported pH into severe acid range ($\text{pH} \approx 4.37$), triggering false alarms in `SensorQualityEvaluator`!
2. **Turbidity Unit Inconsistency:**
   - Physical output: Clamped at quiescent ground rail ($V_{\text{P34}} \approx 0.258\,\text{V}$, $V_{\text{OUT}} \approx 0.643\,\text{V}$).
   - `TurbidityDriver.cpp`: Returns $0.258\,\text{V}$.
   - `CalibrationMath.cpp`: Applies $-1120.4 \times V^2 + 5742.3 \times V - 4352.9 = -2945.9 \rightarrow$ clamped to **0.0 NTU**.
   - If the trimpot is adjusted to $1.8\,\text{V}$ at the pin ($4.5\,\text{V}$ at module), the formula without $2.5\times$ scaling yields $-1120.4 \times 1.8^2 + 5742.3 \times 1.8 - 4352.9 = 2353.1 \rightarrow$ clamped to **500.0 NTU** (maximum dirty water)!
   - **Conclusion:** The calibration layer cannot be used until the $0.400\times$ voltage divider factor ($2.500\times$ inverse multiplier) is formally incorporated.
3. **CAML ML Model Feature Omission:**
   - The supervised CAML model (`models/caml_best_model.joblib`) predicts cyanobacteria bloom probability strictly using **geospatial and temporal coordinates** (`lat`, `lon`, `distance_to_water_m`, `region`, `Season`, `Year`, `Month_sin/cos`, `DayOfYear_sin/cos`).
   - It **does NOT consume pH, Turbidity, or DO**! Physical water chemistry enters the system exclusively through `SensorQualityEvaluator`, `TemporalEnvironmentalEngine`, and rule-based safety thresholds in `AutonomousResponseEngine`.

---

## 9. Failure Handling & System Resilience Audit

The repository was inspected for fault tolerance behaviors:

| Fault Scenario | Expected Response | Implemented Behavior | Evidence / Location |
| :--- | :--- | :--- | :--- |
| **ADC Short / Float** | Reject reading; flag ADC failure | Returns `-999.0f`, sets `DriverHealth::ADC_FAILURE` | `PHDriver.cpp:21`, `TurbidityDriver.cpp:20` |
| **Sensor Disconnected** | Prevent crash; flag disconnected | Returns `-999.0f`, sets `SENSOR_DISCONNECTED` | `DS18B20Driver.cpp:22, 43` |
| **Wi-Fi Dropped** | Queue messages; attempt reconnect | Enqueues publishes up to queue capacity; exponential retry | `WiFiManager.cpp:145`, `MQTTManager.cpp:210` |
| **Camera Dropped / Offline**| Fall back to sensor-only fusion | Replaces visual evidence with `UNCERTAIN`; drops $w_{\text{visual}}$ weight to 0.0 | `fusion_engine.py:222`, `camera_driver.py:113` |
| **Corrupted Camera Frame** | Intercept before model inference | Validates JPEG SOI (`0xFF 0xD8`) and EOI; rejects payload | `camera_transport.py:114`, `camera_driver.py:336` |
| **SNTP Clock Drift** | Flag temporal desynchronization | `TemporalValidator` computes $\Delta t$; tags `STALE` or `UNSYNCED` | `temporal_validator.py:75`, `camera_transport.py:119` |
| **Noisy Sensor Probe** | Block spurious actuator trigger | `ActuatorSafetyGate` enforces minimum $Q_{\text{sensor}} \ge 0.70$ and cooldown | `autonomous_response.py:46, 120` |
| **Sensor Fault in Ingestion**| Bypass ML inference; trigger alert | Sets `final_state = "SENSOR_FAULT"`, bypasses ML pipeline | `gateway.py:225` |

---

## 10. Legacy, Duplicate, and Dead Code Inventory

1. **OmniVision OV2640 Artifacts:**
   - `firmware/esp32_cam/main_esp32_cam.cpp`: Hardcoded OV2640 strings and `PIXFORMAT_JPEG` parameters.
   - `firmware/bringup/07_ov2640_camera_verification/`: Named `ov2640`, but internally updated to GC2145.
2. **Obsolete Pin Definitions:**
   - `firmware/include/config/PinConfig.h`: Defines old pins (Green=19, Yellow=21, Red=22, Buzzer=23, Relay=27, Temp=18, Turbidity=33, DO=34).
   - `config/device_config.json`: Duplicates the obsolete `PinConfig.h` pin table under `gpio`.
   - `docs/HARDWARE_INTEGRATION_GUIDE.md`: Outdated document recommending strapping pins GPIO 12 and 15.
3. **Simulated ESP32 Duplicate Architecture:**
   - `src/iot/esp32_device.py` contains a complete duplicate reimplementation of an ESP32 FSM, scheduler, and drivers in Python, creating divergence between Python simulation behavior and real C++ firmware.
4. **Hardcoded HiveMQ Broker URL:**
   - `firmware/src/main.cpp:88` specifies `broker.hivemq.com`. `main_esp32_cam.cpp:45` specifies `192.168.1.100`. `device_config.json` specifies `localhost`. There is no unified broker endpoint across configurations.

---

## 11. Test Coverage Matrix

| Pipeline Level | Test File | Test Count | Scope | Hardware Dependency |
| :--- | :--- | :---: | :--- | :--- |
| **Camera Transport** | `tests/test_v4_8_2_camera_transport.py` | 14 tests | Base64 decode, schema 1.1, size caps | Software Unit Tests (Mock) |
| **Time Sync** | `tests/test_v4_8_3_time_synchronization.py`| 16 tests | SNTP drift, timestamp monotonicity | Software Unit Tests (Mock) |
| **Deployment Integrity**| `tests/test_v4_8_4_deployment_integrity.py` | 12 tests | Package manifests, environment variables | Integration Tests |
| **Software Stability** | `tests/test_v4_8_6_software_stability.py` | 10 tests | Memory leaks, stress loops, resilience | Unit Tests |
| **Sensor Intelligence** | `tests/test_v5_1_sensor_intelligence.py` | 18 tests | Quality scoring Q_sensor, bounds, noise | Algorithmic Unit Tests |
| **Optical Intelligence**| `tests/test_v5_2_optical_intelligence.py` | 20 tests | Optical quality Q_visual, blur, contrast | Algorithmic Unit Tests |
| **Temporal Engine** | `tests/test_v5_3_temporal_intelligence.py` | 15 tests | Slopes, multi-step trend risk | Algorithmic Unit Tests |
| **Decision Core** | `tests/test_v5_4_v5_5_decision_core.py` | 12 tests | Adaptive AIS, clonal memory cells | Algorithmic Unit Tests |
| **Computer Vision** | `tests/test_v6_computer_vision.py` | 22 tests | MobileNetV3 weights, tensor validation | Model Unit Tests |
| **Multimodal Intelligence**| `tests/test_v7_multimodal_intelligence.py` | 25 tests | Concordance, conflict detection, alignment | Fusion Unit Tests |
| **Final Deployment** | `tests/test_v8_final_deployment.py` | 24 tests | End-to-end multi-tier response | System Integration Tests |
| **Physical Bring-Up** | `firmware/bringup/01_` to `08_` | 8 stages | Physical GPIOs, ADCs, LEDs, Buzzer, GC2145 | **REAL HARDWARE BENCH TESTS** |
| **Production Firmware** | `firmware/test/` | 0 tests | None in test folder; boot self-tests only | **ZERO PRODUCTION HARDWARE TESTS** |

---

## 12. Integration Blockers & Missing Work

### Blocker 1: Production Firmware Hardware Mode Lock
- `firmware/src/main.cpp:36` has `ACTIVE_MODE = DriverMode::MOCK`.
- Flipping to `DriverMode::PHYSICAL` is blocked until `PinConfig.h` and driver divider factors are updated.

### Blocker 2: Pin Assignment Conflict
- `PinConfig.h` assigns `pumpRelayPin = 27`, but `GPIO 27` is physically soldered to the Red Status LED.
- `PinConfig.h` assigns `turbidityPin = 33`, but Turbidity is physically wired to `GPIO 34`.
- `PinConfig.h` assigns `buzzerPin = 23`, but Buzzer is physically wired to `GPIO 14`.
- `PinConfig.h` assigns `greenLedPin = 19`, `yellowLedPin = 21`, `redLedPin = 22` (Physical are 25, 26, 27).

### Blocker 3: Voltage Divider Scale Omission in Drivers
- Neither `PHDriver.cpp` nor `TurbidityDriver.cpp` applies the required $2.500\times$ inverse multiplier for the physical 33k/22k divider network.

### Blocker 4: Turbidity Optical Saturation
- The physical turbidity trimpot is biased at negative ground saturation ($0.258\,\text{V}$), rendering the optical sensor unresponsive to water until physically adjusted.

### Blocker 5: GC2145 Production Firmware Porting
- `firmware/esp32_cam/main_esp32_cam.cpp` must be updated with the working GC2145 software JPEG pipeline (`fmt2jpg`) developed and verified in `firmware/bringup/07_ov2640_camera_verification/`.

### Blocker 6: Unified Network Broker Endpoint
- `firmware/src/main.cpp` (HiveMQ), `main_esp32_cam.cpp` (192.168.1.100), `device_config.json` (localhost), and `gateway.py` (InMemory) must agree on a common IP/hostname before physical wireless transmission can succeed.

---

## 13. Recommended Order of Integration (FOR FUTURE PLANNING ONLY)

When integration is formally authorized, work must proceed in strict linear stages:

```text
STAGE 1: CONFIGURATION & PIN ALIGNMENT
         ├── Update PinConfig.h to match verified physical wiring (25, 26, 27, 14, 32, 34)
         ├── Reallocate Relay GPIO to a free, safe output pin
         └── Mirror pin changes in config/device_config.json

STAGE 2: DRIVER VOLTAGE SCALING
         ├── Update PHDriver.cpp with 2.500x inverse divider multiplier (or divider ratio parameter)
         └── Update TurbidityDriver.cpp with 2.500x inverse divider multiplier

STAGE 3: DISCRETE ACTUATOR INTEGRATION (MAIN ESP32)
         ├── Switch DriverFactory LED & Buzzer to DriverMode::PHYSICAL
         └── Validate FSM state transitions driving physical LEDs and Buzzer on COM3

STAGE 4: PH SENSOR PRODUCTION INTEGRATION (MAIN ESP32)
         ├── Switch DriverFactory PHSensor to DriverMode::PHYSICAL
         └── Verify calibrated pH telemetry flowing through HAL

STAGE 5: TURBIDITY SENSOR INTEGRATION (MAIN ESP32)
         ├── Physically adjust trimpot on hardware bench to ~1.6V–2.0V quiescent point
         ├── Validate optical water response
         └── Switch DriverFactory TurbiditySensor to DriverMode::PHYSICAL

STAGE 6: GC2145 PRODUCTION FIRMWARE IMPLEMENTATION (ESP32-CAM)
         ├── Port verified GC2145 RGB565 + fmt2jpg() pipeline into firmware/esp32_cam/
         ├── Flash to COM4
         └── Validate 224x224 Base64 JPEG frame generation

STAGE 7: REAL MQTT BROKER SETUP & WIRELESS COUPLING
         ├── Launch local MQTT broker (Mosquitto)
         ├── Configure WiFi credentials and broker IP across both microcontrollers
         └── Switch Gateway (src/iot/gateway.py) use_mock=False

STAGE 8: FULL SYSTEM CLOSED-LOOP VALIDATION
         ├── Validate end-to-end data flow: Physical Probes + Camera -> MQTT -> Gateway -> CV + AIS -> FSM Actuation -> Backend -> Dashboard
         └── Execute Soak Test to verify 0 memory leaks and stable 240MHz operation
```
