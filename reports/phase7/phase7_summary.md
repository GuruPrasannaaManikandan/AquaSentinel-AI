# Phase 7 Implementation Summary

## 1. Virtual Embedded Components
We have simulated exactly five virtual hardware modules on the ESP32:
1.  **ESP32 Microcontroller Core**
2.  **GPS Receiver**
3.  **Real-Time Clock (RTC)**
4.  **Water Sensors:** Temperature, Salinity/TDS, pH, Turbidity, and Dissolved Oxygen.
5.  **Actuators:** Green LED, Yellow LED, Red LED, Piezo Buzzer, and Relay-controlled Aerator.

---

## 2. Active Model Metric Lineage Reconciliation
To ensure metrics are fully reconciled:
*   **CAML (Freshwater):**
    *   ML Balanced Accuracy: **0.6323**
    *   AIS Balanced Accuracy: **0.8615**
*   **HABSOS (Marine):**
    *   ML Balanced Accuracy: **0.6758**
    *   AIS Balanced Accuracy: **0.5000**

---

## 3. Scientific Limitations & Key Policies
*   **Phase 5 OOD Experiment:** Categorized as **exploratory**. Under validation-locked parameters, OOD coordinates do not trigger the Negative Selection Algorithm's detectors.
*   **HABSOS AIS Limited Reliability:** Preserved HABSOS AIS 0% warning/critical class anomaly recall. The limited-reliability rule routes HABSOS AIS anomalies to `NORMAL` on normal/high ML predictions.
*   **Sensor Fault Exclusion:** Telemetry flagged as `FAULT` by the edge validator is blocked from model entry to prevent data poisoning.

---

## 4. Phase 8 API and Dashboard Integration Recommendation
For Phase 8:
- **Backend Service:** Build a lightweight FastAPI wrapper that connects to the `aquatic_events.db` SQLite store.
- **Data Routes:** Expose REST API endpoints to return JSON records for telemetry logs, validation failures, model decisions, and actuator states.
- **Dashboard UI:** Develop a premium browser-based HTML/CSS/JS dashboard displaying active device markers, real-time telemetry timelines, model confidence distributions, and direct buttons to send manual commands to ESP32 nodes.
