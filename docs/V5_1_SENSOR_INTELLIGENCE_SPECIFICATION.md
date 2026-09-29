# VERSION 5.1 — ADVANCED SENSOR QUALITY & EDGE INTELLIGENCE SPECIFICATION

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Phase:** Version 5.1 Release Specification & Audit Report  
**Date:** 2026-08-26  
**Status:** 🟢 **V5.1 COMPLETE — VERIFIED — RELEASE READY**  

---

## 1. Executive Summary

Version 5.1 transitions the aquatic monitoring system from a simple binary threshold validator (`OK` / `FAULT`) to a **quantitative, multi-dimensional sensor intelligence and reliability estimation layer**.

Prior to V5.1, raw sensor readings were checked only for static physical bounds (e.g. pH in $[0.0, 14.0]$). Physically impossible phenomena—such as an instant jump from pH 7.1 to 9.8 in 10 seconds, rapid oscillating sensor jitter, or an alkaline pH spike with anoxic dissolved oxygen in clear water—were silently passed to downstream machine learning models.

V5.1 solves this through a dedicated, modular engine:
```text
Raw Sensor Reading
       ↓
Existing V4.8.6 Physical Bounds
       ↓
V5.1 Sensor Quality & Plausibility Engine
       ├── Rate-of-change analysis (|ΔX/Δt| ≤ MaxPhysicalRate)
       ├── Statistical deviation analysis (Median Absolute Deviation / Modified Z-Score)
       ├── Noise characterization (alternating sign flips & jitter variance)
       ├── Monotonic drift detection (uncoupled sensor drift)
       ├── Cross-sensor biological/chemical plausibility
       └── Freshness & stuck-value monitoring
       ↓
Sensor Quality Score Q_sensor ∈ [0.0, 1.0]
       ↓
Validated Sensor Evidence Contract
```

---

## 2. V5.1 Architectural Components & File Inventory

### 2.1 Files Added
- `src/iot/sensor_quality.py`: Modular sensor intelligence engine defining `SensorQualityComponent`, `SensorQualityResult`, and `SensorQualityEvaluator`.
- `config/sensor_quality_config.json`: Deterministic, configurable parameters for physical rate limits, MAD multipliers, noise thresholds, and weights.
- `tests/test_v5_1_sensor_intelligence.py`: Comprehensive 16-test unit and integration test suite.
- `docs/V5_1_SENSOR_INTELLIGENCE_SPECIFICATION.md`: This release specification document.

### 2.2 Files Modified
- `src/iot/edge_validation.py`: Added `validate_with_quality()` and `evaluate_quality()` while maintaining 100% backward-compatible signature for `validate()`.
- `src/iot/sensor_simulator.py`: Added 7 deterministic scenarios (`SUDDEN_SPIKE`, `NOISY_SENSOR`, `SENSOR_DRIFT`, `STUCK_SENSOR`, `MISSING_SENSOR`, `CROSS_SENSOR_INCONSISTENCY`, `LEGITIMATE_ENVIRONMENTAL_CHANGE`) and standardized freshwater normal baselines with micro-jitter.
- `src/backend/schemas.py`: Added `SensorQualityComponentSchema` and `SensorQualitySchema`, optionally extending `TelemetryPayloadSchema`.
- `src/iot/gateway.py`: Integrated `SensorQualityEvaluator` in `on_message_received` to assess incoming telemetry and pass quality metadata downstream.
- `src/fusion/decision_pipeline.py`: Added optional `sensor_quality` parameter to `run_pipeline()`.
- `src/fusion/fusion_engine.py`: Added optional `sensor_quality` parameter to `fuse()`, attaching it to `system_metadata` and the root decision dictionary.

### 2.3 Frozen V3.8 Architecture Protection
The five frozen runtime assets remain **100% untouched and unmodified**:
- `src/iot/esp32_device.py`: **0 lines changed (VERIFIED UNTOUCHED)**
- `src/iot/communication.py`: **0 lines changed (VERIFIED UNTOUCHED)**
- `src/iot/scheduler.py`: **0 lines changed (VERIFIED UNTOUCHED)**
- `src/iot/hal.py`: **0 lines changed (VERIFIED UNTOUCHED)**
- `src/iot/actuators.py`: **0 lines changed (VERIFIED UNTOUCHED)**

---

## 3. Mathematical Formulations & Quality Score $Q_{sensor}$

### 3.1 Rate-of-Change Analysis
For each sensor $s$, rate of change between observation $t_k$ and previous $t_{k-1}$ is evaluated:
$$r_s = \frac{|x_s(t_k) - x_s(t_{k-1})|}{\Delta t}$$
Where $\Delta t = \max(t_k - t_{k-1}, 0.1\text{ s})$.

- If $r_s > \text{MaxPhysicalRate}_s$: Severe penalty applied ($-0.55$), status set to `SUSPICIOUS` or `FAULT`.
- If $r_s > \text{WarningRate}_s$: Warning penalty applied ($-0.25$), status set to `DEGRADED`.

