# Final Metric Lineage Audit Report

This report presents a forensic audit of the Capstone project's metrics, tracking historical changes, identifying placeholders, and defining the verified lineage.

## 1. Freshwater (CAML) Metrics Reconciliation

During development, several different CAML performance metrics were reported:
*   **Macro F1 = 0.5243:** This is the **correct and verified validation Macro F1** of the Phase 3 Weighted Random Forest champion model, as logged in [model_manifest.json](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/models/deployment/model_manifest.json).
*   **Macro F1 = 0.4837 / 0.5060:** These belonged to baseline unweighted Random Forest candidates evaluated during early Phase 3 training.
*   **Macro F1 = 0.3014:** This was a typo or a metric belonging to an early HABSOS candidate before correct mapping.
*   **ML Metric = 0.6323:** This represents the **correct validation accuracy** of the active CAML champion.
*   **Dangerous Recall = 0.9480:** This is the **correct and verified validation recall** on dangerous bloom classes (4 and 5), confirming the high sensitivity of the champion model.
*   **Dangerous Recall = 0.9097:** This was a threshold search metric from Phase 4, which has been invalidated.

---

## 2. Marine (HABSOS) Metrics Reconciliation

HABSOS metrics reported historically were resolved as follows:
*   **Macro F1 = 0.3411 (previously close to 0.3382 / 0.3556):** The **verified validation Macro F1** for the Phase 3 Weighted Logistic Regression champion is `0.3411`, as defined in the deployment manifest.
*   **Macro F1 = 0.1887:** This was the validation Macro F1 of the HABSOS Negative Selection Algorithm (NSA).
*   **Macro F1 = 0.5514:** This was the Macro F1 of the CAML Negative Selection Algorithm (NSA).
*   **ML Metric = 0.6758:** This represents the **correct validation accuracy** of the active HABSOS champion.
*   **Dangerous Recall = 0.4873:** The **verified validation recall** on warning/critical classes for the HABSOS champion is `0.4873`.
*   **Dangerous Recall = 0.0778:** This was an early uncalibrated threshold model performance and is inactive.

---

## 3. Verified Performance Source

All verified metrics are consolidated in [final_verified_metrics.json](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/reports/phase9/final_verified_metrics.json) and serve as the single source of truth for release packaging.
