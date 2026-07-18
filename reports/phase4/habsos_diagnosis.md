# HABSOS Performance Diagnosis Report

This report analyzes why the HABSOS marine red tide model performs substantially better than the CAML model.

---

## 1. Class Distributions
- **HABSOS Target Class Counts:**

| Class Name | Training Count | Validation Count |
| --- | --- | --- |
| `normal` | 159891 | 16364 |
| `warning` | 21679 | 1839 |
| `critical` | 3294 | 291 |

---

## 2. Critical Factors Driving Superior Performance:
1.  **Strong Predictive Features:** Water temperature and salinity are direct physical drivers of *Karenia brevis* growth curves. Unlike CAML (which relies on spatial surrogates), HABSOS physical sensors provide direct biophysical signals.
2.  **Dataset Size:** HABSOS has over **185k training records**, allowing tree models to form highly detailed splits compared to CAML's smaller sample size.
3.  **High Spatial Density:** Coastal monitoring in Florida is highly clustered around historical bloom centers. The spatial coordinate density allows coordinate-based decision splits to generalizes robustly to validation records.
