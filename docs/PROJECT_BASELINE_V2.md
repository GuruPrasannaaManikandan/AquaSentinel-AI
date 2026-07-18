# Project Baseline - Version 2.0 (Software-First, Hardware-Ready)

*   **Project Title:** AquaSentinel-AI: Real-Time Aquatic Biosurveillance & IoT Gateway
*   **Baseline Version:** 2.4.0
*   **Release Date:** July 19, 2026
*   **Release Status:** Frozen / Release Candidate 1

---

## 1. System Architecture

The project operates as a complete software-first, hardware-ready IoT edge computing pipeline. The flow of data is strictly directed as follows:

```
[Virtual ESP32 Device] ──(Reads)──> [HAL Abstraction] ──(Polls)──> [Virtual Sensors (calibrated)]
         │
         ├──(Scheduled via)──> [RTOS cooperative tasks: SensorTask / CommTask / HealthTask]
         │
         └──(Publishes over)──> [MQTT / TCP Network Link] ──> [Central Broker]
                                                                     │
                                                               (Subscribed by)
                                                                     v
                                                          [FastAPI Gateway Service]
                                                                     │
                                                           [Edge Range Validator]
                                                                     │
                                                           [Features Mapper (Geo)]
                                                                     │
                                                ┌────────────────────┴────────────────────┐
                                                ▼ (In-Distribution)                       ▼ (Fault Bypass)
                                     [ML & AIS Models Pipeline]                  [Sensor Fault State Emitted]
                                                │                                         │
                                                └────────────────────┬────────────────────┘
                                                                     v
                                                          [Evidence Fusion Engine]
                                                                     │
                                                           [EventStore SQLite DB] ──(Broadcast)──> [Dashboard (Streamlit)]
```

---

## 2. Repository Folder Structure

*   `config/`: Exposes centralized configuration maps (`device_config.json`, `final_demo_scenarios.json`).
*   `dashboard/`: Streamlit client dashboard user interfaces (`app.py`).
*   `embedded_device/`: Independently executable device firmware loops (`main.py`).
*   `src/`: Main source modules.
    *   `src/iot/`: Decoupled HAL, Drivers, configuration loaders, event databases, and coordinators.
    *   `src/iot/drivers/`: Concrete virtual sensor and actuator driver interfaces.
    *   `src/fusion/`: Dempster-Shafer evidence combining rules and ML/AIS pipelines.
    *   `src/backend/`: REST services, WebSockets, and gateway handlers.
*   `tests/`: Comprehensive regression checks (`test_embedded_v2.py`, `integration_test_v2.py`, `sat_verification_v2.py`).
*   `models/`: Serialized Random Forest/XGBoost models, scalers, and Artificial Immune System detectors.

---

## 3. Core Subsystems

1.  **Firmware Loop:** Implemented in `ESP32Device` class inside `esp32_device.py`. Manages states (`BOOT` -> `ONLINE` -> `SENSING` -> `PUBLISHING` -> `WAITING` / `ERROR`).
2.  **RTOS Scheduler:** Cooperatively multiplexes tasks by priority using a tick-based task coordinator (`scheduler.py`). Supports message queues (`Queue`) and event flags (`Event`).
3.  **HAL:** Unified interface `HAL` (`hal.py`) which acts as a hardware gateway shielding physical pins and drivers from loop functions.
4.  **Drivers Layer:** Decoupled `BaseSensorDriver` and `BaseActuatorDriver` classes. Virtual implementations map to a physical simulation generator `VirtualEnvironment`.
5.  **MQTT Communication:** `CommunicationLayer` class supporting simulated network joining and `paho-mqtt` networking client routing when mock mode is disabled.
6.  **AI Pipeline:** Mapped in `DecisionPipeline`. Preprocesses geo-sensor telemetry, runs model predictions, scores NSA detector metrics, and combines weights via Dempster-Shafer rules.
7.  **Dashboard:** Streamlit UI presenting live telemetry, historical timeseries charts, alarm logs, and real-time FSM actuator state controls.

---

## 4. Supported Devices & Specifications

### A. Freshwater Device (`AQUA_FRESH_001`)
*   **Ecosystem Context:** Lakes / reservoirs (CAML route).
*   **Sensors:** pH, Turbidity, Dissolved Oxygen, GPS, RTC, ultrasonic distance.
*   **Actuators:** green, yellow, red LEDs, buzzer, pump relay.

### B. Marine Device (`AQUA_MARINE_001`)
*   **Ecosystem Context:** Estuaries / oceans (HABSOS route).
*   **Sensors:** pH, Turbidity, Dissolved Oxygen, Temperature, Salinity, GPS, RTC, distance.
*   **Actuators:** green, yellow, red LEDs, buzzer, pump relay.

