# Capstone Viva Questions and Answers

This document contains 75 technical questions and answers designed to prepare you for the viva examination.

---

## Part 1: Project Motivation (Q1 - Q5)

#### Q1: What is the core motivation behind this project?
To develop an integrated, fault-tolerant monitoring system for aquatic ecosystems using parallel intelligence (supervised machine learning and unsupervised artificial immune system anomaly detection) at the IoT gateway level.

#### Q2: Why is supervised ML alone insufficient for monitoring aquatic ecosystems?
Supervised classifiers can only detect known threats represented in the training data. They cannot identify out-of-distribution (OOD) novel anomalies, such as unseen chemical runoffs.

#### Q3: How does the Artificial Immune System (AIS) complement the ML classifiers?
The AIS runs in parallel, acting as an unsupervised novelty filter. It flags telemetry points that are geometrically far from normal (SELF) conditions, identifying potential new anomalies.

#### Q4: Why is edge-level data validation critical in this IoT architecture?
It sanitizes sensor inputs on the ESP32 before transmission. This prevents corrupt readings (e.g., NaNs or frozen values) from contaminating downstream ML and AIS inference models.

#### Q5: What is the role of the Evidence-Fusion Engine?
It resolves parallel predictions from the ML classifier and AIS filter using rules-based logic to determine the system's final state (`NORMAL`, `WARNING`, `CRITICAL`, or `UNKNOWN_ANOMALY`).

---

## Part 2: Datasets & Preprocessing (Q6 - Q15)

#### Q6: Which datasets are utilized in this project?
The freshwater CAML dataset (tracking cyanobacteria) and the marine HABSOS dataset (tracking Gulf of Mexico Red Tide dinoflagellates).

#### Q7: What are the target labels for the CAML dataset?
Classes range from `1` (Normal) to `5` (Dangerous Cyanobacteria Bloom).

#### Q8: What are the target labels for the HABSOS dataset?
Classes range from `1` (Normal) to `4` (Critical Red Tide Bloom).

#### Q9: How are missing values handled in the preprocessing pipeline?
We apply median imputation. The imputers are fitted strictly on the training partition.

#### Q10: Why did you apply MinMax scaling instead of standard scaling for the AIS pipeline?
MinMax scaling maps features to a bounded unit hypercube $[0, 1]^D$. This allows the Negative Selection Algorithm to generate detectors within a normalized space.

#### Q11: Why is temporal feature engineering necessary for algal bloom prediction?
Algal blooms are seasonal. Raw dates cannot be utilized directly by distance-based algorithms, requiring cyclical transformations.

#### Q12: How are dates converted to capture seasonal periodicities?
Dates are mapped into 2D circular spaces using sine and cosine transformations:
$$\text{date\_sin} = \sin\left(\frac{2\pi \cdot \text{day\_of\_year}}{365}\right), \quad \text{date\_cos} = \cos\left(\frac{2\pi \cdot \text{day\_of\_year}}{365}\right)$$

#### Q13: What features are included in the HABSOS ML feature space?
13 columns, including Temperature, Salinity, latitude, longitude, and seasonal cyclic date dimensions.

#### Q14: Why does the HABSOS AIS model use a subset of the ML feature space?
The HABSOS AIS model uses a 9-column subset, excluding spatial coordinates (latitude/longitude) to focus anomaly detection purely on environmental indicators.

#### Q15: How do you handle sensor values that fall outside the $[0, 1]$ scaled range during deployment?
The `AISPreprocessor` clips inputs to $[0, 1]$ to prevent negative distances or boundary issues.

---

## Part 3: Data Leakage (Q16 - Q20)

#### Q16: What is data leakage, and why is it a problem?
Data leakage occurs when information from the validation or test set is used during training, leading to overly optimistic performance estimates.

#### Q17: How did you prevent leakage during dataset splitting?
We split the datasets chronologically rather than randomly to preserve temporal order.

#### Q18: What data leakage issue occurred in Phase 4?
Validation data was reused during calibration and threshold search, invalidating the Phase 4 optimizations and requiring a rollback to the Phase 3 models.

#### Q19: How did you verify that preprocessor fitting was leak-free?
We verified that MinMax scalers and median imputers were fitted strictly on training partitions.

#### Q20: How are the test datasets protected in the final release?
The files `caml_test.csv` and `habsos_test.csv` are quarantined. Ripgrep search confirmed that no code files read them.

---

## Part 4: Machine Learning (Q21 - Q35)

#### Q21: What machine learning algorithm was selected for the CAML champion?
A Weighted Random Forest classifier.

#### Q22: What algorithm was selected for the HABSOS champion?
A Weighted Logistic Regression classifier.

#### Q23: Why was Random Forest selected for CAML over Logistic Regression?
Random Forest captures the complex, non-linear relationships in the freshwater geographic and temporal features better than linear classifiers.

