# CAML Target Validity Report

## 1. Analysis of the Target Variable (`severity`)
In the CAML dataset, the target column is `severity` (taking values 1, 2, 3, 4, and 5) and the primary continuous biological measure is `abun` (cyanobacteria abundance in cells/L).

To verify target validity, we audited the exact range of `abun` for each `severity` value:
- **Severity 1 (Low/None):** Abundance range $[0.0, 19.969]$ cells/L (Mean: $5.05$).
- **Severity 2 (Low-Medium):** Abundance range $[20.0, 99.972]$ cells/L (Mean: $49.05$).
- **Severity 3 (Medium):** Abundance range $[100.0, 996.254]$ cells/L (Mean: $349.15$).
- **Severity 4 (High):** Abundance range $[1000.0, 9960.0]$ cells/L (Mean: $4261.47$).
- **Severity 5 (Extreme):** Abundance range $[10016.467, 804667.5]$ cells/L (Mean: $38339.48$).

### Proof of Determinism:
The severity class is assigned strictly on a log10-like binning threshold of abundance:
$$\text{Severity} = \begin{cases} 
1 & \text{if } \text{abun} < 20 \\
2 & \text{if } 20 \le \text{abun} < 100 \\
3 & \text{if } 100 \le \text{abun} < 1,000 \\
4 & \text{if } 1,000 \le \text{abun} < 10,000 \\
5 & \text{if } \text{abun} \ge 10,000 
\end{cases}$$

---

## 2. Target Leakage & Trivial Prediction Analysis
*   **Is there leakage?** **Yes.** If `abun` is included as an input feature to predict `severity`, a simple decision tree will set splits at exactly $20$, $100$, $1,000$, and $10,000$. This leads to a trivial, non-generalizable machine learning model.
*   **Inference Availability:** In a live, real-time IoT scenario, a physical sensor node (such as an ESP32 deployed in a lake) cannot measure biological cell concentrations directly. Microscopic counting requires water sample collection and laboratory analysis, which takes days.
*   **Scientific Meaningfulness:** Training a model to predict severity using other variables (geographic coordinates, month of the year, and distance to water) is highly meaningful because it estimates ecological risk using easily obtainable predictors.

---

## 3. Recommended CAML Machine Learning Task
*   **Selected Task:** **Multiclass Classification of Severity (excluding `abun` as a feature).**
*   **Justification:** Predicting the severity levels (1 to 5) directly maps to the Artificial Immune System (AIS) framework's multi-level immune response:
    *   *Severity 1 and 2:* **NORMAL** (No reaction or background monitoring).
    *   *Severity 3 and 4:* **WARNING** (Early detection warning triggers, increased sensor reading frequencies).
    *   *Severity 5:* **CRITICAL** (Active bloom threat response, buzzer alarms, and dashboard alerts).
*   **Predictors to use:** `lat`, `lon`, `distance_to_water_m`, `Month` (represented cyclically), and `Season`.
