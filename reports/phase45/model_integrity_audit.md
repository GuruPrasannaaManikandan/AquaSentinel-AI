# Forensic Model Integrity & Performance Audit Report

This report presents a forensic investigation of the performance metrics, model lineages, and discrepancies identified between the baseline models (Phase 3) and the final optimized models (Phase 4).

---

## 1. Metric Inconsistency Analysis

### Why are there three different sets of reported metrics?
The three sets of reported metrics arose from three distinct milestones in the codebase development, target mappings, and hardcoded placeholders:

1.  **Set A (Phase 3 Baseline):** Represents the initial evaluation of the uncalibrated baseline classifiers trained on the 3-class target mapping. For HABSOS, the baseline champion was `logistic_regression_weighted` (Macro F1 = 0.3411, Dangerous Recall = 0.4873).
2.  **Set B (Earlier Phase 4 / Phase 3 5-Class Run):** Represents metrics from an earlier pipeline run where the HABSOS target had not yet been mapped to 3 classes (maintaining 5 raw classes). In this state, HABSOS `random_forest_weighted` achieved a validation Macro F1 of `0.1887` and Dangerous Recall of `0.0000`. These metrics were mistakenly reported as the "Earlier Phase 4" baseline.
3.  **Set C (Current Phase 4 Final):** Represents the metrics of the fully tuned, calibrated, and threshold-shifted models (wrapped inside `ThresholdShiftClassifier` with a threshold of `0.2`) on the final 3-class datasets.

### Script Execution and Model Mapping
The following table maps the exact script execution and serialized models to each reported metric set:

| Metric Set | Script / Log Entry | Model File Path | Target Classes | CAML Metrics (F1 / Recall) | HABSOS Metrics (F1 / Recall) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Set A** (Phase 3 Champion) | `run_phase3.py` (Log: `2026-07-08 00:41:15`) | None (represented by baseline metrics) | 3 classes | 0.5243 / 0.9480 (RF) | 0.3411 / 0.4873 (LR) |
| **Set B** (Earlier Phase 4) | `run_phase3.py` (Log: `2026-07-08 00:06:34`) | `models/random_forest_weighted` (5-class) | 5 classes | 0.5243 / 0.9480 (RF) | 0.1887 / 0.0000 (RF) |
| **Set C** (Current Phase 4) | `run_phase4.py` (Log: `2026-07-08 00:42:18`) | `models/habsos_final_model.joblib` | 3 classes | 0.5060 / 0.9359 (RF+Cal+Thresh) | 0.3382 / 0.0751 (RF+Cal+Thresh) |

*Note: The Macro F1 score of `0.5514` for HABSOS reported in `reports/phase4/cost_sensitive_analysis.md` was a hardcoded placeholder text inside `run_phase4.py` (Line 457) and does not represent any actual model execution on the processed validation set.*

---

## 2. Reconstructed Model Lineage

### HABSOS Pipeline Reconstructed
The lineage of the HABSOS pipeline across the stages is as follows:

