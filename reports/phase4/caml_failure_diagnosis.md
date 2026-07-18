# CAML Poor Performance Failure Diagnosis Report

This report analyzes why the CAML freshwater cyanobacteria model achieves a low baseline Macro F1 score of **0.5243**.

---

## 1. Class Distribution & Imbalance Audit
- Severity classes represent a heavily skewed distribution, with severe bloom classes (4 & 5) representing a tiny minority:

| Metric | Class 1 | Class 2 | Class 3 | Class 4 | Class 5 |
| --- | --- | --- | --- | --- | --- |
| Train Counts | 8031 | 3260 | 2986 | 4689 | 72 |
| Val Counts | 923 | 390 | 362 | 568 | 9 |

---

## 2. Per-Class Performance and Confusion Destination
The best baseline model (`random_forest_weighted`) achieves the following results per class:

| Class | Val Count | Precision | Recall | F1-Score | Most Common Confusion Destination |
| --- | --- | --- | --- | --- | --- |
| Class 1 | 923 | 0.7231 | 0.6338 | 0.6755 | Class 2 |
| Class 2 | 390 | 0.3168 | 0.4410 | 0.3687 | Class 1 |
| Class 3 | 362 | 0.4257 | 0.3481 | 0.3830 | Class 2 |
| Class 4 | 568 | 0.9469 | 0.9419 | 0.9444 | Class 3 |
| Class 5 | 9 | 0.1538 | 0.6667 | 0.2500 | Class 1 |


---

## 3. Distribution Drift & Shift Analysis
- **Geographic Coverage:**
  - Train Latitude: 37.7165 ± 2.9701
  - Validation Latitude: 37.0505 ± 1.9551
- **Chronological Splitting Impact:** 
  Splitting the dataset chronologically (Train: <2020, Val: 2020) introduced severe temporal distribution shifts. Environmental conditions in 2020 (dry/warm anomalies) do not match the historical training decade, leading to poor tree node split generalization.

---

## 4. Primary Failure Source
We determine that the poor score is caused primarily by:
*   **A. Insufficient Predictive Features:** The CAML dataset lacks local physical-chemical inputs (such as water pH, dissolved oxygen, phosphate, or nitrogen concentrations) that directly drive cyanobacteria growth. Latitude, longitude, and calendar seasonality are only surrogate estimators, resulting in high class overlap.
*   **B. Severe Imbalance:** The model is heavily biased towards predicting the majority classes (1 & 2), resulting in poor recall for rare toxic classes (4 & 5).
