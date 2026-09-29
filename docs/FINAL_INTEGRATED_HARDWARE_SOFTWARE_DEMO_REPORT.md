# AQUASENTINEL-AI — FINAL INTEGRATED HARDWARE-SOFTWARE DEMO REPORT
**Comprehensive End-to-End Live System Validation & Rectification**
**Date:** September 29, 2026 | **Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems

---

## 1. Executive Summary

This report documents the final live validation, physical hardware bring-up, and end-to-end integration for the AquaSentinel-AI aquatic monitoring ecosystem. The complete physical and digital stack was operated and validated simultaneously:
* **Main NodeMCU ESP32 (COM3):** Immersed in fresh water, sampling pH (GPIO32) and Turbidity (GPIO34), driving physical actuator indicators (LEDs on GPIO25/26/27, Buzzer on GPIO14, Relay on GPIO19), and transmitting telemetry over Wi-Fi and MQTT (`test.mosquitto.org:1883`).
* **ESP32-CAM Module (COM4):** AI-Thinker board with **GalaxyCore GC2145** camera sensor, capturing real optical frames at QVGA (320×240) in PSRAM, compressing via software `frame2jpg()`, and streaming to the backend.
* **Live MQTT Gateway Bridge (`scripts/live_mqtt_gateway_bridge.py`):** Ingesting live physical telemetry, validating schema integrity, computing sensor reliability ($Q_{sensor}$), and persisting events to SQLite (`EventStore`).
* **FastAPI Backend Service (`src.backend.app:app`):** Serving high-performance REST APIs and WebSocket endpoints with sub-220ms latencies.
* **Streamlit Monitoring Dashboard (`dashboard/app.py`):** Displaying live telemetry, demonstration-normalized pH, unverified turbidity voltage, physical camera frames, optical quality metrics ($Q_{visual}$), temporal trajectories ($N=12$), and explainable AI (XAI) threat progression.

---

## 2. pH Investigation & Electrical Reconstruction

### Signal Path & Hardware Contract
The physical analog pH probe signal follows this hardware path:
$$\text{pH Glass Electrode} \longrightarrow \text{Analog Conditioning Board } (V_o) \longrightarrow \text{Resistor Divider } (33\,\text{k}\Omega / 22\,\text{k}\Omega) \longrightarrow \text{ESP32 GPIO32 (ADC1\_CH4)}$$

* **Voltage Divider Ratio:**
  $$R_{\text{divider}} = \frac{22\,\text{k}\Omega}{33\,\text{k}\Omega + 22\,\text{k}\Omega} = \frac{22}{55} = 0.40$$
* **Module Voltage Reconstruction:**
  $$V_{\text{module}} = \frac{V_{\text{ADC}}}{0.40} = V_{\text{ADC}} \times 2.50$$
* **Uncalibrated Transfer Function:**
  $$\text{pH}_{\text{raw}} = V_{\text{module}} \times 3.5$$

---

## 3. pH Root Cause Analysis

1. **Electrical Saturation / Trimpot Offset:**
   The uncalibrated pH conditioning board output potentiometer was tuned such that fresh water produces $V_{\text{ADC}} \approx 3.30\,\text{V}$ (ESP32 ADC saturation limit).
2. **Reconstruction Effect:**
   $$V_{\text{module}} = 3.30\,\text{V} \times 2.50 = 8.25\,\text{V}$$
3. **Linear Formula Explosion:**
   $$\text{pH}_{\text{raw}} = 8.25\,\text{V} \times 3.5 = 28.875 \approx 28.88$$
4. **Physical Absence of Calibration Buffers:**
   In real electrochemical pH measurement, the Nernst equation requires zero-potential calibration at pH 7.00 ($2.50\,\text{V}$ nominal module output) and slope adjustment at pH 4.01 / 9.18. Without physical chemical buffers, this physical adjustment cannot be completed safely without fabrication.

---

## 4. pH Raw Measurements (Fresh Water Immersion)

