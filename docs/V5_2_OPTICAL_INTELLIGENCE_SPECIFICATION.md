# V5.2 — Advanced Optical Quality & Multi-Frame Vision Specification

**Document Version:** 1.0.0  
**Status:** VERIFIED & RELEASE-READY  
**Baseline:** V5.1 / V4.8.6 Verified Baseline  
**Target Systems:** Multimodal Aquatic AI Runtime & CV Subsystem  

---

## 1. Executive Summary & Purpose

The **IoT-Based Artificial Immune System for Aquatic Ecosystems** employs a multimodal sensing architecture combining physical water chemistry probes with edge camera imagery. The V4.x baseline integrated an AI-Thinker ESP32-CAM and a trained PyTorch `MobileNetV3-Small` classifier (trained on 438 labeled static aquatic images across `NORMAL_WATER`, `ALGAL_BLOOM`, and `TURBID_DISCOLORATION`).

However, prior to V5.2, single-frame visual classification had two critical vulnerabilities:
1. **Optical Vulnerability:** Poor optical conditions (severe blur, lens occlusions, glare/overexposure, underexposure/darkness, or flat non-informative frames) could lead to erratic or overconfident model inferences without an explicit measure of image reliability.
2. **Temporal Brittleness:** An isolated transient visual disturbance (e.g., floating debris, temporary water glint, or a single noisy frame) could falsely assert bloom risk, triggering downstream multimodal FSM escalation.

**V5.2 — Advanced Optical Quality & Multi-Frame Vision** closes these vulnerabilities without replacing or retraining the verified MobileNetV3 model:
- Implements an objective optical quality evaluation engine producing $Q_{visual} \in [0.0, 1.0]$.
- Disables reliance on degraded visual evidence by weighting model confidence into an `effective_confidence = raw_confidence * Q_visual`.
- Introduces a sliding window temporal evidence buffer ($K=3$) that suppresses single transient bloom frames (`TRANSIENT_BLOOM`) and flags oscillating sequences (`AMBIGUOUS`).
- Preserves complete data provenance and raw model confidence for forensic auditing.
- Operates in complete harmony alongside V5.1 Sensor Quality ($Q_{sensor} \in [0.0, 1.0]$).

---

## 2. Mathematical Foundations of Optical Quality

The optical assessment pipeline evaluates frames across three independent optical dimensions using discrete pixel analysis before downstream inference.

### 2.1 Sharpness & Focus Assessment (Discrete Laplacian Variance)
Focus is measured via the variance of the 2D discrete Laplacian operator applied to the 8-bit grayscale luminance array $Y(x, y)$:

$$\nabla^2 Y(x, y) = Y(x+1, y) + Y(x-1, y) + Y(x, y+1) + Y(x, y-1) - 4 Y(x, y)$$

The sharpness metric $\sigma^2_{Lap}$ is computed over all valid interior pixels:

$$\sigma^2_{Lap} = \mathrm{Var}\left( \nabla^2 Y \right) = \frac{1}{N} \sum_{x, y} \left( \nabla^2 Y(x, y) - \mu_{\nabla^2 Y} \right)^2$$

- **Blur Threshold:** $\sigma^2_{blur} = 10.0$
- **Sharp Threshold:** $\sigma^2_{sharp} = 20.0$ (calibrated for fluid, soft aquatic textures)
- **Sharpness Score:**
  $$s_{sharp} = \begin{cases} 
  \max\left(0.10, \frac{\sigma^2_{Lap}}{\sigma^2_{blur}} \times 0.60\right) & \text{if } \sigma^2_{Lap} < \sigma^2_{blur} \implies \text{flag } \texttt{"BLURRED"} \\
  1.0 & \text{if } \sigma^2_{Lap} \ge \sigma^2_{sharp} \\
  0.60 + 0.40 \cdot \frac{\sigma^2_{Lap} - \sigma^2_{blur}}{\sigma^2_{sharp} - \sigma^2_{blur}} & \text{otherwise}
  \end{cases}$$

### 2.2 Exposure Assessment (Luminance Histogram & Saturation Fraction)
Luminance is derived via standard ITU-R BT.601 perceptual weights:
$$Y = 0.299 R + 0.587 G + 0.114 B$$

Mean luminance $\mu_Y$ and saturation fraction $f_{sat}$ are measured:
$$f_{sat} = \frac{\sum \mathbb{I}(Y \ge 250)}{N}$$

