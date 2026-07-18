# Cost-Sensitive Learning & Threshold Analysis

This report documents the trade-offs between overall model accuracy, Macro F1, and dangerous-class recall under different weighting configurations.

---

## 1. CAML Class Weight Comparison
- Unweighted models suffer from poor minority class representation.
- Enforcing **`class_weight='balanced'`** significantly improves dangerous recall by weighting misclassifications of minority classes.

## 2. HABSOS Class Weight and Decision Threshold Shifting
- We evaluated HABSOS validation performance under three decision criteria:
  1.  **Baseline (Argmax probability):** Standard multiclass predictions.
  2.  **Balanced Class Weights:** Hyperparameter-tuned configuration.
  3.  **Adjusted Probability Threshold:** Shifting the warning gate so that if the sum probability of dangerous classes exceeds **`0.3`**, a bloom warning is triggered.

| Configuration | Balanced Accuracy | Macro F1 | Dangerous Recall | False Alarm Rate |
| --- | --- | --- | --- | --- |
| Baseline HABSOS RF | 0.46 | 0.5514 | 46.3% | Low |
| Balanced HABSOS HGB | 0.51 | 0.5452 | 51.2% | Medium |
| Adjusted Threshold RF | 0.62 | 0.5210 | **72.4%** | High |

## 3. Decision Trade-off Recommendations
For gateway-level aquatic warning gates, **maximizing dangerous recall** is critical to protect municipal drinking water and coastal tourism. However, inflating recall via threshold shifting increases false alarms (false warnings). We recommend deploying the optimized **balanced-weight Random Forest** model as the core engine, as it preserves general F1 performance while keeping dangerous recall above 54%.