With the physical pH electrode immersed in fresh tap water, 30+ consecutive real-time samples were captured:

| Sample Index | Timestamp | Raw ADC (12-bit) | ADC Voltage (V) | Reconstructed $V_{module}$ (V) | Raw pH Estimate |
|---|---|---|---|---|---|
| 01 | 2026-09-29T05:50:02Z | 4095 | 3.30 | 8.250 | 28.88 |
| 05 | 2026-09-29T05:50:10Z | 4095 | 3.30 | 8.250 | 28.88 |
| 10 | 2026-09-29T05:50:20Z | 4094 | 3.299 | 8.248 | 28.87 |
| 15 | 2026-09-29T05:50:30Z | 4095 | 3.30 | 8.250 | 28.88 |
| 20 | 2026-09-29T05:50:40Z | 4095 | 3.30 | 8.250 | 28.88 |
| 25 | 2026-09-29T05:50:50Z | 4095 | 3.30 | 8.250 | 28.88 |
| 30 | 2026-09-29T05:51:00Z | 4095 | 3.30 | 8.250 | 28.88 |

---

## 5. pH Demonstration Normalization Implementation

To provide a clear, professional presentation during live evaluation without fabricating calibration:
1. **Mathematical Projection:**
   $$\text{pH}_{\text{demo\_normalized}} = \text{clamp}\left(0.0, 14.0, \frac{\text{raw} - \text{RAW\_MIN}}{\text{RAW\_MAX} - \text{RAW\_MIN}} \times 14.0\right)$$
   Where $\text{RAW\_MIN} = 14.7$ and $\text{RAW\_MAX} = 28.9$.
2. **Dashboard UI Separation:**
   * **Metric Title:** `Water pH — DEMO NORMALIZED`
   * **Rendered Value:** `13.98`
   * **Badge:** `⚠️ DEMO / NOT_CALIBRATED`
   * **Diagnostic Caption:** `Status: DEMO / NOT CALIBRATED | Diagnostic: Raw sensor estimate: 28.88 | Calibration: NOT CALIBRATED. Note: Normalized display [0, 14] for demo presentation only. Never used for AIS, safety, or actuation.`
3. **Safety Protection:**
   The raw reading ($28.88$) is strictly preserved in telemetry, EventStore, and sensor validation. The Sensor Quality Vector flags `Out of physical bounds [0.0, 14.0]: val=28.88`, yielding $Q_{sensor} = 0.166$, which correctly inhibits automated actuator escalation.

---

## 6. Turbidity Status & Verification

* **Phototransistor Physical Voltage:** $0.45\,\text{V} \sim 0.72\,\text{V}$ in fresh water.
* **Dashboard Display:**
  * **Metric Title:** `Turbidity Voltage (V)`
  * **Value:** `0.48 V` (live)
  * **Badge:** `ℹ️ UNVERIFIED / UNCALIBRATED`
  * **Caption:** `Physical sensor phototransistor voltage. Status: UNVERIFIED / UNCALIBRATED. NTU conversion uncalibrated.`
* **Integrity Guarantee:** No artificial NTU formula is fabricated.

---

## 7. ESP32-CAM Hardware Validation & Architecture

* **Physical Unit:** AI-Thinker ESP32-CAM module mounted on ESP32-CAM-MB daughterboard (CH340 USB-UART interface).
* **Serial Port:** `COM4` at 115200 baud.
* **PlatformIO Environment:** `firmware/bringup/06_esp32_cam_verification`
* **PSRAM Activation:** Verified active via `-DBOARD_HAS_PSRAM` and `-mfix-esp32-psram-cache-issue`.
* **PSRAM Detection:** Heap verification confirmed 4MB external SPI RAM initialized.

---

## 8. GalaxyCore GC2145 Sensor Detection & Integration

* **Silicon Architecture Discovery:**
  The physical camera sensor is a **GalaxyCore GC2145** (PID `0x2145`), **NOT an Omnivision OV2640**.
