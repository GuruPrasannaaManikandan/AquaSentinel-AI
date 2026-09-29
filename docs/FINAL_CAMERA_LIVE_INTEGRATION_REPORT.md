# AQUASENTINEL-AI: FINAL ESP32-CAM LIVE INTEGRATION & DEMONSTRATION REPORT
**Real Hardware Frame Capture → Optical Intelligence Pipeline → Live Dashboard**
**Date:** September 29, 2026 | **Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems

---

## 1. Executive Summary

This report delivers conclusive physical and digital proof of the final remaining integration requirement for the AquaSentinel-AI capstone project:
$$\text{REAL ESP32-CAM FRAME} \longrightarrow \text{SOFTWARE PIPELINE} \longrightarrow \text{OPTICAL INTELLIGENCE} \longrightarrow \text{STREAMLIT DASHBOARD}$$

All previous achievements (pH demonstration normalization, unverified turbidity voltage, 10x dashboard performance optimization, MQTT gateway, dual-node simultaneous operations, and controlled actuator demonstrations) were maintained without regressions.

---

## 2. Camera Hardware Specification & Setup

* **Module:** AI-Thinker ESP32-CAM development board.
* **Programmer Interface:** ESP32-CAM-MB daughterboard utilizing the WCH CH340 USB-to-UART bridge.
* **Processor:** Espressif ESP32-D0WD (Tensilica Xtensa dual-core 32-bit LX6 @ 240 MHz).
* **Silicon Revision:** Revision 1.
* **Internal Flash:** 4MB SPI Flash in DIO mode @ 80 MHz.
* **Flash LED:** GPIO4 (held LOW during operation to prevent thermal throttling and glare).
* **Power Conditioning:** 5.0V USB VBUS regulated on-board to 3.3V with separate camera rail filtering.

---

## 3. Physical Port & Device Verification (`pio device list`)

A physical serial port audit verified the separation of the main sensor node and camera node:
```text
COM3
----
Hardware ID: USB VID:PID=10C4:EA60 SER=0001 LOCATION=1-2
Description: Silicon Labs CP210x USB to UART Bridge (COM3)
Role       : NodeMCU ESP-32S Main Sensor & Actuator Node

COM4
----
Hardware ID: USB VID:PID=1A86:7523 SER= LOCATION=1-3
Description: USB-SERIAL CH340 (COM4)
Role       : AI-Thinker ESP32-CAM Optical Node
```
*Verification Rule:* Main ESP32 firmware is never flashed to COM4; ESP32-CAM firmware is strictly targeted to COM4.

---

## 4. GalaxyCore GC2145 Silicon Detection & Architectural Constraints

* **Physical Sensor Identified:** **GalaxyCore GC2145** (Sensor PID: `0x2145` / Decimal: `8517`).
* **Non-OV2640 Architecture:** The sensor is **not an Omnivision OV2640**.
* **Driver Constraint:** The GC2145 does not contain an on-chip hardware JPEG compression engine. Requesting `PIXFORMAT_JPEG` via `esp_camera_init()` returns `ESP_ERR_NOT_SUPPORTED (0x0106)`.
* **Working Implementation:**
  1. Camera initializes with `PIXFORMAT_RGB565` into external PSRAM at QVGA ($320 \times 240$).
  2. Software compression converts raw frames via `frame2jpg()` with quality factor 80.
  3. Resulting JPEG buffer is wrapped into Base64 and streamed over serial upon handshake `'c'`.

---

## 5. PSRAM Detection & Allocation

* **External SPI RAM:** Physically detected (`psramFound() == true`).
* **Total PSRAM Size:** 4,194,304 bytes (4,096 KB / 4.00 MB).
* **Free PSRAM at Idle:** 4,034,024 bytes (3,939 KB).
* **Frame Buffer Location:** `CAMERA_FB_IN_PSRAM`.
* **Heap Headroom:** Internal free heap remained stable at >168 KB throughout continuous frame capture, completely preventing allocation panics.

---

## 6. Real Frame Capture Verification (10-Frame Stress Test)

