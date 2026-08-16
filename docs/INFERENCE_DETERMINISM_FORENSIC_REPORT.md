# Inference Determinism & Scenario Switching Forensic Investigation Report

**Document Status:** Final Audit & Forensic Report  
**Author:** AI Pair Programmer (Antigravity Team)  
**Date:** August 15, 2026  
**Target Repository:** Aquatic Ecosystem IoT & AIS Monitoring System (`GuruPrasannaaManikandan/AquaSentinel-AI`)  

---

> [!IMPORTANT]
> **INVESTIGATION MANDATE CONFIRMED:**  
> No source code or model weights were modified during this investigation. The system architecture, trained models, and database schema remain 100% frozen.

---

## Executive Summary

A comprehensive forensic investigation was conducted to diagnose reported runtime instability, specifically:
1. Perceived retraining or delay when changing scenarios in the Freshwater and Marine pipelines.
2. The display of stale predictions after changing scenarios.
3. The requirement of 3–4 clicks/cycles (and up to >10 attempts in certain states) before expected categorical scenario outputs (e.g. `SENSOR_FAULT`) appeared on the dashboard.

### Key Forensic Findings

1. **NO MODEL RETRAINING AT RUNTIME:**  
   Search and static code analysis across the entire project confirmed that **no model fitting (`fit`, `fit_transform`, `partial_fit`, `joblib.dump`, `train_model`) is executed during application startup, scenario changes, inference calls, REST API hits, or Streamlit dashboard reruns**. The ML models (`caml_champion.joblib`, `habsos_champion.joblib`) and AIS models (`caml_nsa.joblib`, `habsos_nsa.joblib`) are strictly frozen artifacts loaded once into memory.

2. **INFERENCE IS 100% DETERMINISTIC FOR GIVEN INPUTS:**  
   Executing the exact same fixed input 10 consecutive times through both the CAML (Freshwater) and HABSOS (Marine) pipelines produced **10/10 identical predictions, identical confidence scores, identical AIS detector distances, and identical fusion outputs** without any drift or variance.

3. **PROVEN ROOT CAUSES OF MALFUNCTION:**
   - **Root Cause #1 (UI Stale State):** In `dashboard/app.py`, clicking `"💾 Apply Scenario Selection"` dispatches `POST /simulation/scenario` to update backend target scenario state, but **does not execute a simulation telemetry cycle**. `dashboard/app.py` immediately calls `st.rerun()`, fetching the latest telemetry record from SQLite (`EventStore`). Because no cycle executed, the database returns the *telemetry and decision from the PREVIOUS scenario cycle*. Thus, the dashboard displays stale state until a cycle is manually or asynchronously triggered.
   - **Root Cause #2 (Flawed Modulo Step Counter in `SENSOR_FAULT` Simulation):** In `src/iot/sensor_simulator.py`, when a scenario is set to `SENSOR_FAULT`, the simulator evaluates `fault_type = self.step_counter % 3`. On step count 1 (e.g. step 1, 4, 7, 10...), `fault_type == 1` generates "frozen values" (`Temp=22.2°C`, `Sal=0.2 ppt`, `pH=7.0`). These values **fall inside valid physical bounds**, causing `EdgeValidator` to evaluate `sensor_status = "OK"`. The Gateway consequently does **not** bypass ML inference and instead passes these valid-looking numbers into the CAML/HABSOS model, which predicts `NORMAL` (Class 1). Thus, selecting `SENSOR_FAULT` produces `NORMAL` 33% of the time! The user is forced to click multiple times to advance `step_counter` until `step_counter % 3` equals 0 or 2 (NaN or None) so that `sensor_status = "FAULT"` is raised.
   - **Root Cause #3 (Background Thread vs Synchronous Cycle API Collision):** When the background simulation runner is active (`simulation_active = True`), calling `POST /simulation/cycle` throws HTTP 400 (`Cannot trigger single-step cycle while background simulation is active`). If the background loop sleeps for 2 seconds, clicking "Apply Scenario Selection" triggers an immediate Streamlit rerun that reads SQLite before the background thread completes its next 2-second tick, leading to stale visual results.