- **Darkness Floor:** $\mu_Y < 30.0 \implies \text{flag } \texttt{"DARK"}$
- **Overexposure Ceiling:** $\mu_Y > 225.0 \text{ or } f_{sat} > 0.60 \implies \text{flag } \texttt{"OVEREXPOSED"}$
- **Ideal Range:** $\mu_Y \in [80.0, 180.0]$
- **Exposure Score:** Quadratic Gaussian decay outside the optimal window:
  $$s_{exp} = \exp\left( - \frac{(\mu_Y - \mu_{opt})^2}{2 \sigma_{exp}^2} \right)$$

### 2.3 Contrast & Information Entropy (Shannon Entropy)
Information richness and dynamic range are quantified by the Shannon entropy $H(Y)$ of the 256-bin grayscale histogram $p(i)$:

$$H(Y) = - \sum_{i=0}^{255} p(i) \log_2 p(i) \quad \text{[bits]}$$

- **Entropy Threshold:** $H_{min} = 0.10 \text{ bits}$ (flat sensor readout or solid lens cap yields $H \approx 0$)
- **Standard Deviation Floor:** $\sigma_Y < 1.0$
- **Low Information Flag:** $H(Y) < 0.10 \text{ or } \sigma_Y < 1.0 \implies \text{flag } \texttt{"LOW_INFORMATION"}$

---

## 3. Composite Optical Quality Metric ($Q_{visual}$)

The overall optical quality score $Q_{visual} \in [0.0, 1.0]$ combines component scores via configurable weights:

$$Q_{visual}^{base} = w_{sharp} s_{sharp} + w_{exp} s_{exp} + w_{cont} s_{cont}$$

Where:
- $w_{sharp} = 0.40$
- $w_{exp} = 0.35$
- $w_{cont} = 0.25$

### Severity Discounts & State Classification
- **Severe Lighting Faults:** If flagged $\texttt{"DARK"}$ or $\texttt{"OVEREXPOSED"}$, $Q_{visual} = Q_{visual}^{base} \times 0.60$.
- **Corrupted Frame:** If payload is unreadable, corrupted, or non-image data, $Q_{visual} = 0.0$.
- **Quality States:**
  $$S_{quality} = \begin{cases}
  \texttt{"RELIABLE"} & Q_{visual} \ge 0.85 \\
  \texttt{"ACCEPTABLE"} & 0.65 \le Q_{visual} < 0.85 \\
  \texttt{"DEGRADED"} & 0.40 \le Q_{visual} < 0.65 \\
  \texttt{"UNRELIABLE"} & 0.0 < Q_{visual} < 0.40 \\
  \texttt{"CORRUPTED"} & Q_{visual} = 0.0
  \end{cases}$$

---

## 4. Multi-Frame Temporal Windowing ($K=3$)

The temporal buffer maintains a sliding FIFO deque of up to $K=3$ consecutive inference records:

$$\mathcal{B} = \left\{ (\mathbf{x}_{t-2}, y_{t-2}), (\mathbf{x}_{t-1}, y_{t-1}), (\mathbf{x}_t, y_t) \right\}$$

### Temporal Consistency Rules
1. **Consistent Bloom:** All $K=3$ frames classify as `ALGAL_BLOOM` with mean $Q_{visual} \ge 0.65$.
   $$\text{State} = \texttt{"CONSISTENT_BLOOM"}, \quad C_{temp} = 1.0$$
2. **Consistent Normal / Turbid:** Unanimous classification over window.
   $$\text{State} \in \{\texttt{"CONSISTENT_NORMAL"}, \texttt{"CONSISTENT_TURBID"}\}, \quad C_{temp} = 1.0$$
3. **Transient Bloom:** Exactly 1 bloom frame observed within an otherwise normal or turbid sequence (e.g., `[NORMAL, BLOOM, NORMAL]` or `[NORMAL, BLOOM]`).
   $$\text{State} = \texttt{"TRANSIENT_BLOOM"}, \quad C_{temp} = 0.35$$
   The visual state is marked $\texttt{"UNCERTAIN"}$, preventing premature emergency actuation.
4. **Ambiguous Sequence:** Conflicting or oscillating classifications (e.g., `[NORMAL, BLOOM, TURBID]`).
   $$\text{State} = \texttt{"AMBIGUOUS"}, \quad C_{temp} = 0.33$$