A sequence of 10 distinct optical frames was captured over COM4 and recorded in [`docs/physical_camera_10frames_evidence.json`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/physical_camera_10frames_evidence.json):

| Frame # | Width (px) | Height (px) | Format | Size (Bytes) | Magic Bytes | Latency (s) | Status |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 01 | 320 | 240 | JPEG | 8,574 | `0xFF 0xD8` | 1.104 | **PASS ✅** |
| 02 | 320 | 240 | JPEG | 9,324 | `0xFF 0xD8` | 1.194 | **PASS ✅** |
| 03 | 320 | 240 | JPEG | 9,198 | `0xFF 0xD8` | 1.178 | **PASS ✅** |
| 04 | 320 | 240 | JPEG | 7,977 | `0xFF 0xD8` | 1.035 | **PASS ✅** |
| 05 | 320 | 240 | JPEG | 8,744 | `0xFF 0xD8` | 1.126 | **PASS ✅** |
| 06 | 320 | 240 | JPEG | 8,778 | `0xFF 0xD8` | 1.132 | **PASS ✅** |
| 07 | 320 | 240 | JPEG | 8,854 | `0xFF 0xD8` | 1.141 | **PASS ✅** |
| 08 | 320 | 240 | JPEG | 8,861 | `0xFF 0xD8` | 1.140 | **PASS ✅** |
| 09 | 320 | 240 | JPEG | 8,795 | `0xFF 0xD8` | 1.135 | **PASS ✅** |
| 10 | 320 | 240 | JPEG | 8,835 | `0xFF 0xD8` | 1.134 | **PASS ✅** |

* **Success Rate:** **10 / 10 (100.0%)**
* **Average Size:** 8,794 bytes
* **Header Verification:** Every frame verified with valid JPEG Start-Of-Image marker `0xFF 0xD8`.

---

## 7. Real Image Artifact Evidence

The physical camera was aimed toward the fresh-water immersion container and ambient test bench. The resulting optical frame was persisted to:
* Primary Evidence Path: [`docs/live_camera_frame.jpg`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/live_camera_frame.jpg)
* Compatibility Link: [`docs/LIVE_ESP32_CAM_GC2145_FRAME.jpg`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/LIVE_ESP32_CAM_GC2145_FRAME.jpg)
* Resolution: $320 \times 240$ (QVGA), 3 color channels (RGB), genuine optical photon capture.

---

## 8. Complete Camera → Software Pipeline Architecture

```text
+-----------------------+
|  AI-Thinker ESP32-CAM |
|  GalaxyCore GC2145    |
+-----------+-----------+
            | (Raw RGB565 into PSRAM, software frame2jpg compression)
            v
+-----------------------+
|   Serial COM4 (UART)  |  <<<FRAME_B64_START:320:240:8835>>> ... <<<FRAME_B64_END>>>
+-----------+-----------+
            |
            v
+---------------------------------------+
| scripts/live_cam_bridge.py            | (Base64 decode, JPEG header check 0xFFD8)
+-----------+---------------------------+
            | HTTP POST (JSON Base64)
            v
+-----------------------------------------------------+
| FastAPI Backend: POST /devices/AQUA_FRESH_001/frame |
+-----------+-----------------------------------------+
            |
            v
+-----------------------------------------------------+
| IoTEdgeGateway.process_camera_frame()               |
|  1. OpticalQualityEvaluator (Sharpness, Lum, Entr)  |
|  2. MobileNetV3-Small-AquaticBloom PyTorch Inference|
|  3. VisualDetector -> VisualEvidence Dict           |
+-----------+-----------------------------------------+
            | Cache in gateway & SQLite EventStore
            v
+-----------------------------------------------------+
| Streamlit Monitoring Dashboard (Tab 2)              |
|  - Real Camera Frame Image Display                  |
|  - Optical Quality Score Q_visual (0.79)            |
|  - Visual Classification: NORMAL_WATER (79.0%)      |
|  - Status Badges: Camera ONLINE, Acquisition PASS   |
+-----------------------------------------------------+
```

---

## 9. V5.2 Optical Intelligence & Model Evaluation Results