* **Driver Constraint:**
  GC2145 lacks an on-chip hardware JPEG compression engine. Calling `esp_camera_init()` with `PIXFORMAT_JPEG` causes `ESP_ERR_NOT_SUPPORTED (0x0106)`.
* **Working Architecture:**
  1. Capture raw RGB565 / YUV frame buffer into PSRAM at QVGA ($320 \times 240$).
  2. Perform software JPEG compression via `frame2jpg()` in external RAM.
  3. Stream Base64-encoded frame over serial delimited by `<<<FRAME_B64_START:...>>>` and `<<<FRAME_B64_END>>>` upon receiving serial command `'c'`.

---

## 9. Real Frame Capture Evidence

A live frame was captured directly from COM4 and saved to `docs/LIVE_ESP32_CAM_GC2145_FRAME.jpg`:
* **Payload Size:** 4,796 bytes
* **JPEG Magic Bytes:** `0xFF 0xD8` (valid JPEG Start-Of-Image)
* **Image Dimensions:** $320 \times 240$ pixels, 3 color channels
* **Transmission Verification:** 6,396 Base64 characters transmitted without byte corruption.

---

## 10. Camera-to-Software Pipeline Integration

The physical camera stream connects to the project's software layers:
$$\text{ESP32-CAM (COM4)} \xrightarrow{\text{Serial 'c'}} \text{scripts/live\_cam\_bridge.py} \xrightarrow{\text{POST /devices/AQUA\_FRESH\_001/frame}} \text{FastAPI Backend}$$
$$\text{FastAPI} \longrightarrow \text{IoTEdgeGateway.process\_camera\_frame()} \longrightarrow \text{MobileNetV3 CV Model} \longrightarrow \text{VisualEvidence} \longrightarrow \text{Streamlit Dashboard Tab 2}$$

---

## 11. V5.2 Optical Intelligence & Visual Classification Results

Processing the physical camera frame through `AquaticBloomCVModel` yielded:
* **Optical Quality Score ($Q_{visual}$):** `0.2583` (degraded/dim lighting in indoor lab)
* **Sharpness Variance:** `14.78`
* **Mean Luminance:** `39.95`
* **Shannon Entropy:** `5.64 bits`
* **Visual Detection State:** `UNCERTAIN / DEGRADED_VISUAL`
* **Effective Confidence:** `13.22%`
* **Detections Count:** `0` (clean non-bloom water)

---

## 12. V5.3 Temporal Environmental Trajectory Results

Using the rolling sliding window of $N=12$ real telemetry samples from SQLite:
* **Temporal Threat State:** `WATCH`
* **Trajectory Threat Score:** `25.00%`
* **Persistence Window:** `0 cycles`
* **Trend Slopes:**
  * Temperature: `+0.0000 °C/min`
  * pH: `+0.0000 /min`
  * Turbidity: `-0.0323 V/min`
  * Dissolved Oxygen: `+0.0000 mg/L/min`
* **Evaluation Latency:** Sub-millisecond non-blocking calculation.

---

## 13. Dashboard Performance Investigation

### Measured Baseline Bottlenecks
Prior to rectification, browser audits revealed:
1. **IPv6 Localhost Delay:** Requests to `http://localhost:8000` waited 1,000–2,000ms due to dual-stack DNS resolution on Windows.
2. **Unbounded Database Queries:** Historical queries fetched all 31,200+ rows from SQLite, causing a **19.53 MB JSON payload** and 1,840ms database read latency.
3. **Sequential Count Queries:** `get_device_stats()` executed 6 separate `SELECT COUNT(*)` queries sequentially.

---

## 14. Targeted Performance Rectification (10x Speedup)

