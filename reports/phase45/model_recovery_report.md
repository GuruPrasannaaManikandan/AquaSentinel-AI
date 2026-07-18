# Phase 4.5 Model Recovery & Freeze Report

## 1. Forensic Audit Verdict
The Phase 4.5 forensic integrity audit determined that the final optimized models in Phase 4 were **invalid** due to:
1.  **Validation Data Leakage:** Reusing the validation partition (`caml_val.csv` and `habsos_val.csv`) to fit the Platt scaling calibration models (`CalibratedClassifierCV`) and search for probability decision thresholds, introducing statistical bias.
2.  **HABSOS Performance Collapse:** Forcing a Random Forest model and Platt scaling for the marine HABSOS dataset, which compressed minority class probabilities near zero and collapsed the safety-critical dangerous class recall to a failing **7.51%** (a 6.5x drop compared to Phase 3).
3.  **Invalid Model Selection:** Excluding Logistic Regression from the Phase 4 optimization space.
4.  **Placeholder Reporting:** Using hardcoded placeholder text for metrics in reports rather than actual model performance.

**Action Taken:** All Phase 4 optimized models have been officially **INVALIDATED** and archived. The uncalibrated Phase 3 champion models have been recovered and promoted as the active, frozen deployment candidates.

---

## 2. Model Lineage & Invalidated Models
The following Phase 4 models have been archived to `models/archive/phase4_invalid/` and marked as `INVALIDATED` in the model registry to prevent accidental loading:

*   **CAML Phase 4 Model (`caml_phase4_invalid`):**
    *   *Algorithm:* `ThresholdShiftClassifier` wrapping Calibrated Random Forest
    *   *Archived Path:* `models/archive/phase4_invalid/caml_final_model.joblib`
    *   *Status:* `INVALIDATED` (failed Phase 4.5 integrity audit)
*   **HABSOS Phase 4 Model (`habsos_phase4_invalid`):**
    *   *Algorithm:* `ThresholdShiftClassifier` wrapping Calibrated Random Forest
    *   *Archived Path:* `models/archive/phase4_invalid/habsos_final_model.joblib`
    *   *Status:* `INVALIDATED` (failed Phase 4.5 integrity audit)

---

## 3. Recovered Models & Deployment Candidates
The following Phase 3 champion models have been verified, copied to `models/deployment/`, and promoted as active deployment candidates:

### 3.1 CAML (Freshwater Cyanobacteria Bloom Model)
*   **Model ID:** `caml_phase3_champion`
*   **Version:** `3.0.0`
*   **Status:** `DEPLOYMENT_CANDIDATE`
*   **Audit Status:** `VERIFIED_AFTER_PHASE45`
*   **Algorithm:** Weighted Random Forest (`random_forest_weighted`)
*   **Artifact Path:** `models/deployment/caml_champion.joblib`
*   **Target:** `severity`
*   **Target Mapping:** None (direct integer levels `1` to `5`)
*   **Dangerous Classes:** `[4, 5]` (High and Extreme risk)
*   **Validation Metrics:**
    *   *Accuracy:* `0.6323`
    *   *Macro F1:* `0.5243`
    *   *Dangerous Recall:* `0.9480`
*   **Feature Schema:**
    `['lat', 'lon', 'distance_to_water_m', 'Year', 'Month_sin', 'Month_cos', 'DayOfYear_sin', 'DayOfYear_cos', 'region', 'Season']`
*   **Preprocessing Pipeline:**
    *   Global median imputation using training statistics
    *   Z-score scaling on all numeric columns
    *   One-hot encoding for `region` and `Season`

### 3.2 HABSOS (Marine Harmful Algal Bloom Model)
*   **Model ID:** `habsos_phase3_champion`
*   **Version:** `3.0.0`
*   **Status:** `DEPLOYMENT_CANDIDATE`
*   **Audit Status:** `VERIFIED_AFTER_PHASE45`
*   **Algorithm:** Weighted Logistic Regression (`logistic_regression_weighted`)
*   **Artifact Path:** `models/deployment/habsos_champion.joblib`
*   **Target:** `CATEGORY`
*   **Target Mapping:**
    *   `'not observed' -> 'normal'`
    *   `'very low' -> 'normal'`
    *   `'low' -> 'warning'`
    *   `'medium' -> 'warning'`
    *   `'high' -> 'critical'`
*   **Dangerous Classes:** `['warning', 'critical']`
*   **Validation Metrics:**
    *   *Accuracy:* `0.6758`
    *   *Macro F1:* `0.3411`
    *   *Dangerous Recall:* `0.4873` (6.5x improvement over Phase 4 RF)
*   **Feature Schema:**
    `['LATITUDE', 'LONGITUDE', 'STATE_ID', 'SAMPLE_DEPTH', 'SALINITY', 'WATER_TEMP', 'Season', 'Year', 'Month', 'Month_sin', 'Month_cos', 'DayOfYear_sin', 'DayOfYear_cos']`
*   **Preprocessing Pipeline:**
    *   Imputation of sample depth with `0.0`
    *   Imputation of salinity/temp via group median (STATE_ID + Month group), with state fallback and global fallback
    *   Creation of indicators `SALINITY_is_missing` and `WATER_TEMP_is_missing`
    *   Standard scaling of numeric features (including indicators)
    *   One-hot encoding for `STATE_ID` and `Season`

---

## 4. Verification Results & Test Status
We performed a systematic load, inference, and serialization audit on the recovered champions.

### 4.1 Artifact Verification
*   **Existence & Load:** Confirmed both `caml_champion.joblib` and `habsos_champion.joblib` load successfully without dependency conflicts.
*   **Feature Alignments:** Verified pipelines execute on data matching the training feature schemas.
*   **Prediction Stability:** Confirmed predictions produce correct outputs and probability distributions sum to exactly `1.0`.
*   **Reproducibility:** Serialized and re-loaded runs produce identical, bit-level predictions.

### 4.2 Test Suite Execution
We implemented a robust test suite in `tests/test_model_recovery.py` consisting of **13 test cases** verifying loader validation, registry alignment, and security boundaries.

All recovery tests **passed** successfully:
```text
Ran 13 tests in 3.050s
OK
```

Total project test status (with Phase 4 skipped due to invalidation):
```text
Ran 25 tests in 0.565s
OK (skipped=3)
```

---

## 5. Registry & Manifest Status
*   **`model_registry.json` Status:** Updated to include all 4 models (2 candidates and 2 invalidated). Status and audit statuses have been locked.
*   **`model_manifest.json` Status:** Created at `models/deployment/model_manifest.json` containing only the active candidates. This manifest acts as the **single source of truth** for the future AIS and backend.

---

## 6. Known Limitations
1.  **Imputation Run-Time Overhead:** HABSOS preprocessing relies on a custom `GroupMedianImputer` which imputes missing salinity/temperature by state and month. This requires a row-by-row lookup for missing indices which, while correct, is slower than global median imputation.
2.  **No Platt Calibration:** The deployment models are uncalibrated. The output probabilities are raw model probabilities (decision boundaries for logistic regression, class vote ratios for random forest) rather than true probability estimates. The future AIS must treat these scores as classification confidence scores, not calibrated risk factors.