| Sensor | Warning Rate ($\text{units/s}$) | Max Physical Rate ($\text{units/s}$) |
| :--- | :--- | :--- |
| **pH** | $0.03\text{ pH/s}$ ($0.3$ in 10s) | $0.10\text{ pH/s}$ ($1.0$ in 10s) |
| **Temperature** | $0.10^\circ\text{C/s}$ ($1.0^\circ\text{C}$ in 10s) | $0.25^\circ\text{C/s}$ ($2.5^\circ\text{C}$ in 10s) |
| **Turbidity** | $2.5\text{ NTU/s}$ ($25$ in 10s) | $8.0\text{ NTU/s}$ ($80$ in 10s) |
| **Dissolved Oxygen** | $0.10\text{ mg/L/s}$ ($1.0$ in 10s) | $0.30\text{ mg/L/s}$ ($3.0$ in 10s) |
| **Salinity** | $0.20\text{ ppt/s}$ ($2.0$ in 10s) | $0.60\text{ ppt/s}$ ($6.0$ in 10s) |

### 3.2 Statistical Outlier Detection (Modified Z-Score via MAD)
Using a rolling window history ($N=10$) for each sensor channel:
$$\text{Median}_s = \text{median}(X_s)$$
$$\text{MAD}_s = \text{median}(|x_{s,i} - \text{Median}_s|)$$
$$\text{Modified } Z = \frac{0.6745 \cdot |x_s - \text{Median}_s|}{\max(\text{MAD}_s, 10^{-4})}$$

If $Z > 3.5$, the observation is flagged as an isolated statistical outlier (penalty $-0.35$).

### 3.3 Noise Characterization (High-Frequency Sign Flips)
Over the last 6 consecutive points, the number of derivative sign changes is counted:
$$\text{SignFlips} = \sum_{i=1}^{4} \mathbb{I}\left(\text{sgn}(\Delta x_i) \ne \text{sgn}(\Delta x_{i+1})\right)$$
If $\text{SignFlips} \ge 3$ AND $\text{std}(X_{last\_6}) > \text{NoiseThreshold}_s$, the sensor is flagged as `EXCESSIVE_NOISE` (penalty $-0.25$).

### 3.4 Monotonic Sensor Drift Detection
If the last 6 observations are strictly monotonic ($\Delta x_i \ge 0$ or $\Delta x_i \le 0$) and total drift $|x_k - x_{k-5}| > \text{DriftThreshold}_s$, the sensor is flagged as `MONOTONIC_DRIFT` (penalty $-0.20$).

### 3.5 Cross-Sensor Biological / Chemical Plausibility
1. **Photosynthetic Coupling:** High pH ($\ge 9.2$) caused by biological bloom must be accompanied by elevated DO ($\ge 6.0\text{ mg/L}$) and/or turbidity ($\ge 5\text{ NTU}$). If $\text{pH} \ge 9.2$ while $\text{DO} < 3.0\text{ mg/L}$ and $\text{Turbidity} < 3.0\text{ NTU}$, this is physically contradictory for a natural water body and indicates an isolated pH electrode failure (consistency penalty $-0.35$).
2. **Henry's Law Gas Solubility:** High water temperature ($> 35^\circ\text{C}$) has a reduced physical gas saturation ceiling. If $\text{Temp} > 35^\circ\text{C}$ and $\text{DO} > 18.0\text{ mg/L}$, flag thermal-gas solubility contradiction (consistency penalty $-0.25$).
3. **Freshwater Salinity Cap:** If a freshwater lake node reports marine ocean salinity ($> 25\text{ ppt}$), flag geographic context contradiction (consistency penalty $-0.20$).

### 3.6 Overall Quality Score $Q_{sensor}$ Calculation
$$Q_{sensor} = \left(\frac{\sum_{s} w_s \cdot q_s}{\sum_s w_s}\right) \times C_{cross} \times F_{fresh} \times D_{severe}$$

Where:
- Individual sensor score $q_s = \text{clamp}(1.0 - \sum \text{penalties}, 0.0, 1.0)$.
- Sensor weights: $w_{pH} = 0.25, w_{DO} = 0.25, w_{turb} = 0.20, w_{temp} = 0.15, w_{sal} = 0.15$.
- Cross-sensor consistency $C_{cross} \in [0.20, 1.0]$.
- Freshness factor $F_{fresh} \in [0.70, 1.0]$.
- Severe discount $D_{severe} = 0.70 + 0.30 \times \left(\frac{\min(q_s)}{0.60}\right)$ if $\min(q_s) < 0.60$, ensuring that severe failure of a critical channel proportionally discounts the overall trust in the telemetry.
- Hard cap: If all sensors are frozen ($N \ge 5$ identical readings), $Q_{sensor} \le 0.40$.

**Validation States:**
- $Q_{sensor} \ge 0.85$: `RELIABLE`
- $0.65 \le Q_{sensor} < 0.85$: `DEGRADED`
- $0.35 \le Q_{sensor} < 0.65$: `SUSPICIOUS`
- $Q_{sensor} < 0.35$: `FAULT`