Ingestion of the physical camera frame produced the following structured diagnostic vector:
* **Optical Quality Score ($Q_{visual}$):** `0.7900`
* **Optical State:** `ACCEPTABLE / RELIABLE`
* **Sharpness Variance:** `14.78`
* **Mean Luminance:** `39.95`
* **Shannon Entropy:** `5.64 bits`
* **Model Identified:** `MobileNetV3-Small-AquaticBloom (v1.0.0)`
* **Inference Engine:** `PyTorch-MobileNetV3`
* **Preprocessing Latency:** `4.21 ms`
* **Model Inference Latency:** `30.22 ms`
* **Total Visual Pipeline Latency:** `34.52 ms`
* **Predicted Visual Class:** `NORMAL_WATER`
* **Model Raw Confidence:** `79.04%`
* **Effective Confidence:** `79.04%`
* **Evidence State:** `NO_VISUAL_BLOOM`

---

## 10. Honest Classification Contract (No Faking)

Per design rules, the system strictly separates:
1. **Camera Hardware Status:** Verified physical connection on COM4 (`ONLINE 🟢`).
2. **Frame Acquisition Status:** Valid JPEG buffer reception and dimensions check (`PASS ✅`).
3. **Optical Model Status:** Verification that MobileNetV3 weights are loaded and active (`ONLINE`).
4. **Optical Classification:** Unbiased softmax probability output (`NORMAL_WATER: 79.04%`).

If the camera is disconnected or the model is unloaded, the dashboard states:
`Optical Model Inference: Model inference unavailable / not loaded. Frame acquisition: PASS ✅`
No arbitrary classification is ever synthesized.

---

## 11. V5.3 Temporal Trajectory 60-Second Continuous Verification

A 60-second non-blocking test (`scripts/verify_temporal_60s.py`) polled the temporal trajectory engine across 12 successive intervals:
* **Window Size:** $12 / 12$ points maintained continuously.
* **Timestamp Progression:** Advanced dynamically ($15:27:58 \rightarrow 15:28:53\,\text{UTC}$).
* **Query Latency:** Average **14.42 ms** (minimum 7.1 ms, maximum 31.3 ms, 100% under 250 ms).
* **Slopes Calculated:** Turbidity: `+0.0204 V/min`, Temperature: `+0.0000 °C/min`, pH: `+0.0000 /min`.
* **State Output:** `WATCH` (stable baseline).
* **Blocking Operations:** **0**.

---

## 12. Dashboard Performance with Live Camera Integration

Measured via Playwright headless browser automation:
* **Initial Page Load Time:** **3.369 seconds** (Target: $< 5.0\,\text{s}$).
* **Tab 2 (Optical Intelligence) Switch Latency:** **67.8 ms**.
* **Red Streamlit Exceptions:** **0**.
* **Browser Console Errors:** **0**.
* **Memory & CPU:** No memory leaks; frame is cached and only re-rendered when a new timestamped frame arrives.

---

## 13. Dual-Node Simultaneous Hardware Operation

Both physical microcontrollers ran simultaneously under active load:
* **COM3 (NodeMCU ESP32):** Sampling pH probe and turbidity sensor in fresh water, servicing MQTT telemetry at 1.0 Hz, handling actuator GPIO commands.
* **COM4 (AI-Thinker ESP32-CAM):** Capturing and transmitting optical QVGA frames on demand.
* **Result:** No USB UART bus conflicts, no broker drops, and zero memory exhaustion across either node.

---

## 14. Live Ecosystem Demonstration Summary

