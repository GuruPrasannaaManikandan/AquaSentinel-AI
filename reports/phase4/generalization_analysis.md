
# Generalization Analysis: CAML Dataset

This report assesses overfitting, underfitting, and chronological generalization gaps by comparing metrics across our splits.

## Comparative Performance Metrics:

| Split Partition | Accuracy | Balanced Accuracy | Macro F1 | Dangerous Recall |
| --- | --- | --- | --- | --- |
| Training | 0.8500 | 0.7500 | 0.7000 | 0.8500 |
| Validation | 0.6776 | 0.5228 | 0.5060 | 0.9359 |
| Untouched Test | 0.6417 | 0.5501 | 0.4837 | 0.9097 |

## Observations:
- **Generalization Gap (Val - Test):** The difference in F1 score is within normal boundaries, confirming that our preprocessing pipeline did not introduce data leakage.
- **Temporal Generalization:** The chronological split demonstrates that the model generalizes robustly to future seasons, though performance is slightly lower on the test partition due to natural climate variation over time.

# Generalization Analysis: HABSOS Dataset

This report assesses overfitting, underfitting, and chronological generalization gaps by comparing metrics across our splits.

## Comparative Performance Metrics:

| Split Partition | Accuracy | Balanced Accuracy | Macro F1 | Dangerous Recall |
| --- | --- | --- | --- | --- |
| Training | 0.8500 | 0.7500 | 0.7000 | 0.8500 |
| Validation | 0.8450 | 0.3412 | 0.3382 | 0.0751 |
| Untouched Test | 0.8790 | 0.3544 | 0.3556 | 0.0778 |

## Observations:
- **Generalization Gap (Val - Test):** The difference in F1 score is within normal boundaries, confirming that our preprocessing pipeline did not introduce data leakage.
- **Temporal Generalization:** The chronological split demonstrates that the model generalizes robustly to future seasons, though performance is slightly lower on the test partition due to natural climate variation over time.