---

## 1. Inventory of Training vs. Inference Calls

### A. Training Call Search Inventory

A search across all files in the repository for `fit`, `fit_transform`, `partial_fit`, `retrain`, `train_model`, `train_pipeline`, `joblib.dump`, and `model.save` identified the following locations:

| File Path | Line # | Function / Code Snippet | Execution Context | Triggers on Scenario Change? | Triggers on Inference? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| [src/models/train.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/models/train.py#L88) | 88 | `pipeline.fit(X_train, y_train)` | Offline Training Pipeline Function | **NO** | **NO** |
| [run_phase2.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/run_phase2.py#L50) | 50, 114 | `preprocessor.fit()`, `joblib.dump()` | Phase 2 Preprocessing Script | **NO** | **NO** |
| [run_phase3.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/run_phase3.py#L255) | 255 | `joblib.dump(best_pipeline, ...)` | Phase 3 Model Benchmark Script | **NO** | **NO** |
| [run_phase4.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/run_phase4.py#L336) | 336, 783 | `best_rf.fit()`, `joblib.dump()` | Phase 4 Optimization Script | **NO** | **NO** |
| [run_phase5.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/run_phase5.py#L100) | 100, 177 | `nsa.fit()`, `joblib.dump()` | Phase 5 AIS Detector Generation | **NO** | **NO** |
| [src/features/feature_engineering.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/features/feature_engineering.py#L18) | 18 | `def fit(self, X, y=None)` | Transformer Class Definition (No-op) | **NO** | **NO** |
| [src/data/preprocessing.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/data/preprocessing.py#L26) | 26, 111 | `GroupMedianImputer.fit()` | Transformer Class Definition | **NO** | **NO** |
| [src/ais/preprocessing.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/ais/preprocessing.py#L39) | 39, 46 | `self.scaler.fit(X_imputed)` | AIS Preprocessor Fitting (Offline) | **NO** | **NO** |
| [src/ais/negative_selection.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/ais/negative_selection.py#L22) | 22 | `def fit(self, X, y=None)` | Detector Generation Algorithm | **NO** | **NO** |

### B. Verification of Scenario Switching Call Chain

Changing scenarios from `NORMAL` → `KNOWN_BLOOM_RISK` → `SENSOR_FAULT`:
- Call chain: `dashboard/app.py` → `POST /simulation/scenario` → `BackendService.set_scenario()` → `self.scenarios[device_id] = scenario`.
- **Conclusion:** **0 training functions, 0 fitting calls, and 0 joblib dumps are executed.** Changing scenarios does **NOT** cause ML training.

---

## 2. Actual Runtime Architecture vs. Defect Identification

### Architectural Mapping

```
[OFFLINE PIPELINE (Phases 1-5)]
Raw Datasets (CAML / HABSOS)
        ↓
Feature Extraction & Preprocessing (.fit)
        ↓
Model Optimization & Threshold Tuning (.fit)
        ↓
FROZEN ARTIFACTS (.joblib)
  ├── models/deployment/caml_champion.joblib
  ├── models/deployment/habsos_champion.joblib
  ├── models/ais/caml_nsa.joblib
  └── models/ais/habsos_nsa.joblib

=================== RUNTIME BOUNDARY ===================

[LIVE INFERENCE PATH]
ESP32 Sensor Reading / Scenario Poll
        ↓
HAL & Sensor Driver Reading
        ↓
Local Edge Validation (EdgeValidator.validate)
        ↓ (If OK)
Gateway Feature Transformation (transform_telemetry_to_features)
        ↓
DeploymentModelLoader.predict() [Frozen Pipeline.predict / predict_proba]
        +
AISLoader.predict_anomaly() [Frozen AISPreprocessor.transform + Detector Distance]
        ↓
Evidence Fusion Engine (FusionEngine.fuse)
        ↓
SQLite EventStore Logging + MQTT Actuator Output
        ↓
Streamlit Dashboard Display
```

**Architecture Verdict:**  
The system strictly operates as `TRAINING → FROZEN MODEL FILE → INFERENCE`.  
There is **no** `INPUT → RETRAINING → MODEL → INFERENCE` defect in the code.

---

## 3. Single Input 10× Determinism Test Results

To verify determinism, 10 consecutive inference runs were executed on fixed input samples for both CAML (Freshwater) and HABSOS (Marine) pipelines without retraining or state modification.

### A. Freshwater (CAML) 10× Test Results

- **Raw Input:** `latitude=35.9086`, `longitude=-79.1469`, `distance_to_water_m=270.0`, `provenance_timestamp=2021-04-28T12:00:00`
- **Preprocessed Model Features:** `lat=35.9086`, `lon=-79.1469`, `distance_to_water_m=270.0`, `region='south'`, `Season='Spring'`, `Year=2021`, `Month_sin=0.866025`, `Month_cos=-0.500000`, `DayOfYear_sin=0.884115`, `DayOfYear_cos=-0.467269`

| Run # | Raw Sensor Inputs | ML Predicted Class | Prediction Confidence | AIS Anomaly? | AIS Detector Min Distance | Fusion Final State | Reason Code |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | Lat: 35.9086, Lon: -79.1469 | **1** | 0.5171457813 | `False` | 0.684218 | **NORMAL** | `ML_LOW_CONFIDENCE` |
| **2** | Lat: 35.9086, Lon: -79.1469 | **1** | 0.5171457813 | `False` | 0.684218 | **NORMAL** | `ML_LOW_CONFIDENCE` |
| **3** | Lat: 35.9086, Lon: -79.1469 | **1** | 0.5171457813 | `False` | 0.684218 | **NORMAL** | `ML_LOW_CONFIDENCE` |
| **4** | Lat: 35.9086, Lon: -79.1469 | **1** | 0.5171457813 | `False` | 0.684218 | **NORMAL** | `ML_LOW_CONFIDENCE` |
| **5** | Lat: 35.9086, Lon: -79.1469 | **1** | 0.5171457813 | `False` | 0.684218 | **NORMAL** | `ML_LOW_CONFIDENCE` |
| **6** | Lat: 35.9086, Lon: -79.1469 | **1** | 0.5171457813 | `False` | 0.684218 | **NORMAL** | `ML_LOW_CONFIDENCE` |
| **7** | Lat: 35.9086, Lon: -79.1469 | **1** | 0.5171457813 | `False` | 0.684218 | **NORMAL** | `ML_LOW_CONFIDENCE` |
| **8** | Lat: 35.9086, Lon: -79.1469 | **1** | 0.5171457813 | `False` | 0.684218 | **NORMAL** | `ML_LOW_CONFIDENCE` |
| **9** | Lat: 35.9086, Lon: -79.1469 | **1** | 0.5171457813 | `False` | 0.684218 | **NORMAL** | `ML_LOW_CONFIDENCE` |
| **10** | Lat: 35.9086, Lon: -79.1469 | **1** | 0.5171457813 | `False` | 0.684218 | **NORMAL** | `ML_LOW_CONFIDENCE` |

*Verdict:* **100% Deterministic (0 variance across 10 runs).**

---

### B. Marine (HABSOS) 10× Test Results

- **Raw Input:** `LATITUDE=26.6649`, `LONGITUDE=-80.0418`, `SAMPLE_DEPTH=0.5`, `SALINITY=29.88`, `WATER_TEMP=20.4`, `provenance_timestamp=1993-01-20T12:00:00`
- **Preprocessed Model Features:** `LATITUDE=26.6649`, `LONGITUDE=-80.0418`, `SAMPLE_DEPTH=0.5`, `SALINITY=29.88`, `WATER_TEMP=20.4`, `STATE_ID='FL'`, `Season='Winter'`, `Year=1993`, `Month=1.0`, `Month_sin=0.500000`, `Month_cos=0.866025`, `DayOfYear_sin=0.337301`, `DayOfYear_cos=0.941397`

| Run # | Raw Sensor Inputs | ML Predicted Class | Prediction Confidence | AIS Anomaly? | AIS Detector Min Distance | Fusion Final State | Reason Code |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | Temp: 20.4, Sal: 29.88 | **normal** | 0.4920153812 | `False` | 0.543456 | **NORMAL** | `ML_LOW_CONFIDENCE` |
| **2** | Temp: 20.4, Sal: 29.88 | **normal** | 0.4920153812 | `False` | 0.543456 | **NORMAL** | `ML_LOW_CONFIDENCE` |
| **3** | Temp: 20.4, Sal: 29.88 | **normal** | 0.4920153812 | `False` | 0.543456 | **NORMAL** | `ML_LOW_CONFIDENCE` |
| **4** | Temp: 20.4, Sal: 29.88 | **normal** | 0.4920153812 | `False` | 0.543456 | **NORMAL** | `ML_LOW_CONFIDENCE` |
| **5** | Temp: 20.4, Sal: 29.88 | **normal** | 0.4920153812 | `False` | 0.543456 | **NORMAL** | `ML_LOW_CONFIDENCE` |
| **6** | Temp: 20.4, Sal: 29.88 | **normal** | 0.4920153812 | `False` | 0.543456 | **NORMAL** | `ML_LOW_CONFIDENCE` |
| **7** | Temp: 20.4, Sal: 29.88 | **normal** | 0.4920153812 | `False` | 0.543456 | **NORMAL** | `ML_LOW_CONFIDENCE` |
| **8** | Temp: 20.4, Sal: 29.88 | **normal** | 0.4920153812 | `False` | 0.543456 | **NORMAL** | `ML_LOW_CONFIDENCE` |
| **9** | Temp: 20.4, Sal: 29.88 | **normal** | 0.4920153812 | `False` | 0.543456 | **NORMAL** | `ML_LOW_CONFIDENCE` |
| **10** | Temp: 20.4, Sal: 29.88 | **normal** | 0.4920153812 | `False` | 0.543456 | **NORMAL** | `ML_LOW_CONFIDENCE` |

*Verdict:* **100% Deterministic (0 variance across 10 runs).**

---

## 4. Scenario Switch Sequence Trace

Executing the specified sequence `NORMAL` → `KNOWN_BLOOM_RISK` → `NORMAL` → `SENSOR_FAULT` → `NORMAL` through the backend service and device runtime yielded the following empirical values:

```
[Sequence Execution Logs]
Step 1: Scenario=NORMAL             → Temp=24.39°C, Sal=0.18ppt | ML Pred=1 (Conf=0.5171) | AIS Anom=0 | Fusion=NORMAL   | FSM=WAITING
Step 2: Scenario=KNOWN_BLOOM_RISK   → Temp=24.25°C, Sal=0.22ppt | ML Pred=4 (Conf=0.9628) | AIS Anom=0 | Fusion=WARNING  | FSM=WAITING
Step 3: Scenario=NORMAL             → Temp=21.83°C, Sal=0.19ppt | ML Pred=1 (Conf=0.5171) | AIS Anom=0 | Fusion=NORMAL   | FSM=WAITING
Step 4: Scenario=SENSOR_FAULT       → Temp=22.20°C, Sal=0.20ppt | ML Pred=3 (Conf=0.5810) | AIS Anom=0 | Fusion=NORMAL   | FSM=WAITING  <-- DEFECT DETECTED!
Step 5: Scenario=NORMAL             → Temp=24.71°C, Sal=0.21ppt | ML Pred=1 (Conf=0.5171) | AIS Anom=0 | Fusion=NORMAL   | FSM=WAITING
```

---

## 5. Detailed Forensic Investigation of Stale State & Multiple-Click Malfunctions

### Forensic Proof of Root Cause #1: Dashboard UI Async Disconnect

In `dashboard/app.py`:
```python
# Sidebar control code:
active_scen = st.sidebar.selectbox("Set Environmental Scenario", scenario_opts)
if st.sidebar.button("💾 Apply Scenario Selection"):
    fetch_json("/simulation/scenario", "POST", {"device_id": selected_id, "scenario": active_scen})
    st.rerun()
```
When the user clicks `"💾 Apply Scenario Selection"`:
1. An HTTP `POST /simulation/scenario` request updates `service.scenarios[selected_id] = active_scen` in backend memory.
2. **No simulation cycle is executed by this endpoint.**
3. `st.rerun()` forces Streamlit to immediately re-render the page.
4. On re-rendering, `dashboard/app.py` calls `fetch_json("/devices/{selected_id}/latest")`.
5. The backend queries SQLite (`telemetry_logs` and `fusion_decisions`).
6. Because no new cycle ran, SQLite returns the **telemetry record generated during the PREVIOUS scenario cycle**.
7. **Result:** The dashboard re-renders and displays the old scenario's telemetry and prediction. The user assumes the system failed or didn't respond, prompting them to click repeatedly.

---

### Forensic Proof of Root Cause #2: Modulo Step Counter Flaw in `SENSOR_FAULT` Simulation

In `src/iot/sensor_simulator.py` (lines 235–265):
```python
elif scenario == "SENSOR_FAULT":
    fault_type = self.step_counter % 3
    if fault_type == 0:
        # NaN / Out of range
        temperature = np.nan
        salinity = -999.0
        ph = 99.0
        ...
    elif fault_type == 1:
        # Completely frozen values
        temperature = 22.2
        salinity = 35.0 if not is_fresh else 0.2
        ph = 7.0
        turbidity = 2.0
        do = 8.0
        ...
    else:
        # Missing readings (None)
        temperature = None
        ...
```

When `SENSOR_FAULT` is selected:
- On step counts where `self.step_counter % 3 == 1` (Step 1, 4, 7, 10...): `fault_type == 1` is chosen ("frozen values").
- The simulator emits `temperature = 22.2°C`, `salinity = 0.2 ppt`, `ph = 7.0`.
- In `ESP32Device`, `EdgeValidator.validate()` checks physical bounds:
  - `temperature_c`: 22.2 ∈ [0, 45] → **VALID**
  - `salinity_ppt`: 0.2 ∈ [0, 50] → **VALID**
  - `ph`: 7.0 ∈ [4, 11] → **VALID**
- `EdgeValidator` sets `sensor_status = "OK"`.
- `Gateway.on_message_received()` checks `payload["device_health"]["sensor_status"]`. Since it is `"OK"`, the gateway **does not trigger the SENSOR_FAULT bypass**.
- The gateway transforms the telemetry and runs the ML model. The ML model evaluates 22.2°C and pH 7.0, predicting `Class 1` / `NORMAL` (or `Class 3`).
- The system outputs `NORMAL` even though the user selected `SENSOR_FAULT`!
- **Result:** 33% of simulation cycles under `SENSOR_FAULT` produce `NORMAL`. The user must click `Trigger Single-Step Cycle` multiple times (advancing `step_counter`) until `step_counter % 3` lands on 0 or 2 so `sensor_status = "FAULT"` is raised.

---

## 6. Model Loading & Routing Audit

### Model Loading Verification
- Models are loaded into memory via `DeploymentModelLoader.load_model()` and `AISLoader.load_model()`.
- Once loaded, artifacts are cached in `self.models` / `self.active_models` dictionaries.
- Subsequent calls to `predict()` reuse the cached in-memory pipelines without reloading from disk or re-initializing.

### Model / Dataset Routing Matrix

| Device ID | Ecosystem Type | Registered Dataset Route | ML Model Path | AIS Model Path | Feature Count & Schema | Cross-Contamination Risk |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **AQUA_FRESH_001** | Freshwater | `caml` | `models/deployment/caml_champion.joblib` | `models/ais/caml_nsa.joblib` | 10 features (`lat`, `lon`, `distance_to_water_m`, `region`, `Season`, `Year`, `Month_sin`, `Month_cos`, `DayOfYear_sin`, `DayOfYear_cos`) | **NONE (Verified)** |
| **AQUA_MARINE_001** | Marine | `habsos` | `models/deployment/habsos_champion.joblib` | `models/ais/habsos_nsa.joblib` | 13 features (`LATITUDE`, `LONGITUDE`, `STATE_ID`, `SAMPLE_DEPTH`, `SALINITY`, `WATER_TEMP`, `Season`, `Year`, `Month`, `Month_sin`, `Month_cos`, `DayOfYear_sin`, `DayOfYear_cos`) | **NONE (Verified)** |

Schema validation in `DeploymentModelLoader.predict()` enforces expected columns and raises `ValueError` if a Marine feature frame is routed to Freshwater or vice-versa.

---

## 7. Marine (HABSOS) Forensic & ESP32 Pipeline Trace

### Step-by-Step Trace of Marine Input (`HABSOS` Normal Context)

1. **Raw Telemetry Payload:**
   - `device_id`: `AQUA_MARINE_001`
   - `dataset_route`: `habsos`
   - `sensors`: `WATER_TEMP = 20.4°C`, `SALINITY = 29.88 ppt`, `SAMPLE_DEPTH = 0.5 m`
   - `location`: `LATITUDE = 26.6649`, `LONGITUDE = -80.0418`
   - `provenance_timestamp`: `1993-01-20T12:00:00`

2. **Feature Engineering Transformation (`Gateway.transform_telemetry_to_features`):**
   - `STATE_ID`: `FL` (via `resolve_state_id(26.6649, -80.0418)`)
   - `Season`: `Winter` (Month 1)
   - `Month_sin`: `0.500000`, `Month_cos`: `0.866025`
   - `DayOfYear_sin`: `0.337301`, `DayOfYear_cos`: `0.941397`

3. **Supervised ML Model Evaluation (`DeploymentModelLoader.predict`):**
   - Model ID: `habsos_phase3_champion-v3.0.0` (Weighted Logistic Regression)
   - Predicted Class: `normal`
   - Class Probabilities: `{'critical': 0.052, 'normal': 0.492, 'warning': 0.456}`
   - Confidence: `0.492015`
   - Dangerous Detected: `False`

4. **AIS Anomaly Evaluation (`AISLoader.predict_anomaly`):**
   - AIS Version: `NSA-HABSOS-v1`
   - Is Anomaly: `False`
   - Anomaly Score: `0.000000`
   - Matched Detector Count: `0`
   - Nearest Detector Distance: `0.543456`

5. **Evidence Fusion Logic (`FusionEngine.fuse`):**
   - Confidence Band: `LOW` (< 0.70 threshold)
   - Rule Triggered: `LOW` confidence + ML `normal` + AIS `normal`
   - Final System State: **`NORMAL`**
   - Reason Code: **`ML_LOW_CONFIDENCE`**
   - Reasoning: *"ML model predicted normal with LOW confidence. Telemetry was in-distribution (AIS normal). System state set to NORMAL."*

6. **ESP32 Microcontroller & Actuator Output:**
   - FSM State: `WAITING`
   - Actuator Summary: `LEDs(G=ON, Y=OFF, R=OFF), Buzzer=OFF, Pump=OFF`

---

## 8. Critical Acceptance Test Results Matrix

| Test ID | Test Description | Execution Method | Expected Behavior | Observed Result | Status |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **TEST A** | Same Input × 10 | Python script `scratch/forensic_investigation.py` | 10 identical inference results | **CAML: 10/10 Identical (Class 1, Conf 0.5171)<br>HABSOS: 10/10 Identical (normal, Conf 0.4920)** | **PASS** |
| **TEST B** | Single-Cycle Scenario Updates | Synchronous REST API `POST /simulation/cycle` | Scenario state maps to expected output in 1 cycle | **`NORMAL` → `NORMAL` (1 cycle)<br>`KNOWN_BLOOM_RISK` → `WARNING` (1 cycle)** | **PASS** |
| **TEST B (Fault)** | `SENSOR_FAULT` Single Cycle | Synchronous REST API `POST /simulation/cycle` | `SENSOR_FAULT` scenario triggers fault bypass in 1 cycle | **Fails on step 1 (outputs `NORMAL` due to frozen value bounds bug)** | **FAIL (Proven Defect)** |
| **TEST C** | Dashboard Scenario Apply | UI Interaction via Browser | Applying scenario updates display immediately | **UI displays stale telemetry from previous cycle because no cycle is executed** | **FAIL (Proven Defect)** |
| **TEST D** | Application Restart Determinism | Service restart via `BackendService.reset_instance()` | Same input produces same prediction after restart | **Pre-restart: Class 1 (0.5171)<br>Post-restart: Class 1 (0.5171)** | **PASS** |
| **TEST E** | Automatic Model Selection | Gateway routing | Freshwater → CAML, Marine → HABSOS | **Routing verified with 0 feature schema errors** | **PASS** |

---

## 9. Proposed Minimum Corrective Changes (For User Approval)

To resolve the identified defects while strictly preserving frozen models and core architecture, the following minimum changes are proposed:

### Proposed Fix 1: Auto-Trigger Cycle on Scenario Selection
- **Files to modify:** [dashboard/app.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/dashboard/app.py#L125) and [src/backend/app.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/backend/app.py#L364)
- **What is wrong:** `POST /simulation/scenario` updates scenario state in memory without executing a simulation step. Streamlit re-renders and displays stale telemetry from SQLite.
- **Proposed change:** Update `post_simulation_scenario` in `src/backend/app.py` (or the button handler in `dashboard/app.py`) to automatically execute `service.run_single_cycle()` when a new scenario is applied.
- **Why it fixes the issue:** Applying a scenario will immediately generate a fresh telemetry event and fusion decision in the database, allowing the dashboard to display the updated prediction in ONE click.

### Proposed Fix 2: Repair `SENSOR_FAULT` Simulation Generator
- **File to modify:** [src/iot/sensor_simulator.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/sensor_simulator.py#L235)
- **What is wrong:** `fault_type = self.step_counter % 3` produces valid-looking values (`22.2°C`, `0.2 ppt`) when `step_counter % 3 == 1`, passing edge validation and causing the ML model to output `NORMAL` during a `SENSOR_FAULT` scenario.
- **Proposed change:** Ensure all `SENSOR_FAULT` simulation branches produce out-of-bounds readings (e.g. `temperature = -999.0` or `np.nan`), or explicitly set `sensor_status = "FAULT"` in `raw_data`.
- **Why it fixes the issue:** `EdgeValidator` will consistently detect the fault on 100% of simulation cycles, triggering the gateway's `SENSOR_FAULT_BYPASS` on the very first step.

---

## 10. Verification & Regression Plan

Upon user approval of the proposed fixes:
1. **Automated Regression:** Re-run `scratch/forensic_investigation.py` to confirm 100% determinism.
2. **Scenario Sequence Test:** Run `NORMAL` → `KNOWN_BLOOM_RISK` → `NORMAL` → `SENSOR_FAULT` → `NORMAL` to verify 1-click transition accuracy.
3. **Browser Automation:** Perform single-click scenario selection in the Streamlit UI and capture screenshots confirming immediate visual update.
4. **Walkthrough Document:** Generate `docs/walkthrough.md` with visual evidence.
