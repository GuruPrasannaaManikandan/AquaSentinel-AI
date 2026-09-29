# V5.0 — Comprehensive V4.8.6 → V5 Gap & Opportunity Audit
**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Phase:** Version 5 Architectural Inception & Feasibility Audit  
**Date:** 2026-08-26  
**Status:** Audit Complete — Awaiting Approval Before Implementation  

---

## 1. Executive Summary & V5 Core Mission

The Capstone Project has progressed through five distinct developmental evolutions:
- **V1:** Initial AI/AIS software prototype and exploratory machine learning algorithms.
- **V2:** Embedded firmware architecture, task scheduler, driver abstraction, and initial IoT communication.
- **V3.0–V3.8:** Production-hardened, frozen, deterministic embedded IoT runtime architecture (FSM, scheduler, HAL, MQTT, edge validation).
- **V4.x (V4.1–V4.8.6):** Multimodal AI integration, MobileNetV3-Small computer vision model, temporal validation, camera transport, Dempster-Shafer style fusion, and PlatformIO build closure.
- **V4.8.6 Baseline Status:** Fully verified (314 unit/integration tests passing, clean PlatformIO binary generation, frozen V3.8 files strictly untouched, physical hardware paused).

### The V5 Paradigm Shift
V4.8.6 operates primarily as a **point-in-time multimodal aquatic bloom detection system**. It acquires an observation (sensors + camera), evaluates ML/AIS/CV for that single time instant, and emits a categorical state (`NORMAL`, `WARNING`, `CRITICAL`, `UNKNOWN_ANOMALY`).

**V5 Primary Objective:**
Transform the system from a point-in-time bloom classifier into a:
> **Reliable, Temporal, Explainable, Adaptive Aquatic Ecosystem Intelligence and Early-Warning System.**

This transition must be achieved purely through **software intelligence, mathematical rigor, and architectural extensions** without touching the frozen V3.8 runtime files, without adding physical hardware dependencies, and without introducing unsupportable or fabricated AI claims.

---

## 2. Comprehensive Capability Matrix

| Capability Dimension | V4.8.6 Status | Fully Solved? | Weakness / Limitation in V4.8.6 | V5 Opportunity & Target Scope |
| :--- | :--- | :--- | :--- | :--- |
| **1. Sensor Intelligence** | Boundary checks & basic range checks | 🟡 Partially | Edge validator checks static bounds (-5 to 45°C, 0-14 pH). Cannot detect drift, sudden spikes, or sensor noise. | Dynamic multi-metric sensor quality index ($Q_{sensor}$), statistical noise estimation, and drift tracking. |
| **2. Sensor Quality Assessment** | Binary `OK` / `FAULT` status | 🔴 No | Either valid or faulty; no quantitative reliability metric passed to fusion. | Continuous sensor reliability vector $[0.0, 1.0]$ feeding weighted multimodal fusion. |
| **3. Computer Vision Inference** | MobileNetV3-Small (PyTorch) | 🟢 Yes | Evaluates single isolated frames; cannot detect transient surface reflections, debris, or waves. | Multi-frame temporal smoothing and optical quality score (sharpness/contrast/exposure). |
| **4. Visual Confidence & Quality** | Raw softmax confidence score | 🟡 Partially | Overconfident on out-of-distribution optical noise; lacks image-quality degradation awareness. | Optical Quality Index ($Q_{visual}$) based on Laplacian variance (blur) and histogram entropy. |
| **5. Artificial Immune System** | Static Negative Selection (NSA) | 🟡 Partially | Detectors are static hyperspheres generated at initialization; no adaptation, memory, or context. | Clonal selection / immune memory for recurring environmental patterns; dynamic detector sensitivity. |
| **6. Multimodal Fusion** | Rule-based decision table | 🟡 Partially | Hard-coded discrete decision matrix; treats evidence as unweighted binary/categorical inputs. | Reliability-weighted evidential fusion: $m(State) = f(E_{sensor}, E_{visual}, E_{AIS}, E_{temporal})$. |
| **7. Temporal Reasoning** | Single-frame timestamp check | 🔴 No | System evaluates $t_0$ in isolation; cannot detect gradual temperature warming or sustained pH rise. | Rolling-window trajectory analysis ($N=10$ cycles): Rate-of-Change ($\Delta X / \Delta t$), trend slope, and persistence. |
| **8. Risk Prediction & Forecasting** | Current-state detection only | 🔴 No | System only flags bloom when thresholds are already crossed; zero proactive early-warning window. | Multi-tier Risk Evolution: `NORMAL` $\rightarrow$ `WATCH` $\rightarrow$ `EARLY_WARNING` $\rightarrow$ `HIGH_RISK` $\rightarrow$ `BLOOM_CONFIRMED`. |
| **9. Explainability (XAI)** | Pre-formatted string templates | 🟡 Partially | Text explanation repeats reason code; cannot attribute mathematical percentage contributions. | Transparent Feature & Modality Contribution attribution (Sensor: 45%, Vision: 35%, AIS: 20%). |
| **10. Historical Intelligence** | SQLite raw table logging | 🟡 Partially | Logs rows to SQLite; does not compute historical baselines, rolling averages, or diurnal variance. | In-memory cyclic telemetry ring buffer + automated baseline modeling (rolling mean/std per device). |
| **11. System Dashboard** | Streamlit (ML/AIS/Telemetry) | 🟡 Partially | Dashboard lacks camera frame feed, visual confidence dials, temporal trend meters, and XAI panels. | Comprehensive Intelligence Dashboard with visual stream, early-warning gauge, and attribution waterfall. |
| **12. Fault Handling & Fallback** | Sensor fault bypass & camera drop | 🟢 Yes | Robust fallback to sensor-only mode, but handles degradation abruptly rather than gracefully. | Graceful evidence discounting: dynamic re-weighting when a modality degrades or loses sync. |
| **13. Ecosystem Recovery** | Actuators reset on normal | 🟡 Partially | Instantaneous state drop from CRITICAL to NORMAL on a single normal frame (hysteresis absent). | State Recovery Hysteresis: requires $K$ consecutive confirmed normal observations to clear alarms. |

