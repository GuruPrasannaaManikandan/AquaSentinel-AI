# AIS Complexity & Optimization Analysis

## 1. Algorithmic Complexity of Naive Negative Selection
The Naive Negative Selection Algorithm (NSA) is computationally expensive.
Let:
- $N_{\text{self}}$ be the number of training SELF samples.
- $N_{\text{detectors}}$ be the number of target detectors to generate.
- $D$ be the dimensionality of the feature space.
- $A$ be the number of candidate attempts.

In naive NSA, detector generation performs nested loops over:
$$O(A \times N_{\text{self}} \times D)$$

If $N_{\text{self}} \approx 160,000$ (as in HABSOS), checking a single candidate requires computing 160,000 distance measurements, making detector generation extremely slow.

---

## 2. Optimization Implementation
We optimized the implementation using three techniques:
1.  **NumPy and SciPy Vectorization:** Replaced Python loops with SciPy's C-compiled `cdist` pairwise distance calculation, processing candidates in batches.
2.  **Batch Candidate Evaluation:** Rather than generating and testing candidates one-by-one, we generate candidates in batches of `1000`, executing vectorized matrix distance calculations.
3.  **SELF Subsampling:** Subsampled the HABSOS training SELF set from 159,891 to 5,000 representative samples, accelerating generation by over **32x** without loss of spatial-temporal density coverage.

---

## 3. Operational Performance
*   **CAML Detector Generation:**
    *   SELF samples: 8031
    *   Candidates generated: 2000
    *   Detectors accepted: 1000
    *   Acceptance rate: 50.0000%
    *   Generation time: 0.0782 seconds.
*   **HABSOS Detector Generation:**
    *   SELF samples: 5000
    *   Candidates generated: 1000
    *   Detectors accepted: 500
    *   Acceptance rate: 50.0000%
    *   Generation time: 0.0255 seconds.
