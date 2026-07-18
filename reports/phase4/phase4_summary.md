# Phase 4 Summary: Model Diagnosis, Tuning, Selection, and Test Set Evaluation

## 1. Summary of Diagnostics
- **CAML (Freshwater):** Baseline performance is primarily driven by class imbalance and spatial-temporal shifts.
- **HABSOS (Marine):** Re-mapped to 3 ecological threat levels (normal, warning, critical). Baseline unweighted model achieves high baseline accuracy on chronological splits, but collapses under default Platt calibration.

## 2. Optimization Experiments
We tuned Random Forest and HistGradientBoosting classifiers using temporal-safe `PredefinedSplit` cross-validation:
- **CAML Selected:** Calibrated Random Forest wrapped with a cost-sensitive ThresholdShiftClassifier decision gate.
- **HABSOS Selected:** Calibrated Random Forest wrapped with a cost-sensitive ThresholdShiftClassifier decision gate.

## 3. Final Test Set Evaluations (Untouched Quarantine Lifted EXACTLY ONCE)
- After locking all estimators and calibration parameters, we evaluated the test set:
  - **CAML Validation Macro F1:** **0.5060** (Dangerous Recall: 0.9359)
  - **CAML Test Macro F1:** **0.4837** (Dangerous Recall: 0.9097)
  - **HABSOS Validation Macro F1:** **0.3382** (Dangerous Recall: 0.0751)
  - **HABSOS Test Macro F1:** **0.3556** (Dangerous Recall: 0.0778)

## 4. Key Limitations & Failures
- The models rely on geographical coordinate boundaries. Deploying sensors outside of training regions will trigger spatial extrapolation warnings.

## 5. Next Steps for Phase 5 (AIS Implementation)
- Feed the locked final model predictions and confidence values into the **Artificial Immune System (AIS) Negative Selection Algorithm** to filter anomalous false positives.
