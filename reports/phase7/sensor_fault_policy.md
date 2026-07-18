# Sensor Fault Policy Report

This report outlines the rules and policies used to distinguish physical environmental anomalies from hardware and sensor failures.

## 1. Defining Faults vs. Anomalies

We define a clear separation between environmental states and device health states:

| Category | Indicator | System Response | Model Ingestion | Final State |
|:---|:---|:---|:---|:---|
| **Normal State** | Environmental features within standard bounds. | Normal Operation. | Yes | `NORMAL` |
| **Environmental Anomaly** | Physically consistent readings that lie outside normal statistical distributions. | AIS flags anomaly. | Yes (CAML) | `UNKNOWN_ANOMALY` |
| **Sensor Fault (Hardware)** | Non-physical values (NaN, infinite, out-of-bounds) or completely frozen values. | Edge validator flags `FAULT`. | **BLOCKED** | `ERROR` / `WARNING` |

---

## 2. Ingestion Block Policy

> [!WARNING]
> **Data Poisoning Prevention:**
> Under no circumstances may sensor readings flagged with a `FAULT` status by the edge validator be passed to the ML/AIS models. Doing so would violate the inference contract and could cause models to crash or output unreliable predictions.

### Fault Routing Protocol:
1.  **Edge Detection:** The ESP32 device runs `EdgeValidator` on raw polled inputs.
2.  **Telemetry Flagging:** If a fault is detected (e.g. a temperature sensor returning `NaN`), the telemetry is marked with `sensor_status = "FAULT"` or `"DEGRADED"`.
3.  **Gateway Block:** The central gateway validates the schema. If `sensor_status == "FAULT"`:
    *   The gateway **bypasses** the `DecisionPipeline` completely.
    *   The event is logged in the SQLite store as a `validation_failure` and `error_log`.
    *   An override state (`WARNING` or `UNKNOWN`) is emitted, and a `RUN_DIAGNOSTICS` command is sent back to the device.
