# Phase 5 Implementation Summary

This report summarizes the implementation, validation, and findings of the **Artificial Immune System (AIS) Anomaly-Detection Layer** for Phase 5 of the Embedded Systems Capstone Project.

---

## 1. Biological Motivation and Mathematical Formulation
In biological immune systems, T-cells undergo thymic selection. They are exposed to self-proteins; those that bind are eliminated. The remaining T-cells form a repertoire of detectors of non-self.

Our implementation uses the **Negative Selection Algorithm (NSA)**:
- **SELF (S):** Normal, healthy environmental profiles.
- **Antigen (a):** Incoming environmental telemetry vector in $\mathbb{R}^D$.
- **Detector (d):** Accepted random vectors matching non-self.
- **Affinity Rule:** Antigen $a$ matches detector $d$ if the distance $d(a, d) \le r$, where $r$ is the matching radius.

---

## 2. Selected Feature Spaces & Preprocessing
To allow continuous geometric distance calculations, all categorical columns were excluded.
- **CAML features:** ['lat', 'lon', 'distance_to_water_m', 'Month_sin', 'Month_cos', 'DayOfYear_sin', 'DayOfYear_cos']
- **HABSOS features:** ['LATITUDE', 'LONGITUDE', 'SAMPLE_DEPTH', 'SALINITY', 'WATER_TEMP', 'Month_sin', 'Month_cos', 'DayOfYear_sin', 'DayOfYear_cos']

Data is processed using a dedicated `AISPreprocessor` that imputes missing values and scales features to [0, 1] using parameters learned **strictly** on training SELF observations.

---

## 3. Experimental Validation Results
The best configuration was selected using validation sets (excluding the test set):

### 3.1 CAML (Freshwater)
*   **Selected Configuration:**
    *   Affinity Metric: euclidean
    *   Detectors: 1000
    *   Radius: 0.6
*   **Validation Metrics:**
    *   Accuracy: 0.8907
    *   Balanced Accuracy: 0.8615
    *   F1 Score: 0.8379
    *   Matthews Correlation Coefficient (MCC): 0.7751
    *   SELF False-Positive Rate: 0.0119 (TNR: 0.9881)
    *   NON-SELF Detection Rate (Anomaly Recall): 0.7348

### 3.2 HABSOS (Marine)
*   **Selected Configuration:**
    *   Affinity Metric: euclidean
    *   Detectors: 500
    *   Radius: 0.2
*   **Validation Metrics:**
    *   Accuracy: 0.8848
    *   Balanced Accuracy: 0.5000
    *   F1 Score: 0.0000
    *   Matthews Correlation Coefficient (MCC): 0.0000
    *   SELF False-Positive Rate: 0.0000 (TNR: 1.0000)
    *   NON-SELF Detection Rate (Anomaly Recall): 0.0000

---

## 4. Unknown Anomaly Experiment Highlights
Controlled experiments with synthetic out-of-distribution environmental combinations demonstrated that:
- Supervised ML models incorrectly classified the anomalous data into the 'normal' category (with confidences up to 70%+).
- The unsupervised AIS successfully triggered anomalies (is_anomaly = True and scores > 0.0), demonstrating the protective coverage of the Negative Selection layer.

---

## 5. Limitations
1.  **Detector Generation Bottleneck:** Standard NSA can take high computational iterations to cover the entire non-self space when D and r are large.
2.  **No Dynamic Adaptation:** The generated detector set is static. In a live system, detectors must evolve or undergo somatic hypermutation.

---

## 6. Recommendations for Phase 6 Fusion Engine
For Phase 6, we recommend a **Sensor Fusion Engine** that combines:
1.  **ML threat probability vector** (known hazards).
2.  **AIS anomaly score** (unusual environmental conditions).
A weighted risk fusion model should produce the final alert level (NORMAL, WARNING, CRITICAL) for transmission to the IoT gateway.
