# Error Analysis Report

This report analyzes incorrectly classified validation observations, focusing on patterns related to seasons, location, and data imputation.

## 1. HABSOS Misclassification Audits
- **Total Validation Rows:** 18494
- **Total Misclassified Rows:** 2866 (Error Rate: 15.50%)

### Imputation and Errors:
- **Imputed Salinity rate among Errors:** 55.23%
- **Imputed Salinity rate among Correct Predictions:** 40.27%

*Insight:* The error rate is higher on records where salinity/temperature values were missing and imputed. This indicates that while custom group-based imputation preserves physics, missing field data remains a key challenge for prediction accuracy.

## 2. Common Spatial-Temporal Error Patterns:
- Misclassifications are most common in transition seasons (Spring and Autumn) where water temperature thresholds fluctuate rapidly.
- Boundary errors (e.g., predicting 'medium' when the true label is 'high' or 'low') are more common than extreme errors (e.g., predicting 'not observed' when the true label is 'high').
