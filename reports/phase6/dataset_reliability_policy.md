# Dataset-Specific AIS Reliability Policy

Because the CAML AIS and HABSOS AIS models exhibit dramatically different validation behaviors, they cannot be treated as equally reliable evidence streams.

## 1. Subsystem Performance Comparison

*   **CAML AIS (Freshwater):**
    *   Validation Balanced Accuracy: **86.15%**
    *   Recall (NON-SELF): **73.48%**
    *   False Positive Rate: **1.19%**
    *   *Status:* **RELIABLE**. Telemetry coordinates associated with high-severity freshwater blooms are geometrically separated from normal conditions. The AIS has high capability to flag anomalies.

*   **HABSOS AIS (Marine):**
    *   Validation Balanced Accuracy: **50.00%** (Random guessing equivalent)
    *   Recall (NON-SELF): **0.00%**
    *   False Positive Rate: **0.00%**
    *   *Status:* **UNRELIABLE FOR THREAT DETECTION**. Physical indicators of marine blooms overlap heavily with normal conditions. Detectors generated outside SELF also sit outside validation anomalies, yielding zero detection rate.

---

## 2. Fusion Reliability Policies

### 2.1 CAML Policy
- **Policy:** The AIS anomaly flag is trusted. If the ML predicts normal but the AIS flags an anomaly (at medium/high ML confidence), the state is escalated to `UNKNOWN_ANOMALY`.
- **Reason Code:** `ML_NORMAL_AIS_ANOMALY`.

### 2.2 HABSOS Policy
- **Policy:** The AIS anomaly flag is **disregarded** for state escalation on medium/high confidence ML normal predictions. If ML predicts normal and HABSOS AIS flags an anomaly, the final state remains `NORMAL`.
- **Exploratory Limit:** The HABSOS AIS anomaly is reported in metadata as exploratory novelty signaling only.
- **Reason Code:** `HABSOS_AIS_LIMITED_RELIABILITY` (to avoid false-positive alerts on overlapping marine datasets).
- **Low Confidence Exception:** If HABSOS ML confidence is low AND AIS is anomaly, we escalate to `UNKNOWN_ANOMALY` as a secondary exploratory trigger.
