# VERSION 4.8.5 — PHYSICAL INTEGRATION READINESS AUDIT

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Milestone:** V4.8.5 Forensic Audit of Physical Integration Readiness  
**Audit Date:** August 18, 2026  
**Status:** Software Fully Verified / Ready for Future Physical Hardware Build  
**V3.8 Source Code Modifications:** ZERO (0) (Verified via `git status`)

---

> [!IMPORTANT]
> **CRITICAL PHYSICAL HARDWARE BOUNDARY PRINCIPLE**  
> NO physical hardware has been built or tested yet. All physical hardware (ESP32-WROOM-32 board, ESP32-CAM board, sensors, relays, wiring, Wi-Fi AP, MQTT broker) will be physically assembled later strictly following the software architecture and contracts established up to Milestone V4.8.4.  
> 
> Physical hardware testing/validation MUST remain explicitly marked **PENDING**.

---

## 1. Software-to-Hardware Interface & Pin Mapping Audit

### 1.1 Main Sensor & Actuator MCU (ESP32-WROOM-32 / ESP32-WROOM-32E)
- **DS18B20 Temperature Sensor**: `GPIO 18` (OneWire digital interface with 4.7 kΩ pull-up resistor).
- **pH Sensor Probe**: `GPIO 32` (Analog input, mapped to `ADC1_CH4`).
- **Turbidity Sensor**: `GPIO 33` (Analog input, mapped to `ADC1_CH5`).
- **Dissolved Oxygen (DO) Probe**: `GPIO 34` (Analog input, mapped to `ADC1_CH6` — Input Only pin).
- **Salinity / TDS Sensor**: `GPIO 36` (Analog input, mapped to `ADC1_CH0` — VP / Input Only pin).
- **GPS Module**: `GPIO 16` (UART2 RX), `GPIO 17` (UART2 TX).
- **Status LEDs**:
  - Green LED (Normal / System Ready): `GPIO 19`
  - Yellow LED (Warning / Elevated Risk): `GPIO 21`
  - Red LED (Critical / Bloom Alert): `GPIO 22`
- **Audio Alarm Buzzer**: `GPIO 23` (High-active transistor driver).
- **Aerator Pump Control Relay**: `GPIO 27` (Optocoupled relay module driver).

### 1.2 Camera Microcontroller Board (ESP32-CAM AI-Thinker OV2640)
- **Physical Board**: Independent AI-Thinker ESP32-CAM module.
- **Role**: Dedicated frame acquisition and JPEG encoding node.
- **Sampling Contract**: Resolution `224x224` pixels (`FRAMESIZE_224X224`), format `PIXFORMAT_JPEG`, `jpeg_quality = 12`, capture rate `0.1 FPS` (1 frame every 10 seconds).
- **Transport Contract**: Base64 JSON payload published to MQTT topic `aquatic/{device_id}/camera/raw` (Schema 1.1).

---

## 2. Sensor Driver & ADC Architecture Verification

- **ADC Channel Selection**: All analog probes (pH, Turbidity, DO, Salinity) are assigned exclusively to **ADC1** (GPIOs 32, 33, 34, 36). This completely avoids ADC2 pin conflicts during active Wi-Fi transmissions.
- **Calibration Decorator Pattern**: Managed in C++ firmware by `CalibratedSensor` and `CalibrationManager`, decorating raw driver reads with linear zero-point offsets and span scaling factors.
- **Out-of-Bounds & Diagnostic Checks**: Handled by C++ `HAL` and Gateway `EdgeValidator`. Invalid voltage or sensor fault readings trigger `FAULT` / `OUT_OF_BOUNDS` telemetry status.

---

## 3. Actuator Driver & Safety Logic Audit

- **Green LED (`GPIO 19`)**: Indicates normal monitoring operational state.
- **Yellow LED (`GPIO 21`)**: Indicates warning state (elevated sensor telemetry or visual turbidity).
- **Red LED (`GPIO 22`)**: Indicates critical bloom emergency.
- **Buzzer (`GPIO 23`)**: Activated during critical bloom emergency.
- **Pump Relay (`GPIO 27`)**: Activates water aeration pump during critical bloom emergency.
- **Safety Interlock**: Spurious MQTT disconnections or communication drops do **NOT** trigger unsafe pump activation. FSM retains safe previous state.

---

## 4. Telemetry & Camera Data Contracts Audit

- **Telemetry Topic**: `aquatic/{device_id}/telemetry` (Schema 1.1). Transmits wall-clock ISO timestamp, `time_sync_status` (`SYNCED` vs `UNSYNCED`), `clock_source` (`NTP` vs `UNSYNCED_BOOT_TICK`), sensor readings, and diagnostics flags.
- **Camera Topic**: `aquatic/{device_id}/camera/raw` (Schema 1.1). Transmits Base64 JPEG data, frame ID, capture timestamp, `time_sync_status`, and `clock_source`.
- **Decision Topic**: `aquatic/{device_id}/decision` (Schema 1.1). Gateway publishes fused decision state, risk score, and recommended actuation outputs back to the ESP32 main board.

---

## 5. Gateway Temporal Validation & Multi-Tier Timestamp Audit

