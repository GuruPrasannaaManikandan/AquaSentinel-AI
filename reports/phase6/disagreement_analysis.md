# Subsystem Agreement & Disagreement Analysis

This report analyzes the consistency and contradictions between the supervised ML classifications and unsupervised AIS anomaly flags across the validation datasets.

## 1. CAML Validation (2,252 samples)
- **Agreement Count (Both normal or both anomalous):** 2076 ({caml_agree_rate:.2%})
- **Disagreement Count:** 176 ({caml_disagree_rate:.2%})
- **ML Normal + AIS Anomaly (Suspected Novelty):** 14
- **ML Dangerous + AIS Normal (Suspected Bloom in known bounds):** 162

## 2. HABSOS Validation (18,494 samples)
- **Agreement Count (Both normal or both anomalous):** 13211 ({habsos_agree_rate:.2%})
- **Disagreement Count:** 5283 ({habsos_disagree_rate:.2%})
- **ML Normal + AIS Anomaly:** 0
- **ML Dangerous + AIS Normal:** 5283

## 3. Final State Distributions
- **CAML final states:**
  - NORMAL: 1634
  - WARNING: 604
  - CRITICAL: 0
  - UNKNOWN_ANOMALY: 14
- **HABSOS final states:**
  - NORMAL: 13211
  - WARNING: 2010
  - CRITICAL: 3273
  - UNKNOWN_ANOMALY: 0

## 4. Analytical Observations
- **CAML Disagreement:** In CAML, the disagreement rate is relatively low. The 14 cases of ML Normal + AIS Anomaly were successfully escalated to `UNKNOWN_ANOMALY` by the Fusion Engine.
- **HABSOS Disagreement:** In HABSOS, the AIS registered zero anomalies under locked parameters (FPR=0.0%), meaning HABSOS AIS remains 100% normal. Hence, agreement rate is governed strictly by whether ML predicts normal. No HABSOS validation cases triggered `UNKNOWN_ANOMALY`.