---

## 3. Forensic Analysis of Candidate V5 Areas (V5.1 – V5.10)

### 3.1 V5.1 — Advanced Sensor Intelligence & Quality Assessment
- **What V4.8.6 Does:** `EdgeValidator` (`src/iot/edge_validation.py`) enforces static physical limits (e.g., pH $\in [0, 14]$) and checks if the last 5 readings are identical (frozen sensor check).
- **The Gap:** Natural aquatic sensors drift gradually due to bio-fouling or calibration loss. An electrode reading pH 7.0 for 3 hours, then jumping to pH 9.8 in 10 seconds without high turbidity or temperature change, is physically implausible. V4.8.6 accepts it because 9.8 is within $[0, 14]$.
- **V5 Architectural Solution:**
  Introduce an **Edge Sensor Quality & Plausibility Filter** that computes:
  1. *Rate-of-Change Plausibility Check:* $\left|\frac{x_t - x_{t-1}}{\Delta t}\right| \le \text{MaxPhysicalRate}$.
  2. *Statistical Z-Score / Moving-Median Deviation:* Flags readings $>3\sigma$ from the local moving median.
  3. *Cross-Sensor Consistency:* Physical coupling checks (e.g., photosynthetic bloom causes simultaneous daytime pH rise and DO saturation rise; an isolated pH spike with crashing DO indicates sensor failure, not a bloom).
  4. *Sensor Quality Score ($Q_{sensor} \in [0.0, 1.0]$):* Emitted alongside telemetry to guide fusion weighting.

### 3.2 V5.2 — Advanced Computer Vision Intelligence & Optical Quality
- **What V4.8.6 Does:** MobileNetV3-Small classifies incoming JPEG frames into `NORMAL_WATER`, `ALGAL_BLOOM`, or `TURBID_DISCOLORATION`.
- **The Gap:** The model receives frames regardless of lighting, lens water droplets, sun glint, or severe motion blur. An out-of-focus frame can yield false bloom classifications or low confidence. Moreover, an observation evaluates only the instantaneous frame without checking if the previous frame saw the same pattern.
- **V5 Architectural Solution:**
  1. *Optical Quality Metric ($Q_{visual}$):* Compute Laplacian variance (sharpness score) and luminance distribution (underexposed/overexposed check) in `ImagePreprocessor`. If $Q_{visual} < \tau_{blur}$, classify frame as `OPTICAL_DEGRADED` rather than passing corrupted pixels to the neural network.
  2. *Temporal Frame Buffer ($K=3$ frames):* Require spatial-temporal consistency across $K$ successive frames before elevating visual evidence to `BLOOM_EVIDENCE`.