*   **Stage 1: Phase 3 Baseline**
    *   *Algorithm:* Weighted Logistic Regression (`logistic_regression_weighted`)
    *   *Hyperparameters:* `C=1.0`, `solver='lbfgs'`, `multi_class='multinomial'`, `class_weight='balanced'`
    *   *Preprocessing:* Conditional median imputation by `STATE_ID` + `Month` -> scaling -> one-hot encoding ([preprocessing.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/data/preprocessing.py#L30))
    *   *Calibration Method:* None
    *   *Threshold Rule:* Argmax
    *   *Validation Performance:* Accuracy = `0.6758`, Balanced Accuracy = `0.4613`, Macro F1 = `0.3411`, Dangerous Recall = `0.4873` (Log: `logs/phase3.log#L206`)
*   **Stage 2: Phase 4 Tuned Model**
    *   *Algorithm:* Random Forest Classifier
    *   *Hyperparameters:* `n_estimators=50`, `max_depth=8`, `min_samples_split=5`, `class_weight='balanced'` ([run_phase4.py#L744](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/run_phase4.py#L744))
    *   *Preprocessing:* Same as baseline
    *   *Calibration Method:* None
    *   *Threshold Rule:* Argmax
    *   *Validation Performance:* Macro F1 = `0.3627` (Log: `logs/phase4.log#L83`)
*   **Stage 3: Calibrated Model**
    *   *Algorithm:* CalibratedClassifierCV wrapping Tuned RF
    *   *Hyperparameters:* Same as Stage 2 base RF
    *   *Calibration Method:* Sigmoid (Platt scaling) with `cv='prefit'` ([run_phase4.py#L380](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/run_phase4.py#L380))
    *   *Threshold Rule:* Argmax
    *   *Validation Performance:* Unreported (intermediate stage)
*   **Stage 4: ThresholdShiftClassifier**
    *   *Algorithm:* `ThresholdShiftClassifier` wrapping Calibrated RF
    *   *Threshold Rule:* Pred warning class if sum of `['warning', 'critical']` probabilities > `0.2` ([run_phase4.py#L780](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/run_phase4.py#L780))
    *   *Validation Performance:* Accuracy = `0.8450`, Balanced Accuracy = `0.3412`, Macro F1 = `0.3382`, Dangerous Recall = `0.0751` ([generalization_analysis.md#L27](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/reports/phase4/generalization_analysis.md#L27))
*   **Stage 5: Locked Final Model**
    *   *Algorithm / Specs:* Same as Stage 4; serialized in `models/habsos_final_model.joblib`.

### CAML Pipeline Reconstructed
The lineage of the CAML pipeline across the stages is as follows:

*   **Stage 1: Phase 3 Baseline**
    *   *Algorithm:* Weighted Random Forest (`random_forest_weighted`)
    *   *Hyperparameters:* `n_estimators=100`, `max_depth=12`, `min_samples_split=5`, `class_weight='balanced'`
    *   *Preprocessing:* Global median imputation -> scaling -> one-hot encoding
    *   *Calibration Method:* None
    *   *Threshold Rule:* Argmax
    *   *Validation Performance:* Accuracy = `0.6323`, Balanced Accuracy = `0.6063`, Macro F1 = `0.5243`, Dangerous Recall = `0.9480` ([caml_model_comparison.csv#L7](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/reports/phase3/caml_model_comparison.csv#L7))
*   **Stage 2: Phase 4 Tuned Model**
    *   *Algorithm:* Random Forest Classifier
    *   *Hyperparameters:* `n_estimators=50`, `max_depth=14`, `min_samples_split=5`, `class_weight='balanced'` ([run_phase4.py#L742](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/run_phase4.py#L742))
    *   *Calibration Method:* None
    *   *Threshold Rule:* Argmax
    *   *Validation Performance:* Macro F1 = `0.5225` (Log: `logs/phase4.log#L78`)
*   **Stage 3: Calibrated Model**
    *   *Algorithm:* CalibratedClassifierCV wrapping Tuned RF
    *   *Calibration Method:* Sigmoid with `cv='prefit'`
    *   *Threshold Rule:* Argmax
    *   *Validation Performance:* Unreported (intermediate stage)
*   **Stage 4: ThresholdShiftClassifier**
    *   *Algorithm:* `ThresholdShiftClassifier` wrapping Calibrated RF
    *   *Threshold Rule:* Pred warning class if sum of `[4, 5]` probabilities > `0.2` ([run_phase4.py#L776](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/run_phase4.py#L776))
    *   *Validation Performance:* Accuracy = `0.6776`, Balanced Accuracy = `0.5228`, Macro F1 = `0.5060`, Dangerous Recall = `0.9359` ([generalization_analysis.md#L11](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/reports/phase4/generalization_analysis.md#L11))
*   **Stage 5: Locked Final Model**
    *   *Algorithm / Specs:* Same as Stage 4; serialized in `models/caml_final_model.joblib`.

---

## 3. Analysis of HABSOS Regression & Performance Collapse

### Why did HABSOS Macro F1 drop and dangerous recall collapse to 7.51%?
1.  **Architecture Swapping:** The primary driver of this regression is that the Phase 4 optimization script ([run_phase4.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/run_phase4.py)) **completely excluded Logistic Regression** from the hyperparameter search space, only tuning Random Forest and HistGradientBoosting. Random Forest was selected solely based on validation Macro F1 score, ignoring that tree-based models suffer from severe majority-class bias on unseen chronological splits.
2.  **Overfitting of Trees:** HABSOS Random Forest baseline in Phase 3 already had a dangerous recall of `0.0038` (near-zero recall). Hyperparameter tuning did not resolve this fundamental generalization failure.
3.  **Impact of Calibration:** Fitting `CalibratedClassifierCV` on the highly skewed validation set compressed the probability estimates of rare minority classes towards zero. This scaling bias made it impossible for the subsequent decision gate to activate warnings.
4.  **Impact of ThresholdShiftClassifier:** The `ThresholdShiftClassifier` actually cushioned the degradation; without it, the calibrated RF model's recall would have been `0.0000`. By setting a threshold of `0.2`, the recall was marginally elevated to `0.0751`, but this is still a total failure compared to Logistic Regression's `0.4873`.

---

## 4. Pipeline & Statistical Leakage Audit

### Target Label & Metric Definitions
*   **Did target labels or dangerous-class definitions change?** No. The target categories for HABSOS were mapped to `normal`, `warning`, and `critical` during Phase 2 preprocessing ([run_phase2.py#L78-L85](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/run_phase2.py#L78-L85)). However, the Phase 3 report template hardcoded old raw category names (`medium`, `high`) in its text, creating confusion, while the code correctly computed metrics on `['warning', 'critical']`.
*   **Did metric calculation code change?** No. The code in [evaluate.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/models/evaluate.py#L14) remained identical.

### Dataset and Split Audit
*   **Are Phase 3 and Phase 4 metrics calculated on the same validation dataset?** Yes, both phases loaded `data/processed/caml_val.csv` and `data/processed/habsos_val.csv`.
*   **PredefinedSplit Verification:** PredefinedSplit combined the training and validation sets strictly using indices `-1` for train and `0` for validation ([run_phase4.py#L300-L304](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/run_phase4.py#L300-L304)). This did not cause any training data leakage.
*   **Refit Audit:** `refit=False` was passed to `RandomizedSearchCV` ([run_phase4.py#L328](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/run_phase4.py#L328)). The script manually fit a new estimator strictly on the training partition (`X_train_trans`), preventing validation data leakage into the model parameters.
*   **Calibration Data Leakage: YES!** 
    In [run_phase4.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/run_phase4.py#L766-L767), probability calibration was fit on the validation partition (`X_val_trans`, `y_val`). Subsequently, the threshold search and validation metrics reporting were evaluated on this *exact same validation set*. Reusing the validation partition to fit the Platt scaling model and search for optimal thresholds introduced severe statistical bias.

---

## 5. Model Comparison and Recommendations

### Comparison: Phase 3 Champion vs. Phase 4 Final Model
*   **CAML:**
    *   *Phase 3 Champion (`random_forest_weighted`):* Macro F1 = `0.5243`, Dangerous Recall = `0.9480`
    *   *Phase 4 Final (`ThresholdShiftClassifier`):* Macro F1 = `0.5060`, Dangerous Recall = `0.9359`
    *   *Verdict:* Phase 3 champion is superior (slightly better F1 and recall, no calibration bias).
*   **HABSOS:**
    *   *Phase 3 Champion (`logistic_regression_weighted`):* Macro F1 = `0.3411`, Dangerous Recall = `0.4873`
    *   *Phase 4 Final (`ThresholdShiftClassifier`):* Macro F1 = `0.3382`, Dangerous Recall = `0.0751`
    *   *Verdict:* Phase 3 champion is vastly superior. It maintains similar Macro F1 while delivering a **6.5x higher dangerous recall**.

### Conclusion
*   **Which existing model is currently objectively better?** 
    For both datasets, the **Phase 3 champion models** (`random_forest_weighted` for CAML and `logistic_regression_weighted` for HABSOS) are objectively superior.
*   **Is Phase 4 valid?** **NO.** The selection of Random Forest for HABSOS completely collapsed the safety-critical recall metric, and calibration fitting leaked the validation set.