---

## 5. Supported Sensors Range & Units

| Sensor Parameter | Unit | Physical Range | Validation Checks |
| --- | --- | --- | --- |
| pH | pH units | 0.0 - 14.0 | Range limits & frozen checks |
| Turbidity | NTU | 0.0 - 500.0 | Range limits & frozen checks |
| Dissolved Oxygen | mg/L | 0.0 - 25.0 | Range limits & frozen checks |
| Temperature | °C | -5.0 - 45.0 | Range limits & frozen checks |
| Salinity | ppt | 0.0 - 50.0 | Range limits & frozen checks |
| Latitude | degrees | -90.0 - 90.0 | GPS Range checks |
| Longitude | degrees | -180.0 - 180.0 | GPS Range checks |

---

## 6. Supported Scenarios Mappings

1.  **NORMAL:** Telemetry is in-distribution, ML outputs safe labels, AIS confirms SELF, and the fusion engine outputs `NORMAL` state (Green LED = ON).
2.  **KNOWN_BLOOM_RISK:** Telemetry exhibits bloom features, ML outputs dangerous label, and fusion engine outputs `WARNING` (Yellow LED = ON, Aerator Pump = ON).
3.  **SENSOR_FAULT:** Bad telemetry is injected (NaN/Inf). The Edge Validator rejects the frame and flags `FAULT`, triggering direct gateway bypass and emitting `SENSOR_FAULT` state (Red LED = ON, Buzzer = ON).
4.  **NETWORK_FAILURE:** Device loses network connectivity, transitioning internally to the offline `ERROR` fallback routine before auto-reconnecting.

---

## 7. Machine Learning & AIS Model Pipeline

*   **Supervised ML Model:** XGBoost / Random Forest classifier. Reads latitude, longitude, DayOfYear, and distance features. Returns predicted class IDs and probability matrices.
*   **Artificial Immune System (AIS):** Negative Selection Algorithm (NSA). Evaluates anomalous distance to trained detectors. Output is `SELF` if distance exceeds anomaly threshold, otherwise `NON-SELF`.
*   **Evidence Fusion:** Combines ML classes and AIS flags via Dempster-Shafer weights, emitting a final state decision (`NORMAL`, `WARNING`, `CRITICAL`, `UNKNOWN_ANOMALY`, or `SENSOR_FAULT`).

---

## 8. MQTT Topic Specifications

*   `aquatic/{device_id}/telemetry` (QoS 0): Telemetry payload containing sensor arrays and FSM states published by the device.
*   `aquatic/{device_id}/status` (QoS 0): Live connection status alerts.
*   `aquatic/{device_id}/command` (QoS 1): Commands sent by the gateway (e.g. `RESTART_DEVICE`).
*   `aquatic/{device_id}/decision` (QoS 0): Combined fusion outputs published by the gateway to sync hardware LED/buzzer states.

---

## 9. API & Endpoints Specifications

*   `GET /health`: Checks system health status.
*   `GET /devices`: Lists all registered devices in the system.
*   `GET /devices/{device_id}/latest`: Returns the latest telemetry frame and decision log.
*   `GET /devices/{device_id}/telemetry`: Retrieves historical telemetry logs.
*   `GET /devices/{device_id}/decisions`: Retrieves historical fusion decisions.
*   `POST /devices/{device_id}/command`: Submits an actuator or system command to the device.
*   `GET /alerts`: Fetches unacknowledged alerts.
*   `POST /alerts/{alert_id}/acknowledge`: Clears a logged alarm.

---

## 10. Database Schema (SQLite EventStore)

*   `telemetry_logs`: Stores time-series data from sensors.
*   `validation_logs`: Logs edge verification outcomes.
*   `fusion_decisions`: Logs ML, AIS, and Evidence Fusion parameters.
*   `actuator_logs`: Stores history of LED, buzzer, and relay states.
*   `alerts`: Stores unacknowledged active system warnings.

---

## 11. Testing & Acceptance Benchmarks

*   **Pytest Unit Cases:** 186 unit tests passing.
*   **Integration Tests:** Decoupled processes connection stability verified in [integration_test_v2.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/tests/integration_test_v2.py).
*   **Stress Performance:** Throughput reaches **19.57 cycles/sec** at average latencies of **51.09 ms**.

---

## 12. Version History

1.  **Version 1.0 (Stable / Frozen):** Initial dataset pipeline, models, and dashboard.
2.  **Version 2.0 (Embedded HAL Refactor):** Added abstraction layers, driver partitions, cooperative task schedulers, configuration interfaces, and automated integration suites.