5. **Frame Age & Time Stamping:** If the time span across the buffer exceeds `max_frame_age_seconds = 30.0s`, temporal consistency is discounted by $0.80\times$ and logged in `reasons`.

---

## 5. Model Confidence Handling & Provenance Preservation

MobileNetV3-Small model parameters and weights are strictly frozen. The model outputs raw probabilities:
$$P(\text{NORMAL}), \quad P(\text{BLOOM}), \quad P(\text{TURBID})$$

### Evidence Weighting Contract
- **Raw Confidence:** $C_{raw} = \max_k P(k)$ (strictly preserved in `VisualEvidence.confidence`).
- **Effective Confidence:**
  $$C_{eff} = C_{raw} \times Q_{visual}$$
- **Evidence Strength:**
  $$W_{ev} = C_{eff} \times C_{temp}$$

If an image is degraded ($Q_{visual} < 0.40$), the visual state naturally transitions to $\texttt{"UNCERTAIN"}$ with a heavily discounted evidence strength ($W_{ev} < 0.20$), allowing downstream FusionEngine to rely on water chemistry sensors.

---

## 6. System Architecture & Integration Points

```
+---------------------+
|  Camera Frame       | -> ESP32-CAM / VirtualCameraDriver
+---------------------+
           |
           v
+---------------------+
| ImagePreprocessor   | -> Computes OpticalQualityResult (Laplacian, Exposure, Entropy)
|                     | -> Attaches Q_visual to PreprocessedImage.metadata
+---------------------+
           |
           v
+---------------------+
| AquaticBloomCVModel | -> MobileNetV3-Small PyTorch inference (frozen weights)
|                     | -> Emits raw CVPrediction + class_probabilities
+---------------------+
           |
           v
+---------------------+
| TemporalVisualBuffer| -> Sliding FIFO buffer (K=3), computes temporal consistency
+---------------------+
           |
           v
+---------------------+
| VisualDetector      | -> Calculates effective_confidence = raw_conf * Q_visual
|                     | -> Emits structured VisualEvidence
+---------------------+
           |
           v
+---------------------+
| FusionEngine / FSM  | -> Multi-modal belief combination (consumes Q_sensor & Q_visual)
+---------------------+
```

---

## 7. Verification Evidence & Quality Audits

The implementation has been thoroughly verified across multiple test regimes:

1. **Dedicated V5.2 Test Suite (`tests/test_v5_2_optical_intelligence.py`):**
   - 19 / 19 passed (100%).
   - Covers valid quality, blur detection, dark frames, overexposure, low information, corrupt payloads, mathematical bounds ($[0.0, 1.0]$), determinism, confidence preservation, effective confidence discounting, $K=3$ consistency, transient bloom discounting, ambiguous sequences, mixed quality, frame age limits, full provenance preservation, and V4/V5.1 backward compatibility.
2. **CV Subsystem Regression:**
   - 91 / 91 passed across all 9 CV test modules (`tests/test_v4_1_*.py` through `tests/test_v4_8_3_*.py`).
3. **V5.1 Sensor Quality Regression:**
   - 16 / 16 passed on `tests/test_v5_1_sensor_intelligence.py`.
4. **Complete Repository Regression:**
   - 349 passed, 3 skipped, 0 failed across all 352 test cases.
5. **Phase 9 End-to-End Audit (`run_phase9.py`):**
   - 244 / 244 passed, 3 skipped, all 21 release artifacts confirmed.

---

## 8. Change-Control & Frozen V3.8 Architecture Verification

In strict adherence to project architectural constraints:
- `src/iot/esp32_device.py`: **UNTOUCHED (0 diffs)**
- `src/iot/communication.py`: **UNTOUCHED (0 diffs)**
- `src/iot/scheduler.py`: **UNTOUCHED (0 diffs)**
- `src/iot/hal.py`: **UNTOUCHED (0 diffs)**
- `src/iot/actuators.py`: **UNTOUCHED (0 diffs)**

Verified via Git status check: `git status --short src/iot/esp32_device.py src/iot/communication.py src/iot/scheduler.py src/iot/hal.py src/iot/actuators.py` returned zero modifications.

---

## 9. Release Declaration

**V5.2 — Advanced Optical Quality & Multi-Frame Vision** is officially declared **COMPLETE, VERIFIED, AND RELEASE-READY**.
