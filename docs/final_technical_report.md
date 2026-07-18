# Final Technical Report: IoT-Based Artificial Immune System for Aquatic Ecosystems

## Abstract
Aquatic ecosystems are increasingly threatened by harmful algal blooms (HABs) and chemical runoffs. Traditional monitoring frameworks rely on either supervised machine learning (ML) models—which struggle with out-of-distribution (OOD) novel anomalies—or simple threshold checks. This paper presents an integrated IoT and Artificial Immune System (AIS) architecture that combines supervised classification with an unsupervised Negative Selection Algorithm (NSA) running on a transparent, rules-based evidence-fusion gateway. The system validates incoming telemetry at the edge, routes predictions in real-time, logs transitions to an event store, and exposes metrics via a REST/WebSocket API and Streamlit dashboard. 

---

## 1. Introduction
Real-time environmental monitoring is essential for preserving public health and aquatic life. While supervised models predict known hazards (e.g., specific dinoflagellate concentrations), they fail when encountering novel conditions. An Artificial Immune System (AIS), modeled after biological self/non-self discrimination, provides an effective parallel defense by flagging anomalous patterns without requiring labeled out-of-distribution training sets.

## 2. Problem Statement
Supervised classifiers are vulnerable to data contamination and novel environmental states. If an unrepresented runoff occurs, a traditional classifier may assign it a high-confidence, incorrect class. Additionally, noisy or corrupt sensor inputs (NaNs/infinities) can destabilize inference models, demanding robust edge-level sanitization and transparent fusion logic.

## 3. Objectives
*   Develop an ESP32 microcontroller and sensor software simulation.
*   Deploy baseline supervised classifiers for freshwater and marine datasets.
*   Implement an unsupervised Negative Selection Algorithm (NSA) anomaly filter.
*   Construct a rules-based Evidence-Fusion Engine to resolve parallel predictions.
*   Implement a REST/WebSocket API and interactive dashboard for real-time telemetry rendering.

## 4. Literature/Technical Background
Negative Selection Algorithms (NSA), inspired by T-cell maturation, generate random detectors in the non-self space and discard any that match self-samples. In IoT networks, running NSA alongside supervised ML models creates a parallel defense system: the ML model handles known threats while the NSA handles unknown anomalies.

## 5. Datasets
*   **CAML (Freshwater)**: Geographic and temporal contextual variables (latitude, longitude, shoreline distance, and calendar date). Predicts regional cyanobacteria abundance risk. Classes: `1` (Normal) to `5` (Dangerous Bloom). Note: This dataset contains no physical sensor variables (temp, pH, DO, etc.).
*   **HABSOS (Marine)**: Gulf of Mexico oceanographic parameters measuring temperature, salinity, sample depth, and spatial-temporal features. Classes: `1` (Normal) to `4` (Critical Red Tide).

## 6. Data Preprocessing
*   **Imputation & Scaling**: Median imputation and MinMax scaling are fitted strictly on training data.
*   **Cyclic Date Transformations**: Dates are mapped into 2D sine/cosine coordinates (e.g., `date_sin`, `date_cos`) to capture seasonal bloom patterns.

## 7. Supervised Machine Learning
Active deployment models are locked champions from Phase 3:
*   **Freshwater (CAML)**: Weighted Random Forest Contextual Risk Model. Accuracy = **63.23%**, Macro F1 = **0.5243**, Recall = **94.80%**.
*   **Marine (HABSOS)**: Weighted Logistic Regression Sensor-Based Model. Accuracy = **67.58%**, Macro F1 = **0.3411**, Recall = **0.4873**.

## 8. Artificial Immune System
The AIS preprocessor scales incoming readings against the training SELF subset. If scaled values fall outside the unit hypercube, they are clipped to prevent downstream numerical issues.

## 9. Negative Selection Algorithm
*   **Detector Generation**: 1,000 detectors generated in the non-self hypercube for CAML (radius = 0.6) and 500 detectors for HABSOS (radius = 0.2).
*   **CAML NSA Performance**: Validation balanced accuracy = **86.15%**, anomaly recall = **73.48%**, false positive rate = **1.19%**.
*   **HABSOS NSA Performance**: Validation anomaly recall = **0.00%**. Overlap in the low-dimensional feature space between normal and bloom states prevents effective geometric separation under locked configurations.