### 3.3 V5.3 — Temporal Environmental Intelligence & Trend Detection
- **What V4.8.6 Does:** Evaluates each observation strictly at timestamp $t$. No memory of historical trajectories exists in the inference path.
- **The Gap:** Algal blooms do not materialize instantaneously in a single 10-second polling cycle. They exhibit distinct biological and physico-chemical lead indicators:
  - Phase 1 (Incubation): Rising water temperature ($+1.5^\circ\text{C}$ over hours) + sustained sunlight.
  - Phase 2 (Proliferation): Accelerating pH rise (carbon dioxide uptake via photosynthesis) + steady DO rise.
  - Phase 3 (Surface Manifestation): Turbidity climb + surface scum detection.
- **V5 Architectural Solution:**
  Implement a lightweight **Temporal Trend Engine** operating on a sliding window of the last $N=12$ telemetry points:
  - Linear regression slope ($m = \frac{\Delta y}{\Delta t}$) for key eutrophication markers.
  - Cumulative anomaly persistence counters ($C_{persist}$).
  - Detection of *gradual degradation* versus *instantaneous spikes*.

### 3.4 V5.4 — Adaptive Artificial Immune System (AIS)
- **What V4.8.6 Does:** Static Negative Selection Algorithm (`src/ais/negative_selection.py`) with 100 fixed spherical detectors generated during `fit()`.
- **The Gap:** The detector set is completely immutable at runtime. It has no immunological memory: an anomaly observed 50 times in succession is treated with the exact same surprise as an anomaly seen for the very first time. Furthermore, HABSOS marine validation recall is documented as 0% due to static spherical detector limitations in high-dimensional tabular spaces.
- **V5 Architectural Solution:**
  1. *Primary vs. Secondary Immune Response (Memory Cells):* When a non-self antigen is repeatedly observed and verified, instantiate a designated **Memory Detector** with a reinforced affinity radius. Secondary responses trigger faster and with higher confidence.
  2. *Adaptive Affinity Radius:* Dynamically adjust the matching radius based on local feature density, suppressing false alarms in noisy boundary regions.
  3. *Deterministic Baseline Guarantee:* Maintain a frozen base detector core to ensure complete reproducibility, layering adaptive memory as a deterministic runtime cache.

### 3.5 V5.5 — Advanced Multimodal Fusion & Evidential Weighting
- **What V4.8.6 Does:** `FusionEngine._fuse_multimodal_table()` uses a hard-coded `if-elif` ladder matching discrete strings (`NORMAL`, `WARNING`, `CRITICAL`, `BLOOM_EVIDENCE`, etc.).
- **The Gap:** It does not account for continuous confidence or source reliability. If the camera has $Q_{visual} = 0.95$ and high confidence, its evidence should weigh significantly higher than when the camera lens is fogged ($Q_{visual} = 0.30$). Similarly, if water sensors exhibit high noise, fusion should dynamically down-weight sensor evidence.
- **V5 Architectural Solution:**
  Upgrade to an **Evidential Fusion Architecture** (Dempster-Shafer / Weighted Belief Combination):
  - Modality Basic Belief Assignments (BBA):
    $$m_{sensor}(\text{Threat}) = w_{sensor} \cdot C_{sensor} \cdot Q_{sensor}$$
    $$m_{visual}(\text{Threat}) = w_{visual} \cdot C_{visual} \cdot Q_{visual}$$
    $$m_{temporal}(\text{Threat}) = w_{temporal} \cdot P_{trend}$$
  - The fusion mathematically combines independent mass functions, providing continuous confidence and transparent conflict resolution.

