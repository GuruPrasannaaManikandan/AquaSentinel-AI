# Safety and Failure-Mode Analysis

This document provides a safety analysis and defines system behavior under potential failure modes.

## 1. Safety Failure-Mode Matrix

| ID | Failure Mode | System Behavior | Residual Risk | Mitigation in Backend / IoT Gateway |
|:---|:---|:---|:---|:---|
| 1 | ML false negative + AIS normal | System emits `NORMAL`. No hazard detected. | Dangerous bloom goes undetected. | Gateway uses physical redundant sensors or manual local samples. |
| 2 | ML false negative + AIS anomaly | System emits `UNKNOWN_ANOMALY` (for CAML) or `NORMAL` (HABSOS). | CAML bloom triggers inspection. HABSOS bloom goes undetected. | Gateway triggers manual sampling on HABSOS OOD indicators. |
| 3 | ML false positive + AIS normal | System emits `WARNING`/`CRITICAL`. | False alarm. | Operator manually reviews sensor imagery to cancel alarm. |
| 4 | ML false positive + AIS anomaly | System emits `WARNING`/`CRITICAL`. | False alarm. | Operational threshold check. |
| 5 | AIS false positive | System emits `UNKNOWN_ANOMALY` (CAML). | Unnecessary inspection alert. | Local imputer calibration to prevent coordinate noise. |
| 6 | HABSOS AIS failure to detect blooms | System behaves according to ML prediction. | Bloom detection relies entirely on ML classifier. | Increase features space (e.g. adding wind, nutrients, chlorophyll-a). |
| 7 | Low-confidence ML outputs | Fusion Engine maps to `UNKNOWN_ANOMALY` or suspicion-state with low-confidence warning. | High uncertainty. | Flagged telemetry for cloud retraining. |
| 8 | Missing sensor data | Preprocessor imputes missing columns with median VALUES. | Imputation bias. | Sensor diagnostic flag raised to notify hardware technicians. |
| 9 | Invalid payload | FusionEngine raises `ValueError` or `TypeError`. | Engine crash. | Exception handlers in the Edge coordinator emit `UNKNOWN_ANOMALY` state. |
| 10 | Out-of-distribution telemetry | AIS triggers anomaly flag, engine emits `UNKNOWN_ANOMALY` (if CAML). | Flagged. | Immediate sensor recalibration check. |
