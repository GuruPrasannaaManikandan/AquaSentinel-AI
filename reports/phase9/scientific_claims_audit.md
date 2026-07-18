# Scientific Claims Audit Report

This report evaluates and classifies the scientific and technical claims made throughout the Capstone project.

## 1. Classification of Scientific Claims

We audit all core project claims under five classifications:
1.  **VERIFIED:** Proven by reproducible, validated testing metrics.
2.  **SUPPORTED_WITH_LIMITATIONS:** Supported under specific boundaries or caveats.
3.  **EXPLORATORY:** Valid during initial experiments but not verified as stable performance.
4.  **INVALIDATED:** Invalidated due to methodology errors or lack of integrity.
5.  **UNSUPPORTED:** Lacking empirical evidence.

---

## 2. Audited Claims & Classifications

### 2.1 Model Tuning Optimization (Phase 4)
*   *Claim:* Phase 4 model parameter tuning increased the accuracy of the CAML and HABSOS models.
*   *Classification:* **INVALIDATED**. The Phase 4.5 forensic audit discovered that validation data was leaked during threshold selection, model evaluations used invalid baselines, and mappings changed. All Phase 4 optimizations were rolled back.

### 2.2 Unsupervised OOD Telemetry Detection (Phase 5)
*   *Claim:* The Negative Selection Algorithm (NSA) immediately detects out-of-distribution telemetry under locked, validation-trained parameters.
*   *Classification:* **EXPLORATORY**. In high dimensions, the locked self-radii (0.6 and 0.2) have zero coverage of OOD coordinates. Telemetry only triggered when ad-hoc radii (0.9 and 0.7) were introduced.

### 2.3 HABSOS Dinoflagellate Bloom Anomaly Recall
*   *Claim:* The HABSOS AIS module acts as a reliable filter for marine dinoflagellate blooms.
*   *Classification:* **UNSUPPORTED / SUPPORTED_WITH_LIMITATIONS**. HABSOS validation anomalies overlap physically with normal SELF states, yielding **0.00%** recall. It remains active under a limited-reliability routing policy.

### 2.4 IoT Edge Hardware Deployment
*   *Claim:* The system runs physically on an ESP32 microcontroller with raw water quality sensor inputs.
*   *Classification:* **SUPPORTED_WITH_LIMITATIONS**. The microcontroller, sensors, and actuators are simulated using software models. The in-memory MQTT transport replaces physical radios.

---

## 3. Preservation of Crucial Scientific Limitations

To maintain scientific integrity, we declare the following limitations:
1.  Phase 4 model optimization is fully **invalidated** and inactive.
2.  The Phase 5 OOD anomaly experiment is **exploratory** due to ad-hoc radius tuning.
3.  Under locked parameters, the OOD points do not match any detectors (`is_anomaly = False`).
4.  HABSOS AIS achieved **0% known recall** on validation warning/critical classes.
5.  The communication layer is an **in-memory MQTT transport**.
6.  The physical hardware consists of **software simulations**.
7.  An AIS anomaly flags coordinate novelty, which does **not** prove biological contamination.