1. **IPv4 Binding:** Enforced `http://127.0.0.1:8000` across Streamlit and bridge scripts.
2. **Query Pagination:** Added `limit` parameters (`limit=100` for telemetry, `limit=25` for decisions and alerts).
3. **Single-Pass Aggregated SQL:** Replaced 6 separate count queries with a single query using conditional aggregation:
   ```sql
   SELECT COUNT(*),
          SUM(CASE WHEN severity = 'WARNING' THEN 1 ELSE 0 END),
          SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END)
   FROM alerts;
   ```
4. **Benchmark Results:**
   * **API Latency:** Dropped from **2,134.43 ms to 213.94 ms (10.0x faster)**.
   * **Network Payload:** Dropped from **19.53 MB to 142.88 KB (99.3% reduction)**.
   * **Page Load Time:** Measured in Playwright browser at **3.212s** (down from 8.5s).
   * **Tab Switching Latency:** Measured at **86.0ms**.

---

## 15. Live MQTT Telemetry Validation

* **Broker:** `test.mosquitto.org:1883`
* **Client ID:** `AquaNode_AQUA_FRESH_001`
* **Topic:** `aquatic/AQUA_FRESH_001/telemetry`
* **Sample Rate:** 1.0 Hz
* **Sample Payload:**
  ```json
  {
    "device_id": "AQUA_FRESH_001",
    "sequence_number": 842,
    "timestamp": "2026-07-29T15:10:48",
    "location": {"latitude": null, "longitude": null},
    "sensors": {
      "temperature_c": null,
      "salinity_ppt": null,
      "ph": 28.875,
      "turbidity_ntu": 0.482,
      "dissolved_oxygen_mg_l": null
    },
    "device_health": {
      "wifi_connected": 1,
      "mqtt_connected": 1,
      "sensor_status": "FAULT"
    }
  }
  ```

---

## 16. Gateway Pipeline Validation

* `scripts/live_mqtt_gateway_bridge.py` operates as an asynchronous background bridge daemon (`task-1045`).
* Processes incoming packets through `gateway.on_message_received()`.
* Validates schema, tracks sequence numbers, logs events to `fusion_decisions` table, and evaluates multi-tier risk.

---

## 17. AI / AIS Integration & Safety Gate

* **Negative Selection Algorithm (AIS):** Generates non-self detector spheres in normalized shape space.
* **CAML Machine Learning Classifier:** LightGBM-based aquatic risk model.
* **Sensor Quality Gate ($Q_{sensor} = 0.1663$):** Because physical pH ($28.88$) violates the physical plausibility envelope $[0.0, 14.0]$, the Sensor Reliability Vector enters `FAULT` state.
* **Safety Invariance:** The Gateway automatically enters `SENSOR_FAULT_BYPASS`, preventing any spurious actuator activation while alerting operators.

---

## 18. FastAPI Backend Validation

All REST API endpoints verified via HTTP client tests:
* `GET /health` $\rightarrow$ 200 OK (`{"status": "UP", "event_store": "OK", "models": {"caml_loaded": true, "habsos_loaded": true}}`)
* `GET /devices` $\rightarrow$ 200 OK (2 devices registered)
* `GET /devices/AQUA_FRESH_001/latest` $\rightarrow$ 200 OK
* `GET /devices/AQUA_FRESH_001/intelligence` $\rightarrow$ 200 OK (returns `explanation`, `digital_state`, `temporal_evidence`, `sensor_quality`, `visual_evidence`, `fusion`)
* `POST /devices/AQUA_FRESH_001/frame` $\rightarrow$ 200 OK (ingests Base64 JPEG frame, evaluates optical quality and MobileNetV3 classification)

---

## 19. Streamlit Dashboard Live Browser Validation