### 3.6 V5.6 — Risk Prediction & Multi-Tier Early Warning
- **What V4.8.6 Does:** Categorizes into 4 operational states: `NORMAL`, `WARNING`, `CRITICAL`, `UNKNOWN_ANOMALY`.
- **The Gap:** No distinction between an active critical emergency (massive bloom underway) and an *emerging threat trajectory* (early warning 30 minutes prior).
- **V5 Architectural Solution:**
  Formalize a **5-Tier Ecological Threat Progression**:
  1. `NORMAL`: All parameters within baseline bounds, zero trajectory risk.
  2. `WATCH`: Environmental precursors detected (water warming, slight pH upward drift), but no physical bloom.
  3. `EARLY_WARNING`: Statistically significant upward rate-of-change across $\ge 2$ indicators; visual pre-bloom discoloration detected.
  4. `HIGH_RISK`: Precursors confirmed by AIS anomaly and visual evidence; bloom emergence imminent.
  5. `BLOOM_CONFIRMED`: Multi-modal confirmation of full algal bloom manifestation.

### 3.7 V5.7 — Explainable AI (XAI) & Attribution
- **What V4.8.6 Does:** Emits a fixed string sentence from a dictionary lookup (e.g., `"Multimodal confirmation: Sensor evidence (WARNING) and camera visual evidence..."`).
- **The Gap:** Operators cannot see *why* the system concluded 85% risk. Which feature drove the decision? Was it pH? Was it optical greenness? Was it AIS detector match #4?
- **V5 Architectural Solution:**
  Generate a **Structured Evidence Attribution Vector**:
  ```json
  {
    "risk_score": 0.88,
    "state": "HIGH_RISK",
    "attribution": {
      "ph_elevation": 0.32,
      "turbidity_trend": 0.24,
      "visual_bloom_confidence": 0.28,
      "ais_novelty": 0.16
    },
    "key_factors": [
      "pH climbed 0.8 units over last 30 minutes",
      "Camera detected surface green scum (conf=0.91, quality=0.88)",
      "Non-self antigen matched 3 memory detectors"
    ]
  }
  ```

### 3.8 V5.8 — Ecosystem Digital State & Historical Intelligence
- **What V4.8.6 Does:** Logs telemetry and decisions into SQLite tables (`telemetry_logs`, `fusion_decisions`, `alerts`).
- **The Gap:** Historical data is strictly passive. The gateway does not query historical data to dynamically understand baseline diurnal cycles (e.g., daytime vs. nighttime dissolved oxygen cycles).
- **V5 Architectural Solution:**
  Implement a **Digital State Baseline Engine** within `EventStore`:
  - Maintains rolling 24-hour baseline distributions (mean, median, standard deviation) for each monitored site.
  - Automatically contextualizes live readings against site-specific historical baselines rather than static global constants.

### 3.9 V5.9 — Advanced Intelligence Dashboard
- **What V4.8.6 Does:** Streamlit app with 4 tabs: Live Telemetry, Subsystem Intelligence (ML/AIS/State), Historical Charts, Alerts.
- **The Gap:** The dashboard is completely blind to Computer Vision! No camera frames are rendered, no optical quality is shown, no temporal trend gauges exist, and no attribution waterfall is plotted.
- **V5 Architectural Solution:**
  Upgrade Streamlit dashboard:
  - Add **Camera Visual Feed Panel** with latest captured frame, detected bounding boxes, and $Q_{visual}$ gauge.
  - Add **Early-Warning & Trajectory Radar** showing multi-tier risk progression.
  - Add **Explainability Attribution Waterfall** showing exact percentage contributions of each sensor and vision modality.

### 3.10 V5.10 — End-to-End Forensic Verification Suite
- **What V4.8.6 Does:** `pytest` (314 tests) and `run_phase9.py` (244 tests) test static inputs, boundary conditions, and mock scenarios.
- **The Gap:** No integration test verifies temporal sequence evolution over time (e.g., simulating 20 successive timestamps showing a gradual bloom development, followed by mitigation and recovery).
- **V5 Architectural Solution:**
  Construct a **Temporal Sequence Verification Suite**:
  - Test Suite 1: Clean ecosystem baseline sequence (20 cycles).
  - Test Suite 2: Gradual eutrophication trajectory (Incubation $\rightarrow$ Watch $\rightarrow$ Early Warning $\rightarrow$ Bloom).
  - Test Suite 3: Transient artifact rejection (single-frame glare/leaf ignored by temporal consistency filter).
  - Test Suite 4: Sensor failure with visual recovery (bad pH, clean vision $\rightarrow$ graceful degradation).
  - Test Suite 5: Full recovery cycle (mitigation applied, parameters normalize, state steps down with hysteresis).

