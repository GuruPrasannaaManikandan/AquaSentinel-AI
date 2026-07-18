# Evidence-Fusion Philosophy

This document defines the roles of each subsystem and explains the evidence-fusion philosophy used in this Capstone project.

## 1. Role of Subsystems

### 1.1 Supervised Machine Learning (ML)
- **Primary Question:** "What known class does this observation resemble?"
- **Role:** Supervised ML classifiers (Weighted Random Forest for CAML, Weighted Logistic Regression for HABSOS) are optimized to learn complex decision boundaries between known target classes. They provide high-precision hazard classification, distinguishing normal states from warning or critical bloom conditions.
- **Limitation:** Closed-world assumption. They will force out-of-distribution (OOD) or novel telemetry inputs into one of the trained classes, often with high confidence.

### 1.2 Unsupervised Artificial Immune System (AIS)
- **Primary Question:** "Does this observation exhibit non-self or novel structure relative to learned normal conditions?"
- **Role:** The Negative Selection Algorithm (NSA) acts as a novelty filter. It models the multi-dimensional feature space of SELF (normal telemetry) and populates the remaining empty non-self space with random detectors.
- **Limitation:** Naive NSA cannot perform hyperplane classification between overlapping classes. In HABSOS, where physical environmental indicators overlap heavily between classes, random detector generation is highly inefficient at capturing blooms.

### 1.3 Evidence-Fusion Engine
- **Primary Question:** "What operational system state should be emitted given the available evidence and known subsystem limitations?"
- **Role:** The Fusion Engine acts as a transparent, rule-based coordinator. It ingests standardized predictions and confidences from both streams and determines the final system state using a deterministic decision table, taking into account dataset-specific reliability policies.

---

## 2. Final System States
We define exactly four system states:
1.  **NORMAL:** No known hazard suspected by ML, and telemetry is within known-normal bounds (AIS normal).
2.  **WARNING:** ML suspects a moderate threat (warning class), or ML is low-confidence and suspects danger.
3.  **CRITICAL:** ML suspects a high threat (critical class) with medium/high confidence.
4.  **UNKNOWN_ANOMALY:** AIS detects out-of-distribution non-self coordinates while ML does not suspect a known threat. This represents a novel environmental telemetry pattern requiring investigation.