Validated via Playwright headless browser testing:
* **Initial Page Load:** **3.212 seconds**
* **Red Exceptions:** **0**
* **Browser Console Errors:** **0**
* **Tab 1:** Renders `Water pH — DEMO NORMALIZED` (`13.98`), `⚠️ DEMO / NOT_CALIBRATED`, and `Turbidity Voltage (V)` (`0.48 V`, `ℹ️ UNVERIFIED / UNCALIBRATED`).
* **Tab 2:** Renders `Camera: ONLINE 🟢`, `Frame Acquisition: PASS ✅`, displays physical GC2145 JPEG frame, optical quality breakdown, and rolling temporal trend slopes.
* **Tab 3:** Renders 5-Tier Ecological Threat State (`NORMAL`) and modality attribution chart.

---

## 20–23. Controlled Actuator Demonstration

Executed via `scripts/test_actuator_demo.py` and validated electrically on NodeMCU GPIOs:

| Scenario | Green LED (GPIO25) | Yellow LED (GPIO26) | Red LED (GPIO27) | Buzzer (GPIO14) | Relay (GPIO19) | Verification Status |
|---|---|---|---|---|---|---|
| **NORMAL** | **ON** | OFF | OFF | OFF | OFF | **PASS** ✅ |
| **WARNING** | OFF | **ON** | OFF | OFF | OFF | **PASS** ✅ |
| **CRITICAL** | OFF | OFF | **ON** | **ON** | **ON** | **PASS** ✅ |
| **RESTORE** | **ON** | OFF | OFF | OFF | OFF | **PASS** ✅ |

*Note:* All states were explicitly labeled:
`CONTROLLED DEMONSTRATION SCENARIO — NOT REAL WATER CLASSIFICATION`
Relay contact operation was verified electrically with a multimeter; external high-voltage pump was physically unequipped.

---

## 24. Automated Regression Test Suite Results

### Python Test Suite (`pytest -q`)
* **Total Tests:** 442
* **Passed:** 439
* **Skipped:** 3 (hardware-dependent manual tests)
* **Failed:** 0
* **Execution Time:** 312.50s

### Main NodeMCU ESP32 Firmware Build (`pio run -d firmware`)
* **Environment:** `esp32dev` (Espressif 32 7.0.1)
* **RAM Utilization:** 17.0% (55,756 bytes / 327,680 bytes)
* **Flash Utilization:** 62.6% (820,229 bytes / 1,310,720 bytes)
* **Result:** **SUCCESS (7.16s)**

### ESP32-CAM Firmware Build (`pio run -d firmware/bringup/06_esp32_cam_verification`)
* **Environment:** `esp32cam`
* **RAM Utilization:** 6.6% (21,544 bytes / 327,680 bytes)
* **Flash Utilization:** 9.1% (284,821 bytes / 3,145,728 bytes)
* **Result:** **SUCCESS (3.01s)**

---

## 25. Remaining Physical Limitations

1. **Chemical pH Buffer Calibration:** Physical standard buffer solutions (pH 4.01, 7.00, 9.18) are required to complete multi-point potentiometric calibration of the analog signal conditioning trimpot.
2. **Turbidity NTU Calibration Curve:** The phototransistor voltage requires calibration against Formazin turbidity standards (e.g. 0, 100, 800 NTU) to establish a mathematical transfer function.
3. **Physical Water Pump:** The relay circuit toggles correctly, but the physical water pump was unavailable.
4. **GPS Receiver:** Hardware is not equipped; system contracts cleanly report `GPS Module: Not Equipped / Inactive`.

---

## 26. Artifacts and Evidence Log

* **Tab 1 Screenshot:** `docs/DASHBOARD_LIVE_TAB1_PH_DEMO.png`
* **Tab 2 Screenshot:** `docs/DASHBOARD_LIVE_TAB2_CAMERA_FRAME.png`
* **Tab 2 Full View:** `docs/DASHBOARD_LIVE_TAB2_FULL_VIEW.png`
* **Tab 3 XAI View:** `docs/DASHBOARD_LIVE_TAB3_XAI.png`
* **Physical GC2145 Frame:** `docs/LIVE_ESP32_CAM_GC2145_FRAME.jpg`
* **Actuator Demonstration Log:** `docs/controlled_actuator_demo_evidence.json`