---

## 4. Dataset Realism & Constraints Analysis (Rule 5 Compliance)

To comply with **Rule 5 (Dataset Realism)**, an explicit forensic audit of available repository data was conducted:

| Dataset / Source | Format & Content | True Capabilities Supported | Hard Limitations (Must NOT Claim) |
| :--- | :--- | :--- | :--- |
| **CAML (Freshwater)** | Static tabular rows: lat, lon, date, time, severity, distance_to_water. | Geographic risk context, spatial-temporal seasonality risk. | **NO continuous sensor streaming.** CAML features do not include water chemistry probes; cannot train physical sensor time-series models from CAML alone. |
| **HABSOS (Marine)** | Historical field observation records: lat, lon, cellcount, water temp, salinity. | Coastal background risk, salinity/temperature baseline distributions. | **Sparse, sporadic sampling.** Samples are days/weeks apart; cannot support continuous sub-minute temporal forecasting. |
| **Visual Dataset (`data/cv_processed`)** | 438 total images (303 train, 68 val, 67 test) across 3 classes. | Optical categorization: `NORMAL_WATER`, `ALGAL_BLOOM`, `TURBID_DISCOLORATION`. | **Static photographs, not continuous video streams.** Temporal video models (e.g. 3D-CNN, ConvLSTM) cannot be trained on this data. Temporal reasoning must operate on consecutive frame inference outputs. |
| **Simulated IoT Telemetry (`SensorSimulator`)** | Deterministic continuous 5-sensor stream (`temp`, `ph`, `turb`, `salinity`, `DO`). | Continuous time-series, rate-of-change simulation, drift injection, scenario testing. | **Synthetic physics-based generation.** Must remain transparently classified as simulated benchmark telemetry. |

**Scientific Realism Conclusion:**
Any V5 capability claiming "deep learning temporal forecasting directly trained on raw multi-year sensor streams" would be fraudulent because the datasets do not contain continuous time-series.  
Therefore, V5's temporal intelligence must be implemented as a **physically-grounded, rule-and-statistics based Temporal Trend Engine** operating on rolling live observation windows, contextualized by CAML/HABSOS regional models and verified via scenario simulation.

---

## 5. Official V5 Architecture Blueprint

