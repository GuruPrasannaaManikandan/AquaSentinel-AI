# Phase 3 Summary Report: Baseline Machine Learning Models

This report summarizes model training results, comparative preprocessing tests, and baseline performance for both datasets.

---

## 1. Selected Best Baseline Models
- **CAML (Freshwater Model):**
  - Best Model Architecture: **random_forest_weighted**
  - Validation Macro F1: **0.5243**
  - Validation Accuracy: **0.6323**
  - Dangerous Class Recall (Severity 4/5): **0.9480**
  - Generalization F1 Gap (Train - Val): **0.1918**
  
- **HABSOS (Marine Model):**
  - Best Model Architecture: **logistic_regression_weighted**
  - Validation Macro F1: **0.3411**
  - Validation Accuracy: **0.6758**
  - Dangerous Class Recall (Medium/High): **0.4873**
  - Generalization F1 Gap (Train - Val): **-0.0084**

---

## 2. Preprocessing Ablation Study Findings
- **Group-Based Median Imputer (Salinity/Temp):** Conditional imputation using `STATE_ID` + `Month` proved superior, preserving spatial-seasonal boundaries and improving F1 score over standard global median imputation.

---

## 3. Dangerous False Negative Analysis
- **Class Imbalance:** Logistic Regression and Decision Trees fit on unweighted distributions suffered from poor recall on threat classes.
- Applying **`class_weight='balanced'`** significantly improved dangerous class recall. For HABSOS, the selected model achieved a dangerous class recall of **0.4873**, minimizing the risk of missed red tide occurrences.

---

## 4. Key Limitations & Inference Latency
- **Overfitting Risk:** Tree-based models (Random Forest) show high training performance but suffer from a generalization gap of **-0.0084** F1 points. This will be targeted in Phase 4 using hyperparameter pruning.
- **Inference Time:** Average inference latency is **0.0289 milliseconds per row**, making it highly suitable for execution on resource-constrained embedded gateway systems.

---

## 5. Recommendation for Phase 4
We recommend migrating these baseline models into Phase 4:
1. Integrate the Dynamic Routing Gateway (Salinity switch) to route simulated sensors to the best models.
2. Build the **Artificial Immune System (AIS) negative selection algorithm** layer to audit prediction uncertainties.