- **Three Non-Overwriting Timestamps**:
  1. `capture_timestamp`: Recorded on camera hardware upon optical acquisition.
  2. `gateway_receive_timestamp`: Recorded on Gateway host upon MQTT ingress.
  3. `gateway_process_timestamp`: Recorded on Gateway host upon pipeline execution.
- **Gateway Temporal Validator Thresholds**:
  - `MAX_ALLOWED_FRAME_AGE_SEC = 30.0 s` (3x sampling interval).
  - `MAX_FUTURE_TOLERANCE_SEC = 5.0 s` (Clock skew tolerance).
  - `MAX_SENSOR_VISUAL_DELTA_SEC = 15.0 s` (1.5x sampling interval).
- **Monotonic Timing Rule**: Latency calculations use strictly `time.perf_counter()` (Python) and `millis()` (C++). Wall-clock timestamps are **NEVER** subtracted to measure execution latency.

---

## 6. Safety Behavior Audit & Fallback Guarantee

| Failure / Fault Scenario | Visual System State | Fusion Engine State | Safety Outcome | Safety Assertion |
| :--- | :--- | :--- | :--- | :--- |
| **Camera Hardware Disconnect** | `CAMERA_FAULT` | Sensor Telemetry Authoritative | Preserves Sensor Decision | 🟢 **NEVER NO_BLOOM** |
| **Un-synchronized SNTP Clock** | `CAMERA_FAULT` | Sensor Telemetry Authoritative | Preserves Sensor Decision | 🟢 **NEVER NO_BLOOM** |
| **Stale Camera Frame (>30s)** | `CAMERA_FAULT` | Sensor Telemetry Authoritative | Preserves Sensor Decision | 🟢 **NEVER NO_BLOOM** |
| **PyTorch Model Exception** | `CAMERA_FAULT` | Sensor Telemetry Authoritative | Preserves Sensor Decision | 🟢 **NEVER NO_BLOOM** |
| **Sensor Telemetry Fault** | Sensor `FAULT` | Multimodal / Visual State | Preserves Threat Level | 🟢 **NEVER NORMAL** |
| **MQTT Broker Disconnection** | Telemetry Cached | Local FSM Retains State | Maintains Safe Actuation | 🟢 **SAFE ACTUATION** |

---

## 7. Model Checkpoint & Deployment Integrity Audit

- **Model Checkpoint**: `models/cv/aquatic_bloom_mobilenetv3.pt` (5.93 MB / 6,218,731 bytes).
- **Model Checksum (SHA-256)**: `19d84e0b1d27571296591434e02ec9331f14a49c75680f57c73333e7e53bb6bb`.
- **Validation**: Verified by `DeploymentValidator` and `StartupValidator`.
- **Secrets Security**: `.env.example` created. Production config uses `${AQUA_WIFI_PASSWORD}` placeholder.
- **Dependencies**: `requirements.txt` explicitly declares `torch`, `torchvision`, `Pillow`, `opencv-python`, `scipy`.
- **Release Manifest**: `config/release_manifest.json` updated to version `4.8.4` with `physical_hardware_validation: "PENDING"`.

---

## 8. Frozen V3.8 Code Protection Audit

Empirical verification via `git status --porcelain`:

- `src/iot/esp32_device.py`: **UNTOUCHED (0 modifications)**
- `src/iot/communication.py`: **UNTOUCHED (0 modifications)**
- `src/iot/scheduler.py`: **UNTOUCHED (0 modifications)**
- `src/iot/hal.py`: **UNTOUCHED (0 modifications)**
- `src/iot/actuators.py`: **UNTOUCHED (0 modifications)**

---

## 9. Categorized Forensic Statements

### 9.1 REPOSITORY-VERIFIED FACTS
1. PyTorch MobileNetV3 model checkpoint exists with SHA-256 checksum `19d84e0b1d27571296591434e02ec9331f14a49c75680f57c73333e7e53bb6bb`.
2. All 5 frozen V3.8 source files contain exactly zero modifications (100% clean `git status`).
3. Regression baseline stands at 299 passed, 3 skipped under pytest, and 244/244 core Phase 9 assertions passed.

### 9.2 SOFTWARE-VERIFIED BEHAVIORS
1. `TemporalValidator` enforces frame age <30s, clock skew <5s, and sensor-visual delta <15s.
2. Un-synchronized or faulty camera frames trigger `CAMERA_FAULT` and preserve base sensor decisions.
3. `StartupValidator` runs a safe 10-step validation sequence on system launch.

### 9.3 ENGINEERING RECOMMENDATIONS FOR FUTURE HARDWARE BUILD
1. **Dedicated Power Supply**: Use a dedicated 5V 2A power supply for the ESP32-CAM board to prevent voltage brownouts during peak Wi-Fi JPEG transmission.
2. **Optocoupled Relay Isolation**: Connect the aerator pump relay using optocoupled isolation on GPIO 27 to protect the main ESP32 MCU from inductive kickback.

### 9.4 PHYSICAL HARDWARE PENDING
1. Physical PCB fabrication, breadboard wiring, and sensor pin soldering.
2. Physical flashing of PlatformIO C++ firmware to physical ESP32 and ESP32-CAM boards.
3. Physical Wi-Fi network AP connection and SNTP NTP server handshake.

---

## 10. Final Integration Readiness Conclusion

The software codebase is **100% software-complete, fully audited, verified, and ready for future physical hardware integration**.

No software remediation or code modification is required.