---

## 4. Simulator Scenarios Specification

| Scenario Name | Physical Behavior Injected | Expected Quality Response |
| :--- | :--- | :--- |
| `NORMAL` | Stable baseline with natural micro-jitter | $Q_{sensor} \ge 0.85$, State `RELIABLE`, components `OK` |
| `SUDDEN_SPIKE` | Single-step jump in pH to 9.8 or temp $+12^\circ\text{C}$ | Rate-of-change violation, $Q_{sensor} < 0.85$ |
| `NOISY_SENSOR` | Alternating fluctuations exceeding noise floor | `is_noisy=True`, $Q_{sensor}$ degraded |
| `SENSOR_DRIFT` | Monotonic artificial drift on uncoupled channel | `is_drifting=True`, drift penalty |
| `STUCK_SENSOR` | Identical repeated float values for $N \ge 6$ cycles | `is_stuck=True`, State `FROZEN`, $Q_{sensor} \le 0.60$ |
| `MISSING_SENSOR` | Missing channel/None value | $q_s = 0.0$, State `FAULT`, $Q_{sensor}$ degraded |
| `CROSS_SENSOR_INCONSISTENCY` | pH 9.5 with anoxic DO (1.8 mg/L) in clear water | $C_{cross} < 1.0$, consistency warning emitted |
| `LEGITIMATE_ENVIRONMENTAL_CHANGE` | Coupled shift across temp, pH, DO, and turbidity | $Q_{sensor} \ge 0.70$, NO false isolated fault emitted |

---

## 5. Verification & Acceptance Results

### 5.1 Dedicated V5.1 Test Suite (`tests/test_v5_1_sensor_intelligence.py`)
```text
tests/test_v5_1_sensor_intelligence.py::test_normal_sensor_quality PASSED          [ 6%]
tests/test_v5_1_sensor_intelligence.py::test_rate_of_change_violation PASSED      [12%]
tests/test_v5_1_sensor_intelligence.py::test_pH_spike PASSED                      [18%]
tests/test_v5_1_sensor_intelligence.py::test_temperature_spike PASSED             [25%]
tests/test_v5_1_sensor_intelligence.py::test_turbidity_spike PASSED               [31%]
tests/test_v5_1_sensor_intelligence.py::test_noisy_sensor PASSED                  [37%]
tests/test_v5_1_sensor_intelligence.py::test_sensor_drift PASSED                  [43%]
tests/test_v5_1_sensor_intelligence.py::test_stuck_sensor PASSED                  [50%]
tests/test_v5_1_sensor_intelligence.py::test_missing_sensor PASSED                [56%]
tests/test_v5_1_sensor_intelligence.py::test_stale_sensor PASSED                  [62%]
tests/test_v5_1_sensor_intelligence.py::test_cross_sensor_inconsistency PASSED    [68%]
tests/test_v5_1_sensor_intelligence.py::test_legitimate_environmental_change PASSED[75%]
tests/test_v5_1_sensor_intelligence.py::test_quality_bounds PASSED                [81%]
tests/test_v5_1_sensor_intelligence.py::test_quality_determinism PASSED           [87%]
tests/test_v5_1_sensor_intelligence.py::test_quality_explanation PASSED           [93%]
tests/test_v5_1_sensor_intelligence.py::test_v4_backward_compatibility PASSED     [100%]

============================= 16 passed in 0.29s =============================
```

### 5.2 Full Repository Regression (`pytest`)
```text
================= 330 passed, 3 skipped, 1 warning in 23.77s ==================
```

### 5.3 Phase 9 End-to-End Release Freeze (`python run_phase9.py`)
```text
==============================================================
🎉 PHASE 9 SYSTEM AUDIT & RELEASE FREEZE COMPLETE! 🎉
Ran 244 tests in 17.137s -- OK (skipped=3)
==============================================================
```

### 5.4 Frozen Architecture Audit (`git status`)
```bash
git status --short src/iot/esp32_device.py src/iot/communication.py src/iot/scheduler.py src/iot/hal.py src/iot/actuators.py
# Output: (EMPTY - 0 modifications across all 5 frozen files)
```

---

## 6. Known Limitations & Transition to V5.2

1. **Optical Quality Independence:** V5.1 evaluates *sensor* telemetry only. Optical image quality assessment ($Q_{visual}$ via Laplacian blur and luminance histograms) belongs to Milestone **V5.2**.
2. **Temporal Window Depth:** V5.1 uses a short rolling window ($N=10$) for immediate sequential checks. Multi-cycle trend slope forecasting ($\frac{\Delta X}{\Delta t}$) and 5-tier threat progression (`WATCH`, `EARLY_WARNING`) belong to Milestone **V5.3**.
3. **Deterministic Memory Layer:** Secondary immune response memory cells for repeated non-self antigens belong to Milestone **V5.4**.

---

## 7. Official Release Declaration

All acceptance criteria, boundary invariants, and regression tests have passed.

🟢 **VERSION 5.1 — COMPLETE — VERIFIED — RELEASE READY**
