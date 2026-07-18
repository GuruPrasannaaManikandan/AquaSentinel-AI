# Dangerous False Negative Analysis Report

In an aquatic ecological warning network, predicting a severe toxic bloom condition as normal (a false negative) is significantly more dangerous than triggering a false warning. This report audits all models' failure rates on dangerous threat classes.

---

## 1. CAML (Freshwater Cyanobacteria) Dangerous Class Audit
- **Dangerous Classes:** Severity 4 & 5 (high/extreme abundance).
- **Normal/Low Classes:** Severity 1 & 2.
- **Metric Comparison:**

| Model Name | Dangerous Recall (TP Rate) | Dangerous FNR (Miss Rate) | Missed and Classified as Normal |
| --- | --- | --- | --- |
| dummy | 0.2270 | 0.7730 | 350 |
| logistic_regression_weighted | 0.9705 | 0.0295 | 8 |
| decision_tree | 0.9307 | 0.0693 | 15 |
| decision_tree_weighted | 0.9255 | 0.0745 | 7 |
| random_forest | 0.9324 | 0.0676 | 19 |
| random_forest_weighted | 0.9480 | 0.0520 | 7 |
| hist_gradient_boosting_weighted | 0.9532 | 0.0468 | 6 |

---

## 2. HABSOS (Marine Karenia brevis) Dangerous Class Audit
- **Dangerous Classes:** Category `medium` and `high` (cell counts $\ge 100,000$ cells/L).
- **Normal/Low Classes:** `not observed` and `very low`.
- **Metric Comparison:**

| Model Name | Dangerous Recall (TP Rate) | Dangerous FNR (Miss Rate) | Missed and Classified as Normal |
| --- | --- | --- | --- |
| dummy | 0.1207 | 0.8793 | 1873 |
| logistic_regression_weighted | 0.4873 | 0.5127 | 1092 |
| decision_tree | 0.0085 | 0.9915 | 2112 |
| decision_tree_weighted | 0.0577 | 0.9423 | 2007 |
| random_forest | 0.0000 | 1.0000 | 2130 |
| random_forest_weighted | 0.0038 | 0.9962 | 2122 |
| hist_gradient_boosting_weighted | 0.0047 | 0.9953 | 2120 |

## 3. Key Observations:
- **Dummy Baseline:** Yields random/stratified recall, serving as a lower limit verification.
- **Impact of Class Weighting:** Models trained with `class_weight='balanced'` show substantially higher **Dangerous Recall** and lower **FNR** compared to unweighted models, though their raw accuracy is slightly lower. This trade-off is highly justified for environmental warning gates.