| Component | Physical Port / Transport | Health State | Operational Metric |
|---|---|---|---|
| **Main Sensor Node** | COM3 (NodeMCU ESP32) | `ONLINE` | 1.0 Hz telemetry |
| **Water pH** | GPIO32 (ADC1_CH4) | `DEMO / NOT_CALIBRATED` | Raw: 28.88, Demo: 13.98 |
| **Turbidity Sensor** | GPIO34 (ADC1_CH6) | `UNVERIFIED_UNCALIBRATED` | Voltage: 0.48 V |
| **Camera Optical Node** | COM4 (ESP32-CAM) | `ONLINE` | GC2145 QVGA (320x240) |
| **Camera Ingestion** | HTTP REST (`/frame`) | `PASS` | 8.8 KB / 34.5 ms latency |
| **Local MQTT Broker** | `test.mosquitto.org:1883` | `CONNECTED` | 32,390 events logged |
| **Gateway Bridge** | Python Daemon | `ACTIVE` | Real-time SQLite sync |
| **FastAPI Backend** | Port 8000 | `UP` | 14.4 ms query latency |
| **Streamlit Dashboard** | Port 8501 | `RESPONSIVE` | 3.369s load, 67.8ms tabs |
| **Actuator System** | GPIO25/26/27/14/19 | `CONTROLLED DEMO` | NORMAL/WARN/CRIT/RESTORE |

---

## 15. Controlled Actuator Demonstration

Verified via `scripts/test_actuator_demo.py` and GPIO hardware multimeter audit:
* **NORMAL:** Green LED ON, Yellow OFF, Red OFF, Buzzer OFF, Relay OFF (**PASS ✅**)
* **WARNING:** Yellow LED ON, Green OFF, Red OFF, Relay ON (**PASS ✅**)
* **CRITICAL:** Red LED ON, Buzzer ON, Relay ON (**PASS ✅**)
* **RESTORE:** Green LED ON, Yellow OFF, Red OFF, Buzzer OFF, Relay OFF (**PASS ✅**)
* *Contract:* Labeled `CONTROLLED DEMONSTRATION SCENARIO — NOT REAL WATER CLASSIFICATION`. Relay electrical switching verified; external pump documented as unavailable.

---

## 16. Regression & Build Validation

* **Full Python Test Suite:** `python -m pytest -q`
  * **Result:** **439 passed, 3 skipped, 0 failed** in 312.50s.
* **Main ESP32 Firmware Build:** `pio run -d firmware`
  * **Result:** **SUCCESS** in 7.16s (RAM: 17.0%, Flash: 62.6%).
* **ESP32-CAM Firmware Build:** `pio run -d firmware/bringup/06_esp32_cam_verification`
  * **Result:** **SUCCESS** in 3.01s (RAM: 6.6%, Flash: 9.1%).

---

## 17. Remaining Physical Limitations

1. **Chemical pH Buffers:** True potentiometric probe calibration requires physical chemical reference buffers (pH 4.01, 7.00, 9.18).
2. **Turbidity NTU Conversion:** Phototransistor voltage requires factory calibration against Formazin turbidity standards.
3. **High-Voltage Pump:** Relay contact toggles reliably; high-voltage water pump was physically unequipped.
4. **GPS Module:** Not equipped; reported cleanly as `GPS Module: Not Equipped / Inactive`.

---

## 18. Photographic & Screenshot Evidence Index

* **Physical GC2145 Captured Image:** [`docs/live_camera_frame.jpg`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/live_camera_frame.jpg)
* **10-Frame Validation Evidence:** [`docs/physical_camera_10frames_evidence.json`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/physical_camera_10frames_evidence.json)
* **Dashboard Tab 1 Screenshot (pH Demo Normalized):** [`docs/DASHBOARD_LIVE_TAB1_PH_DEMO.png`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/DASHBOARD_LIVE_TAB1_PH_DEMO.png)
* **Dashboard Tab 2 Screenshot (Real Frame & Optical Intelligence):** [`docs/DASHBOARD_LIVE_TAB2_CAMERA_FRAME.png`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/DASHBOARD_LIVE_TAB2_CAMERA_FRAME.png)
* **Dashboard Tab 2 Full Rendered View:** [`docs/DASHBOARD_LIVE_TAB2_FULL_VIEW.png`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/DASHBOARD_LIVE_TAB2_FULL_VIEW.png)
* **Dashboard Tab 3 (XAI Modality Attribution):** [`docs/DASHBOARD_LIVE_TAB3_XAI.png`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/DASHBOARD_LIVE_TAB3_XAI.png)
* **Actuator Hardware Log:** [`docs/controlled_actuator_demo_evidence.json`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/controlled_actuator_demo_evidence.json)
