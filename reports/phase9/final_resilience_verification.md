# Final Resilience and Failure Verification Report

This report documents the system's fault-tolerant behaviors and safety blocks under simulated physical and network failures.

## 1. Safety Block Verifications

| Test Case | Simulated Input / State | Expected Safety Action | Actual Behavior | Status |
|:---|:---|:---|:---|:---|
| **Sensor NaN** | Salinity = `NaN` | Block gateway inference, alert and flag sensor status `FAULT`. | Inference bypassed; alert logged; state set to `SENSOR_FAULT`. | **PASS** |
| **Sensor Infinity** | Temp = `inf` | Reject input at edge; alert flagged. | Input blocked; state set to `SENSOR_FAULT`. | **PASS** |
| **Out-of-range** | pH = 15.0 | Flag range error; bypass model schema. | Rejected; logged as `SENSOR_FAULT`. | **PASS** |
| **Frozen values** | pH constant for 5 ticks | Detect frozen state; trigger warning. | Stale log triggers `SENSOR_FAULT`. | **PASS** |
| **Unknown Device** | Client = `AQUA_FAKE_001` | Reject MQTT connection/Gateway registry authorization. | Refused processing. | **PASS** |
| **Malformed JSON** | Payload = `{"bad_json"` | MQTT subscriber catches parse error, logs to `error_logs`. | Logged in database; pipeline bypassed. | **PASS** |
| **Network Outage** | WiFi state = `False` | ESP32 enters `ERROR` state; buffers last data; recovers. | Enters FSM disconnect routine; recovers to sensing. | **PASS** |
| **Invalid commands** | Cmd = `DESTRUCT` | API returns `422 Unprocessable` or `404 Not Found`. | Blocked at validation schema level. | **PASS** |
| **Invalid route** | Route = `/fake` | Gateway returns error or default fallback. | Handled safely via router exception blocks. | **PASS** |

---

## 2. Model Security Verification

*   **Invalid Model Block:** Attempts to load archived or invalidated model files (e.g. from Phase 4 optimization experiments) are blocked. The model loader raises a `PermissionError` to prevent model contamination.