```
═══════════════════════════════════════════════════════════════════════════════════════
                   AQUASENTINEL-AI VERSION 5 SYSTEM ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════════════════

   [ Edge Sensing Node (ESP32-WROOM-32 / V3.8 Frozen Runtime) ]
        │ Telemetry JSON (Temp, pH, Turb, Sal, DO, GPS)
        ▼
 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │ V5.1 ADVANCED SENSOR QUALITY & PLAUSIBILITY ENGINE                              │
 │  ├── Rate-of-Change Filter (|ΔX/Δt| ≤ MaxPhysical)                              │
 │  ├── Dynamic Z-Score / Moving-Median Deviation Check                            │
 │  ├── Cross-Sensor Physico-Chemical Consistency Validator                       │
 │  └── Output: Validated Telemetry + Sensor Quality Vector Q_sensor [0.0 - 1.0]   │
 └─────────────────────────┬───────────────────────────────────────────────────────┘
                           │
   [ Optical Node (ESP32-CAM) ]
        │ JPEG Frame Payload + Provenance Timestamp
        ▼
 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │ V5.2 ADVANCED OPTICAL QUALITY & TEMPORAL VISION ENGINE                          │
 │  ├── Laplacian Blur / Sharpness Metric + Exposure Histogram (Q_visual)          │
 │  ├── Frozen MobileNetV3-Small Inference Engine (models/cv/)                     │
 │  ├── Multi-Frame Optical Temporal Buffer (K=3 Temporal Consistency)             │
 │  └── Output: VisualEvidence (State, Confidence, Bboxes, Q_visual)               │
 └─────────────────────────┬───────────────────────────────────────────────────────┘
                           │
                           ▼
 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │ V5.3 TEMPORAL ENVIRONMENTAL TREND & TRAJECTORY ENGINE                           │
 │  ├── Rolling Window Buffer (N=12 cycles)                                        │
 │  ├── Trend Slopes (ΔpH/Δt, ΔTurb/Δt, ΔTemp/Δt)                                  │
 │  ├── Cumulative Threat Persistence Counter (C_persist)                          │
 │  └── Output: TemporalTrajectoryVector (RateOfChange, Persistence, LeadIndicator)│
 └─────────────────────────┬───────────────────────────────────────────────────────┘
                           │
                           ▼
 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │ V5.4 ADAPTIVE ARTIFICIAL IMMUNE SYSTEM (AIS)                                    │
 │  ├── Frozen Base Negative Selection Detector Core (V3.8 Repro Baseline)         │
 │  ├── Adaptive Secondary Immune Response Memory Cache                            │
 │  ├── Local Density-Aware Dynamic Affinity Radius                                │
 │  └── Output: AISEvidence (AnomalyScore, MatchedDetectors, MemoryRecallStatus)   │
 └─────────────────────────┬───────────────────────────────────────────────────────┘
                           │
                           ▼
 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │ V5.5 RELIABILITY-WEIGHTED MULTIMODAL EVIDENTIAL FUSION                          │
 │  ├── Modality Belief Mass Functions (Sensor, Vision, Temporal, AIS)             │
 │  ├── Graceful Degradation & Evidential Discounting Matrix                       │
 │  ├── 5-Tier Threat Classifier: NORMAL → WATCH → EARLY_WARNING → HIGH_RISK → BLOOM│
 │  └── Output: FusedSystemDecision (FinalState, RiskScore, Confidence)            │
 └─────────────────────────┬───────────────────────────────────────────────────────┘
                           │
                           ▼
 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │ V5.6 EXPLAINABLE AI (XAI) ATTRIBUTION & RECOVERY ENGINE                         │
 │  ├── Modality & Feature Attribution Breakdown (Percentage Weights)              │
 │  ├── Human-Readable Root-Cause Lead Indicator Extraction                        │
 │  ├── State Recovery Hysteresis Gate (K_recover consecutive normal cycles)       │
 │  └── Output: ExplainableDecisionContract + Actuator Control Directives          │
 └─────────────────────────┬───────────────────────────────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
 ┌──────────────────────┐      ┌──────────────────────────────────────────────────┐
 │ V5.8 DIGITAL STATE   │      │ V5.9 COMPREHENSIVE INTELLIGENCE DASHBOARD        │
 │  HISTORICAL STORAGE  │      │  ├── Real-time Optical Stream & Visual Bounding  │
 │  (SQLite Baselines,  │      │  ├── Multi-Tier Threat Progression Radar         │
 │   Diurnal Variance,  │      │  ├── XAI Attribution Waterfall Chart             │
 │   Event Timeline)    │      │  ├── Interactive Historical Trend Visualizer     │
 └──────────────────────┘      │  └── Direct Actuator Overrides & Alert Ack       │
                               └──────────────────────────────────────────────────┘
```

---

## 6. Recommended V5 Milestone Roadmap (V5.1 – V5.6)

Rather than arbitrarily creating 10 independent versions, the forensic audit reveals that capabilities group logically and cohesively into **six structured milestones**:

### Milestone V5.1 — Advanced Sensor Quality & Edge Intelligence
- **Focus:** Sensor quality scoring ($Q_{sensor}$), physical rate-of-change validation, cross-sensor consistency checks, and outlier mitigation.
- **Artifacts:** `src/iot/sensor_quality.py`, updated schemas in `src/backend/schemas.py`.

### Milestone V5.2 — Advanced Optical Quality & Multi-Frame Vision
- **Focus:** Image quality estimation ($Q_{visual}$ via Laplacian blur and luminance check), multi-frame temporal consistency filter ($K=3$ consecutive frames).
- **Artifacts:** `src/cv/optical_quality.py`, update `src/cv/visual_detection.py`.