#### Q24: Why was Logistic Regression selected for HABSOS over Random Forest?
The marine HABSOS dataset has simpler linear boundaries, and Logistic Regression achieved a more stable validation macro F1.

#### Q25: What are the validation metrics of the active CAML champion?
Accuracy = **63.23%**, Macro F1 = **0.5243**, and Dangerous Recall = **94.80%**.

#### Q26: What are the validation metrics of the active HABSOS champion?
Accuracy = **67.58%**, Macro F1 = **0.3411**, and Dangerous Recall = **0.4873**.

#### Q27: Why did you prioritize Weighted algorithms during training?
Both datasets exhibit extreme class imbalance, with normal states outnumbering bloom states. Class weighting penalizes minority class misclassifications during training.

#### Q28: What is Macro F1, and why is it used instead of Accuracy?
Macro F1 computes the F1-score for each class independently and averages them. It evaluates minor classes equally, whereas accuracy is biased toward the majority class.

#### Q29: What does Dangerous Recall measure?
The model's sensitivity in flagging hazardous bloom classes (classes 4 and 5 in CAML, and classes 3 and 4 in HABSOS).

#### Q30: Why was Random Forest incorrectly selected over a better baseline in Phase 4?
The Phase 4 optimization used incorrect target mappings and leaked validation data, which favored a overfitted Random Forest.

#### Q31: What is probability calibration, and why did you rollback Phase 4 calibration?
Calibration scales model probabilities to reflect real frequencies. In Phase 4.5, calibration was shown to reduce minority-class sensitivity.

#### Q32: What is the purpose of a model registry?
It logs model lineage, versions, validation scores, and audit statuses, ensuring only verified models are deployed.

#### Q33: How does `deployment_loader.py` load model files safely?
It verifies the model version and files against `model_manifest.json` and checks that the status is not `INVALIDATED` before loading.

#### Q34: What happens if you try to load an invalidated Phase 4 model?
The deployment loader raises a `PermissionError` and blocks execution.

#### Q35: Do the active ML models access test data during inference?
No. All online predictions run on real-time simulated telemetry.

---

## Part 5: Artificial Immune System & NSA (Q36 - Q50)

#### Q36: What is the biological inspiration behind the Negative Selection Algorithm (NSA)?
It is modeled after the thymus gland's T-cell maturation process, where T-cells that bind to self-proteins are destroyed, and only those recognizing foreign antigens (non-self) are released.

#### Q37: How does the NSA define the SELF space?
The SELF space is represented by the normal environmental coordinates in the training partition.

#### Q38: How are NSA detectors generated?
Random candidate coordinates are generated in the $[0, 1]^D$ hypercube. If a candidate falls within the self-radius ($r_s$) of any training self-sample, it is discarded. Otherwise, it is kept as a detector.

#### Q39: What is the affinity metric used in this system?
Euclidean distance:
$$d(x, y) = \sqrt{\sum_{i=1}^D (x_i - y_i)^2}$$

#### Q40: How does the NSA determine if a telemetry point is an anomaly?
If the Euclidean distance between a telemetry point and any detector is less than the detector's radius ($r_d$), the point is flagged as an anomaly (`is_anomaly = True`).

#### Q41: What are the locked parameters for the CAML NSA model?
1,000 detectors and a self-radius of 0.6.

#### Q42: What are the locked parameters for the HABSOS NSA model?
500 detectors and a self-radius of 0.2.

#### Q43: What is the validation performance of the CAML NSA?
Balanced Accuracy = **86.15%**, Anomaly Recall = **73.48%**, and False Positive Rate = **1.19%**.

#### Q44: Why did the HABSOS NSA achieve 0.00% validation anomaly recall?
The feature space overlap between normal and bloom states in the marine dataset prevents geometric separation under locked self-radii configurations.

#### Q45: Why is the original Phase 5 synthetic OOD experiment classified as exploratory?
It tuned the self-radii dynamically to fit the synthetic OOD samples, rather than locking parameters on validation data.

#### Q46: Did the locked AIS models detect those synthetic OOD samples?
No. Under locked parameters, the OOD points fell inside the self-radius boundaries and were classified as `SELF`.

#### Q47: What does an anomaly score of 0.0000 indicate in the dashboard?
It indicates that the telemetry point did not fall within any detector boundaries, meaning it is classified as `SELF`.

#### Q48: How is nearest detector distance calculated?
It is the Euclidean distance from the input sample to the closest active non-self detector.

#### Q49: What is the detector maturation threshold?
It is the self-radius constraint that candidate detectors must satisfy during the generation phase to be kept.

#### Q50: Can the NSA prove biological contamination?
No. It only identifies coordinate novelty in the environmental feature space, which may or may not correlate with biological contamination.

---

## Part 6: Evidence Fusion Engine (Q51 - Q55)

