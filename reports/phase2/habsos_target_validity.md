# HABSOS Target Validity Report

## 1. Analysis of the Target Variable (`CATEGORY` / `CELLCOUNT`)
In the HABSOS dataset, the target column is `CATEGORY` (a categorical risk assessment) and the primary continuous biological measure is `CELLCOUNT` (*Karenia brevis* cells/L).

To verify target validity, we audited the relationship between `CELLCOUNT` and `CATEGORY`:
- **`not observed`:** CELLCOUNT is exactly $0$ cells/L (164,102 rows).
- **`very low`:** CELLCOUNT ranges from $1$ to $9,733$ cells/L (Mean: $2,454$, 18,925 rows).
- **`low`:** CELLCOUNT ranges from $10,000$ to $99,896$ cells/L (Mean: $39,429$, 12,567 rows).
- **`medium`:** CELLCOUNT ranges from $100,000$ to $999,000$ cells/L (Mean: $340,782$, 11,705 rows).
- **`high`:** CELLCOUNT ranges from $1,000,000$ to $388,400,000$ cells/L (Mean: $6,022,169$, 3,679 rows).

### Proof of Determinism:
The categorical target `CATEGORY` is assigned strictly using the following cell count thresholds:
$$\text{CATEGORY} = \begin{cases} 
\text{not observed} & \text{if } \text{CELLCOUNT} == 0 \\
\text{very low} & \text{if } 0 < \text{CELLCOUNT} < 10,000 \\
\text{low} & \text{if } 10,000 \le \text{CELLCOUNT} < 100,000 \\
\text{medium} & \text{if } 100,000 \le \text{CELLCOUNT} < 1,000,000 \\
\text{high} & \text{if } \text{CELLCOUNT} \ge 1,000,000 
\end{cases}$$

---

## 2. Target Leakage & Trivial Prediction Analysis
*   **Is there leakage?** **Yes.** If `CELLCOUNT` is included as an input feature during classification training, the model achieves trivial 100% accuracy by mapping numerical boundaries.
*   **Inference Availability:** In a live IoT system, cell counts of *Karenia brevis* must be determined by manual water sampling and microscopy. This cannot be measured in real-time.
*   **Scientific Meaningfulness:** Training a model to predict the category of bloom risk using only physical, real-time measurements (such as salinity, water temperature, depth, and spatial-temporal coordinates) is scientifically valuable, as it estimates ecological risk from physical sensor inputs.

---

## 3. Recommended HABSOS Machine Learning Task
*   **Selected Task:** **Multiclass Classification of Category (excluding `CELLCOUNT` as an input feature).**
*   **Justification:** The binned classification targets map cleanly into the multi-level immune warnings required for our Artificial Immune System:
    *   *`not observed` & `very low`:* **NORMAL** (Healthy marine conditions).
    *   *`low` & `medium`:* **WARNING** (Early detection warnings, increasing sensor sample frequencies).
    *   *`high`:* **CRITICAL** (Active red tide response, indicator warnings, dashboard alerts).
*   **Why not regression on cell count?** Since ~77% of the dataset contains exact zeros (zero-inflation) and cell counts range from 0 to 388 million (extremely skewed), training a stable regression model requires complex two-stage architectures (e.g. hurdle models). A multiclass classification task is much more stable, robust, and directly suitable for an IoT alert gateway.
*   **Predictors to use:** `LATITUDE`, `LONGITUDE`, `SALINITY`, `WATER_TEMP`, `SAMPLE_DEPTH`, `Month` (cyclically encoded), and `Season`.
