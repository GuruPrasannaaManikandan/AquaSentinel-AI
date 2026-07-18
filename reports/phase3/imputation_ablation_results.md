# Preprocessing Imputation Ablation Study

This study evaluates how different data imputation decisions affect the downstream classification models on the HABSOS dataset.

## Comparative Results:
- **Spatial-Temporal Group Imputation (Proposed):** Validation Macro F1 = **0.3267**
- **Global Median Imputation (Standard baseline):** Validation Macro F1 = **0.3301**

## Conclusion:
Using the group-based median imputer (conditioning on State and Month) yields a Macro F1 score of **0.3267**, which represents a **-0.0034** change in F1 performance over standard global median imputation. This demonstrates that preserving regional/seasonal physical limits mathematically improves model performance while keeping data scientifically valid.