## 10. Evidence Fusion Engine
The gateway fuses evidence to determine the final system state:
*   **Freshwater Route**: Fuses CAML geographical/temporal contextual risk predictions with CAML AIS geographical/temporal anomaly flags.
    - `NORMAL`: Both ML and AIS confirm normal conditions.
    - `WARNING`: Contextual ML predicted class 2, 3, or 4, indicating elevated risk.
    - `CRITICAL`: Contextual ML predicted class 5, indicating high risk.
    - `UNKNOWN_ANOMALY`: ML predicted normal, but reliable CAML AIS flagged a geographical/temporal anomaly.
*   **Marine Route**: Fuses HABSOS ML predictions (ingesting temp, salinity, depth, and spatial-temporal features) with HABSOS AIS anomaly flags, applying a limited-reliability filter.
    - `NORMAL`: ML confirms normal category (or AIS anomaly is disregarded to prevent false alarms due to low reliability).
    - `WARNING`: ML predicted warning category.
    - `CRITICAL`: ML predicted critical category.
    - `UNKNOWN_ANOMALY`: ML is uncertain (LOW confidence) but AIS flags an anomaly.

## 11. Virtual Embedded System
Simulated using [esp32_device.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/esp32_device.py) running an FSM:
`BOOT` $\rightarrow$ `INITIALIZING` $\rightarrow$ `CONNECTING` $\rightarrow$ `ONLINE` $\rightarrow$ `SENSING` $\rightarrow$ `PUBLISHING` $\rightarrow$ `WAITING` $\rightarrow$ `ERROR`.
Local edge validation checks for NaNs, range violations, and stale timestamps.

## 12. IoT Communication Architecture
Telemetry payloads are transmitted as JSON frames over a mock in-memory MQTT transport wrapper. The mock broker supports wildcard topics and isolated unit tests.

## 13. Gateway
The gateway parses incoming JSON payloads, translates raw timestamps to cyclic coordinates, executes parallel ML/AIS inferences, triggers fusion logic, logs results, and dispatches command overrides to the devices.

## 14. Backend API
Implemented using FastAPI. Endpoints include: `/health`, `/devices`, `/devices/{id}/latest`, `/devices/{id}/telemetry`, `/alerts`, `/alerts/{id}/acknowledge`, and `/ws/live` for real-time WebSocket streaming.

## 15. Monitoring Dashboard
Developed in Streamlit. Displays real-time gauges, maps, parallel ML/AIS diagnostic cards, historical line charts, persistent alerts log tables, and command override controls.

## 16. Experimental Methodology
We evaluated the system under six operational scenarios (Freshwater Normal, Freshwater Bloom, Marine Normal, Marine Bloom, Sensor Fault, and Network Outage) to verify that edge rejections, ML alerts, and actuator overrides trigger correctly.

## 17. Results
*   The complete E2E loop runs successfully under all scenarios.
*   ML classifications, AIS anomaly scans, and fusion engine decisions are logged reliably.
*   All 132 automated tests passed successfully.

## 18. Failure Analysis
Edge validation successfully rejects sensor failures (NaN/inf values, out-of-range inputs, and frozen readings), preventing data contamination and setting the system state to `SENSOR_FAULT`.

## 19. Limitations
1.  Phase 4 model optimization attempts were invalidated due to validation data leakage.
2.  The locked AIS configuration has low anomaly recall on the exploratory OOD dataset.
3.  The HABSOS AIS model has 0.00% validation recall due to feature space overlap.
4.  The system uses simulated hardware and an in-memory MQTT transport.

## 20. Future Hardware Implementation
Migration to physical hardware involves swapping virtual sensors for real drivers (DS18B20 temp, analog pH, analog turbidity, and TDS probes), switching the transport to a real MQTT broker (e.g., Mosquitto), and implementing sensor calibration routines.

## 21. Conclusion
The parallel ML-AIS architecture provides a transparent, fault-tolerant monitoring system. Unsupervised anomaly detection flags unknown conditions without requiring labeled OOD training data, while the evidence-fusion engine coordinates gateway decisions.

---

## References Placeholder
1.  *Farmer, J. D., Packard, N. H., & Perelson, A. S. (1986). The immune system, adaptation, and machine learning. Physica D: Nonlinear Phenomena.*
2.  *Forrest, S., Perelson, A. S., Allen, L., & Cherukuri, R. (1994). Self-nonself discrimination in a computer. IEEE Symposium on Security and Privacy.*
