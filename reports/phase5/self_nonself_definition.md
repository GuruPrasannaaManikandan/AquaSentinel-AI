# Self and Non-Self Definitions in the Aquatic AIS

This document defines the mathematical and biological boundary mappings between normal conditions (**SELF**) and anomalous or threat conditions (**NON-SELF**) for the CAML and HABSOS datasets.

---

## 1. Biological and Computational Context
In biological immunology, the thymus trains T-cells to ignore host tissue (**SELF**) and attack pathogens (**NON-SELF**).
For our IoT-Based Artificial Immune System:
*   **SELF** represents the normal, stable baseline status of the aquatic ecosystem (no toxic blooms or abnormal physical behaviors).
*   **NON-SELF** represents ecological anomalies, specifically harmful algal blooms (HABs) and out-of-distribution environmental disruptions.

---

## 2. CAML Target Mapping (Freshwater Cyanobacteria)

### Scientific Class Division
The target column in the CAML dataset is `severity` (derived log-abundance of cyanobacteria cells/L).

| Severity Class | Biological State | Cell Count Range (cells/L) | AIS Designation | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Class 1** | Normal / Baseline | $[0, 20)$ | **SELF** | Represents background levels with zero risk of toxicity. |
| **Class 2** | Low-Medium | $[20, 100)$ | *Excluded from Training* | Intermediate states that represent early transition phases. |
| **Class 3** | Medium | $[100, 1,000)$ | *Excluded from Training* | Intermediate states that could pollute the SELF representation. |
| **Class 4** | High | $[1,000, 10,000)$ | **NON-SELF (Anomaly)** | Confirmed bloom threat requiring alert. |
| **Class 5** | Extreme | $\ge 10,000$ | **NON-SELF (Anomaly)** | Confirmed toxic bloom requiring immediate alert. |

### Computational Protocol
1.  **Training Phase:** The Negative Selection Algorithm (NSA) is trained **strictly on observations where `severity == 1`**.
2.  **Evaluation Phase:** In evaluation, `severity == 1` maps to the negative class (non-anomaly), and `severity in [4, 5]` maps to the positive class (anomaly). Classes 2 and 3 are evaluated separately or excluded to maintain a clean binary validation boundary.

---

## 3. HABSOS Target Mapping (Marine HABs)

### Scientific Class Division
The target column in the HABSOS dataset is `CATEGORY`, mapping to cell counts of the toxic dinoflagellate *Karenia brevis*.

| Target Category | Raw Dinoflagellate Level | cell count / L | AIS Designation | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **`normal`** | not observed, very low | $< 1,000$ | **SELF** | Represents safe marine environment with negligible dinoflagellate count. |
| **`warning`** | low, medium | $[1,000, 100,000)$ | **NON-SELF (Anomaly)** | Elevated counts indicating potential bloom formation. |
| **`critical`** | high | $\ge 100,000$ | **NON-SELF (Anomaly)** | High concentration bloom associated with respiratory irritation and fish kills. |

### Computational Protocol
1.  **Training Phase:** The NSA is trained **strictly on observations where `CATEGORY == 'normal'`**.
2.  **Evaluation Phase:** In validation and testing, `'normal'` maps to the negative class (non-anomaly), and `['warning', 'critical']` map to the positive class (anomaly).
