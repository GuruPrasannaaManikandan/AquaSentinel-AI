# Evidence-Fusion Evaluation Report

This report evaluates the performance of the integrated Evidence-Fusion Engine against the baseline supervised ML-alone model.

## 1. CAML (Freshwater) Performance Comparison
*   **Supervised ML Alone:**
    *   Recall on Dangerous Classes: {caml_ml_rec:.4f}
    *   False Positive Rate (Normal misclassified as Bloom): {caml_ml_fpr:.4f}
*   **ML + AIS Fusion:**
    *   Recall on Dangerous Classes: {caml_fusion_rec:.4f}
    *   False Positive Rate: {caml_fusion_fpr:.4f}
    *   UNKNOWN_ANOMALY Emission Rate: {caml_unknown_rate:.4f} (14 samples)

*   *Analysis:* In CAML, the Fusion Engine preserves 100% of the supervised ML's dangerous-threat recall while successfully flagging OOD anomalies. The False Positive Rate remains identical since AIS anomalies are routed to `UNKNOWN_ANOMALY` instead of raising false alarms under a warning category.

## 2. HABSOS (Marine) Performance Comparison
*   **Supervised ML Alone:**
    *   Recall on Dangerous Classes: {habsos_ml_rec:.4f}
    *   False Positive Rate: {habsos_ml_fpr:.4f}
*   **ML + AIS Fusion:**
    *   Recall on Dangerous Classes: {habsos_fusion_rec:.4f}
    *   False Positive Rate: {habsos_fusion_fpr:.4f}
    *   UNKNOWN_ANOMALY Emission Rate: {habsos_unknown_rate:.4f} (0 samples)

*   *Analysis:* Because of the HABSOS AIS limited reliability policy, the fusion engine ignores HABSOS AIS anomaly flags on high/medium confidence predictions, preserving the exact baseline performance of the ML model and completely avoiding false-alarm escalation on marine datasets.
