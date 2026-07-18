# Phase 5 OOD Consistency Audit Report

This audit examines the threshold discrepancy in the Phase 5 out-of-distribution (OOD) experiment and establishes the distinction between locked-parameter results and exploratory tuning.

## 1. Audit Questions & Findings

1. **Why were different matching radii used in the Phase 5 OOD experiment?**
   In high dimensions (7D for CAML, 9D for HABSOS), random candidate detectors cover a vanishingly small fraction of the unit hypercube. With only 500 or 1000 detectors, using the tight training `self_radius` parameters resulted in zero coverage of the OOD point regions. Therefore, larger matching radii were introduced during testing to increase coverage.
   
2. **Were these test-time matching radii selected using validation data?**
   No, they were selected ad-hoc specifically for the synthetic OOD observations to trigger.
   
3. **Were they registered in `ais_registry.json`?**
   No. The registry only contains the locked validation training self-radii (`0.6` for CAML and `0.2` for HABSOS).
   
4. **Does `AISLoader` use them during ordinary inference?**
   No. Ordinary inference defaults to the locked `self_radius` from the registry.
   
5. **Were they introduced specifically to make the synthetic OOD examples trigger?**
   Yes. Under the locked self-radii, the OOD points do not fall inside any detector's matching radius.
   
6. **Is the OOD experiment reproducible using only locked registered AIS parameters?**
   No, using locked parameters, both OOD observations yield `is_anomaly = False`.

---

## 2. Experimental Verification

We ran the OOD observations through both the locked registered parameters and the exploratory Phase 5 parameters:

### 2.1 CAML (Freshwater) OOD Telemetry
- **Locked Registered Parameters (Radius = 0.6):**
  - Anomaly Detected: False
  - Anomaly Score: 0.0000
  - Nearest Detector Distance: 0.8476
  - Final System State: NORMAL
- **Exploratory Phase 5 Parameters (Radius = 0.9):**
  - Anomaly Detected: True
  - Anomaly Score: 0.0582
  - Final System State: UNKNOWN_ANOMALY

### 2.2 HABSOS (Marine) OOD Telemetry
- **Locked Registered Parameters (Radius = 0.2):**
  - Anomaly Detected: False
  - Anomaly Score: 0.0000
  - Nearest Detector Distance: 0.6301
  - Final System State: WARNING
- **Exploratory Phase 5 Parameters (Radius = 0.7):**
  - Anomaly Detected: True
  - Anomaly Score: 0.0998
  - Final System State: WARNING

---

## 3. Conclusions and Policy Setting
- **Exploratory Classification:** The original Phase 5 OOD experiment is classified as **exploratory**. It does not represent validated system performance.
- **State Escalation Policy:** In production, to ensure deterministic safety without arbitrary ad-hoc overrides, the final decision engine must use the locked registered parameters.
