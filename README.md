# IoT-Based Artificial Immune System for Aquatic Ecosystems

An integrated, fault-tolerant monitoring system running parallel supervised machine learning and unsupervised negative selection anomaly detection on simulated ESP32 nodes connected to an evidence-fusion gateway.

---

## 1. Problem Statement & Motivation
Aquatic monitoring systems are highly susceptible to harmful algal blooms and runoffs. Traditional monitoring frameworks rely either on threshold alarms (which miss complex interactions) or supervised machine learning classifiers (which fail on novel, out-of-distribution runoffs). By running a supervised ML model in parallel with an unsupervised Artificial Immune System (AIS) Negative Selection Algorithm (NSA) at the gateway, this architecture classifies known threats and flags unknown anomalies, protecting data integrity via edge validation.

---

## 2. Complete System Architecture
```text
[Virtual Sensors]
       │
       ▼
[Edge Validation FSM]
       │
       ▼ (Valid Telemetry JSON)
[MQTT In-Memory Broker]
       │
       ▼ (Subscribe)
[IoT Gateway Coordinator] 
 ┌─────┴─────────────────────┐
 │                           │
 ▼ (Parallel)                ▼ (Parallel)
[Supervised ML]             [Artificial Immune System (NSA)]
(Weighted RF & LR)          (Unsupervised Novelty Filter)
 └─────┬─────────────────────┘
       │ (Predictions & Anomaly flag)
       ▼
[Evidence-Fusion Engine] ──► [Actuator Commands Relay]
       │ (Final State)
       ▼
[SQLite Event Store] ──► [FastAPI REST / WS API] ──► [Streamlit Dashboard]
```

---

## 3. Dataset Summary
*   **Freshwater (CAML):** Focuses on cyanobacteria blooms. Raw telemetry variables (temperature, pH, turbidity, dissolved oxygen) are checked at the edge by local validation rules, while geographic context (lat, lon, distance to water, region) and cyclic temporal metrics drive the gateway ML and AIS models. Target classes: `1` (Normal) to `5` (Dangerous Bloom).
*   **Marine (HABSOS):** Focuses on Red Tide dinoflagellates. Features include salinity, temperature, and cyclic time variables. Target classes: `1` (Normal) to `4` (Critical Red Tide).

---

## 4. Pipeline & Module Summaries

### 4.1 Preprocessing & ML Pipeline
*   **Imputation & Scalers:** Fitted strictly on training partitions to prevent data leakage.
*   **Cyclic Date Transformations:** Maps calendars to circular sine/cosine coordinates, capturing seasonal bloom trends.
*   **Freshwater Classifier:** Weighted Random Forest baseline champion.
*   **Marine Classifier:** Weighted Logistic Regression baseline champion.

### 4.2 Artificial Immune System (NSA)
*   **Inspiration:** Inspired by T-cell maturation (thymic selection), generating random detector coordinates in the non-self space ($[0, 1]^D$) and destroying those that match self-samples.
*   **Anomaly Classifier:** If incoming scaled readings fall within the radius of any detector, they are flagged as anomalies.

### 4.3 Evidence Fusion Engine
Fuses evidence according to rules:
*   High-confidence ML predictions take priority.
*   Low-confidence ML predictions paired with AIS anomaly flags are routed as `UNKNOWN_ANOMALY` states.
*   Disregards HABSOS AIS anomaly flags on high/medium confidence ML signals to prevent false alarms due to feature space overlap.

### 4.4 Virtual Embedded System & IoT Communication
*   **ESP32 simulator:** Runs FSM states (`BOOT` $\rightarrow$ `CONNECTING` $\rightarrow$ `SENSING` $\rightarrow$ `PUBLISHING` $\rightarrow$ `WAITING`).
*   **Edge Validator:** Rejects inputs with NaNs, infinities, out-of-range sensor readings, or frozen values.
*   **MQTT Transport:** Uses a custom in-memory mock broker supporting full topic wildcards.

### 4.5 Backend & Dashboard
*   **FastAPI Backend:** Exposes REST endpoints (`/health`, `/devices`, `/alerts`) and a WebSocket route (`/ws/live`) to stream real-time updates.
*   **Streamlit UI:** Renders KPI metrics, FSM status badges, ML/AIS diagnostics, time-series charts, and override controls.

---

## 5. Verified Performance Results
Consolidated performance scores locked in the release configuration:
*   **CAML Supervised RF:** Accuracy = **63.23%** | Macro F1 = **0.5243** | Dangerous Recall = **94.80%**
*   **CAML AIS (NSA):** Balanced Accuracy = **86.15%** | Anomaly Recall = **73.48%** | False Positive Rate = **1.19%**
*   **HABSOS Supervised LR:** Accuracy = **67.58%** | Macro F1 = **0.3411** | Dangerous Recall = **0.4873**
*   **HABSOS AIS (NSA):** Balanced Accuracy = **50.00%** | Anomaly Recall = **0.00%** (limitations preserved)

---

## 6. Known Scientific Limitations
1.  Phase 4 model optimization is invalidated due to validation split leaks and is inactive.
2.  The original Phase 5 OOD anomaly experiment is exploratory due to ad-hoc detector radii.
3.  HABSOS AIS is limited to 0% validation anomaly recall due to close feature overlap between normal and bloom marine vectors.
4.  Physical ESP32 microcontrollers, sensors, and actuators are software simulations.

---

## 7. Future Hardware Migration Plan
To deploy on physical hardware:
1.  **ESP32 C++ Sketch:** Replace `sensor_simulator.py` with Arduino/ESP-IDF OneWire and ADC sensor read loops (DS18B20 temp, gravity pH, TDS, and turbidity probes).
2.  **MQTT Broker:** Connect the ESP32 to a physical broker (e.g. Eclipse Mosquitto) using WiFi.
3.  **Probes Calibration:** Perform standard calibration in pH 4/7/10 buffers to mitigate analog drift.

---

## 8. Setup & Execution

### 8.1 Installation
Install the project dependencies:
```bash
pip install -r requirements.txt
```

### 8.2 Running the Full Test Suite
Run the 180-test suite:
```bash
python -m unittest discover tests
```

### 8.3 Running the Live Demo
Start the FastAPI server and Streamlit dashboard in parallel:
```bash
python run_demo.py
```
Open your browser to:
*   **Dashboard UI:** `http://127.0.0.1:8501`
*   **API Documentation:** `http://127.0.0.1:8000/docs`