#### Q51: How are parallel ML and AIS predictions combined?
The Evidence-Fusion Engine processes the outputs using rules-based logic defined in `fusion_policy.json`. It deterministically combines the supervised ML classification predictions and unsupervised AIS anomaly flags according to the confidence bands of the active ML models to determine the final system state (NORMAL, WARNING, CRITICAL, or UNKNOWN_ANOMALY).

#### Q52: What is the HABSOS limited-reliability policy?
Because of the feature space overlap, HABSOS AIS anomaly alerts are disregarded for state escalation on medium/high confidence ML predictions to prevent false alarms.

#### Q53: How were confidence bands derived for the ML models?
We analyzed correct and incorrect validation probability distributions to establish thresholds:
*   **CAML:** LOW: $< 0.50$, MEDIUM: $[0.50, 0.80)$, HIGH: $\ge 0.80$.
*   **HABSOS:** LOW: $< 0.50$, MEDIUM: $[0.50, 0.70)$, HIGH: $\ge 0.70$.

#### Q54: When does the Fusion Engine emit an UNKNOWN_ANOMALY state?
When a low-confidence ML prediction is combined with an AIS anomaly flag.

#### Q55: What does the confidence_band field represent in a fusion decision?
It indicates the reliability of the final fused state, determined by the ML model's prediction confidence.

---

## Part 7: Virtual IoT, ESP32, FSM, and MQTT (Q56 - Q65)

#### Q56: How is the physical hardware simulated in this project?
We use Python classes: `SensorSimulator` generates environmental readings, `ESP32Device` runs the state machine, and `Actuator` manages status indicators.

#### Q57: What are the states of the ESP32 state machine?
`BOOT`, `INITIALIZING`, `CONNECTING`, `ONLINE`, `SENSING`, `PUBLISHING`, `WAITING`, `ERROR`, and `RECOVERING`.

#### Q58: What checks are performed by the edge validator?
It rejects payloads containing NaNs or infinities, range violations (e.g., pH < 0 or pH > 14), stale timestamps, or frozen values.

#### Q59: How does the edge validator identify frozen sensor readings?
It maintains a sliding history of the last 5 readings. If a sensor value remains constant, it flags a frozen sensor fault.

#### Q60: What transport protocol is simulated in this architecture?
An in-memory MQTT-compatible transport broker (`InMemoryMQTTBroker`).

#### Q61: Does the mock MQTT broker support topic wildcards?
Yes. It supports single-level (`+`) and multi-level (`#`) wildcards.

#### Q62: What topic does the ESP32 device use to publish telemetry?
`aquatic/{device_id}/telemetry`

#### Q63: What topic does the ESP32 device subscribe to for decisions?
`aquatic/{device_id}/decision`

#### Q64: What actuators are simulated for each node?
A green status LED, a yellow status LED, a red status LED, a piezo buzzer, and an aerator pump relay.

#### Q65: What state do the actuators default to in an error or disconnect state?
They turn `OFF` for safety.

---

## Part 8: Backend & Dashboard (Q66 - Q70)

#### Q66: What technology stacks are used for the backend and dashboard?
FastAPI for the REST/WebSocket backend API, and Streamlit for the visualization dashboard.

#### Q67: What does the `/ws/live` WebSocket endpoint do?
It streams real-time telemetry frames and gateway fusion decisions to the dashboard without database polling.

#### Q68: How is the dashboard styled according to the project's visual policy?
We map states to distinct colors using custom CSS:
*   `NORMAL` $\rightarrow$ Green
*   `WARNING` $\rightarrow$ Orange
*   `CRITICAL` $\rightarrow$ Red
*   `UNKNOWN_ANOMALY` $\rightarrow$ Purple
*   `SENSOR_FAULT` $\rightarrow$ Gray

#### Q69: What controls are available on the dashboard sidebar?
Simulation start/stop buttons, scenario selectors, and command override controls (e.g., to activate the buzzer).

#### Q70: What does `run_demo.py` do?
It starts the FastAPI server and the Streamlit dashboard in parallel subprocesses and handles clean shutdowns.

---

## Part 9: Testing, Security, and Limitations (Q71 - Q75)

#### Q71: How many tests are included in the final project test suite?
156 tests, covering ML/AIS loaders, gateways, edge validation, REST endpoints, and WebSocket connections.

#### Q72: How are SQL injection attacks prevented?
All database queries use parameterized parameters (`?`) rather than string concatenation.

#### Q73: What is the path traversal check implemented in the API?
We validate device IDs against strict alphanumeric Pydantic patterns to prevent directory traversal attempts.

#### Q74: Why is the MQTT broker mock preferred over a real broker in the test suite?
It keeps the test suite self-contained, reproducible, and independent of external networks or services.

#### Q75: How should the system be presented in the final capstone viva?
As a software-based simulation demonstrating parallel supervised-unsupervised gateway intelligence, edge validation, and real-time visualization.
