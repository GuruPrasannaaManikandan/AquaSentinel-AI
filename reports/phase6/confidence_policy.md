# Machine Learning Confidence Policy

This document establishes operational confidence bands derived from validation prediction confidence distributions for correct and incorrect classifications.

## 1. Validation Confidence Analysis

### 1.1 CAML (Freshwater)
- **Correct Predictions:** Mean confidence = `0.6725`, Median = `0.6507`. 75% of correct predictions have confidence $> 0.459$.
- **Incorrect Predictions:** Mean confidence = `0.4624`, Median = `0.4308`. 75% of incorrect predictions are below `0.487`.
- **Operational Bands:**
  - **LOW CONFIDENCE:** $< 0.50$ (where incorrect predictions are highly concentrated).
  - **MEDIUM CONFIDENCE:** $[0.50, 0.80)$ (moderate likelihood of correctness).
  - **HIGH CONFIDENCE:** $\ge 0.80$ (highly reliable classifications).

### 1.2 HABSOS (Marine)
- **Correct Predictions:** Mean confidence = `0.6367`, Median = `0.6165`. 75% of correct predictions have confidence $> 0.509$.
- **Incorrect Predictions:** Mean confidence = `0.4565`, Median = `0.4376`. 75% of incorrect predictions are below `0.486`.
- **Operational Bands:**
  - **LOW CONFIDENCE:** $< 0.50$ (where incorrect predictions are concentrated).
  - **MEDIUM CONFIDENCE:** $[0.50, 0.70)$ (moderate likelihood).
  - **HIGH CONFIDENCE:** $\ge 0.70$ (highly reliable classifications).