### Milestone V5.3 — Temporal Environmental Intelligence & Early-Warning Engine
- **Focus:** Sliding-window trend slopes ($\Delta X/\Delta t$), cumulative persistence counters, 5-tier threat progression (`NORMAL` $\rightarrow$ `WATCH` $\rightarrow$ `EARLY_WARNING` $\rightarrow$ `HIGH_RISK` $\rightarrow$ `BLOOM_CONFIRMED`).
- **Artifacts:** `src/fusion/temporal_engine.py`, `src/fusion/risk_classifier.py`.

### Milestone V5.4 — Adaptive Artificial Immune System (AIS Memory & Sensitivity)
- **Focus:** Secondary immune response memory cells, adaptive local affinity radius, repeated anomaly recognition while preserving frozen baseline reproducibility.
- **Artifacts:** `src/ais/adaptive_ais.py`.

### Milestone V5.5 — Reliability-Weighted Multimodal Evidential Fusion & XAI
- **Focus:** Dynamic evidence mass weighting, graceful degradation on missing/degraded modalities, transparent percentage-based attribution vector generation, state recovery hysteresis.
- **Artifacts:** `src/fusion/evidential_fusion.py`, `src/fusion/explainability.py`.

### Milestone V5.6 — Digital State, Dashboard Evolution & End-to-End Forensic Verification
- **Focus:** 24-hour diurnal rolling baseline engine in `EventStore`, complete Streamlit dashboard visual upgrade (camera feed, XAI waterfall, risk progression gauge), comprehensive sequence integration test suite.
- **Artifacts:** `dashboard/app.py`, `tests/test_v5_end_to_end.py`, `docs/V5_FINAL_ACCEPTANCE_REPORT.md`.

---

## 7. Non-Negotiable Boundaries & Rules for V5

1. **Frozen V3.8 Protection:**
   The following 5 files remain strictly **READ-ONLY / FROZEN**:
   - `src/iot/esp32_device.py`
   - `src/iot/communication.py`
   - `src/iot/scheduler.py`
   - `src/iot/hal.py`
   - `src/iot/actuators.py`
2. **Preserve V4 Capabilities:**
   The MobileNetV3-Small binary model (`aquatic_bloom_mobilenetv3.pt`), `TemporalValidator`, MQTT schemas, and existing REST API endpoints must remain fully operational. All existing 314 pytest tests must continue passing without regressions.
3. **No Fabricated Data or Deep Temporal Networks:**
   Temporal trend analysis must rely on sliding-window statistical and physical rate equations, NOT black-box LSTM/Transformers that cannot be trained on the available static datasets.
4. **Physical Hardware Remains Paused:**
   No physical wiring, bench testing, or hardware flashing is introduced in V5.

---

## 8. V5 Completion & Acceptance Criteria

V5 will be declared officially complete when:
1. **Sensor Quality Metric:** All telemetry emits an objective $Q_{sensor} \in [0.0, 1.0]$, correctly flagging synthetic drift, noise, and physical implausibility.
2. **Optical Quality Metric:** All camera frames evaluate $Q_{visual}$, filtering blurred/dark frames before neural inference.
3. **Temporal Early-Warning Window:** The system successfully triggers `EARLY_WARNING` and `WATCH` states prior to full bloom threshold crossing during simulated eutrophication sequences.
4. **Transparent XAI Attribution:** Every decision payload provides numerical modality contributions summing to 100% with traceable physical justifications.
5. **Recovery Hysteresis:** The system requires $K \ge 3$ consecutive normal cycles to recover from `HIGH_RISK` to `NORMAL`, eliminating alarm chattering.
6. **Dashboard Integration:** The Streamlit dashboard actively displays camera frames, visual confidence, temporal trends, and XAI attribution.
7. **Regression Zero:** 100% pass rate on all legacy unit tests (V1–V4.8.6) plus comprehensive V5 temporal sequence test suites.

---
*V5.0 Architectural Gap & Opportunity Audit complete. Awaiting user review and authorization before proceeding to implementation.*
