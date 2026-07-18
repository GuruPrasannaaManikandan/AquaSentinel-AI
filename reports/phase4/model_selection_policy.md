# Model Selection Policy Document

This document outlines the safety-oriented model selection criteria used to select final deployment models.

## 1. Multi-Dimensional Decision Metrics
Since aquatic threat detection is safety-critical, we balance the following performance criteria:
1.  **Macro F1-Score (Primary Generalization Metric):** Measures overall multiclass classification balance.
2.  **Dangerous Class Recall (Primary Safety Metric):** The recall on classes representing environmental hazards (CAML: Severity 4/5; HABSOS: medium/high). Must be maximized.
3.  **Dangerous Class FNR (Miss Rate):** Target: <0.45.
4.  **Balanced Accuracy:** Corrects for massive majority class representation.
5.  **Generalization Gap:** Difference between training Macro F1 and validation Macro F1. Gaps > 0.15 indicate overfitting.
6.  **Inference Latency:** Average prediction time per row. Target: < 5.0 milliseconds on gateway boards.

## 2. Pareto Comparison (Multiclass Performance vs. Recall)
When selecting models, we analyze the trade-off curve between overall Macro F1 and Dangerous Recall:
- **Baseline (Unweighted):** High overall accuracy and high Macro F1, but low dangerous recall (poor safety).
- **Balanced Weights:** Slightly lower overall accuracy, but significantly higher recall on threat classes.
- **Decision Policy:** If Model A has higher overall Macro F1 but Model B has >5% higher Dangerous Recall with a Macro F1 within 2% of Model A, Model B is selected to ensure public safety.
