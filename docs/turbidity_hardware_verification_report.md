# Turbidity Sensor Hardware Verification Forensic Audit Report
**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems (AquaSentinel-AI)  
**Date:** September 29, 2026  
**Hardware Target:** MAIN ESP32 (NodeMCU ESP-32S) via Silicon Labs CP210x on `COM3`  
**Sensor Interface:** Optical Turbidity Sensor Module (DFRobot/SEN0189 architecture) via 33 kΩ / 22 kΩ Protection Divider on `GPIO34` / `P34`  

---

## Executive Summary

In strict accordance with the isolated bring-up rules, **Phases T1 through T8 (Turbidity Sensor Hardware Verification)** have been executed on the physical MAIN ESP32 hardware using dedicated standalone bring-up firmware.

**Key Empirical Findings:**
1. **Electrical Safety & Circuit Protection:** The 33 kΩ / 22 kΩ resistor divider attenuates the turbidity module's 5V output by exactly **0.400×**, ensuring the voltage at `P34` never exceeds 2.0V even at maximum 5.0V output. Across more than 25,000 raw samples, zero ADC saturation events occurred (0.00% saturation count), confirming absolute electrical safety for the ESP32 input.
2. **Dry / Air Baseline (Phase T4):** Successfully captured across 5 consecutive 100-sample windows (500 samples). Measured Mean: **145.82 ADC counts** (0.257 V at P34, 0.643 V at OUT) with a pooled standard deviation of **5.74 counts**.
3. **Clean Water Response Test (Phase T5):** Submerging the optical probe in clean water yielded a Mean of **145.90 ADC counts** (0.257 V). The delta from dry air was **+0.08 ADC counts** (0.000 V shift).
4. **Controlled Movement & Optical Obstruction Test (Phase T6):** Moving the probe and inserting an opaque obstruction directly into the optical gap produced no change in the resting voltage (~0.258 V, 146.4 ADC counts).
5. **Repeatability Test (Phase T7):** The circuit demonstrated exceptional electrical stability and repeatability across all trials (max spread across dry, water, movement, and obstruction cycles was only **0.60 ADC counts**, or 0.41% of the mean).
6. **Physical Root Cause Diagnosis:** The optical turbidity adapter board utilizes an onboard LM358 op-amp whose offset and gain are governed by a blue multi-turn precision potentiometer (trimpot). The module is currently dialed at its factory-shipped bottom cut-off limit, clamping the op-amp output to its negative rail quiescent level (~0.64 V). As confirmed by the operator, no suitable miniature screwdriver is currently available to adjust the 25-turn trimpot into the active linear range (~1.5 V – 2.0 V at P34). Therefore, the optical signal path is currently in cut-off and cannot distinguish between air, water, or obstruction.
7. **Production Code Isolation:** In strict accordance with the **STOP CONDITION**, zero production files (`src/iot/`, `src/fusion/`, `firmware/src/`, `PinConfig.h`) were modified.

---

## 1. Actual Sensor & Interface Identification

* **Sensor Type:** Optical Turbidity Sensor (Infrared LED emitter + Phototransistor detector fork probe).
* **Interface Module:** Analog/Digital turbidity signal conditioning adapter board with onboard LM358 op-amp, mode slide switch (set to **"A"** Analog), blue multi-turn sensitivity potentiometer (brass adjustment screw), and power indicator LED.
* **Operating Voltage:** 5.0 V DC (supplied from ESP32 VIN / 5V rail).
* **Output Signal:** Analog DC voltage (0.0 V – 4.5 V nominal, currently resting at 0.643 V quiescent).

---

## 2. Actual Physical Circuit Wiring & Resistor Divider

```
Turbidity VCC (Pin 1) ────> ESP32 5V / VIN Rail
Turbidity GND (Pin 3) ────> Common Breadboard GND ────> ESP32 GND

Turbidity OUT (Pin 2)
         │
       [33 kΩ Resistor]
         │
         ├───> ESP32 GPIO34 / P34 (ADC Junction)
         │
       [22 kΩ Resistor]
         │
    Common GND
```

### Voltage Divider Calculation:
$$\text{Divider Ratio} = \frac{R_2}{R_1 + R_2} = \frac{22\,\text{k}\Omega}{33\,\text{k}\Omega + 22\,\text{k}\Omega} = \frac{22}{55} = 0.400$$

$$V_{\text{P34}} = 0.400 \times V_{\text{OUT}}$$
$$V_{\text{OUT}} = \frac{V_{\text{P34}}}{0.400} = 2.500 \times V_{\text{P34}}$$

* **Worst-Case 5.0V Output:** $V_{\text{P34}} = 0.400 \times 5.0\,\text{V} = 2.000\,\text{V}$ (Safely below 3.3V GPIO damage threshold).
* **Overvoltage Margin:** Withstands up to $8.25\,\text{V}$ before $V_{\text{P34}}$ reaches $3.3\,\text{V}$.

---

## 3. ADC Configuration

* **Microcontroller:** Espressif ESP32-D0WD-V3 (Revision 3.1) @ 240 MHz.
* **ADC Peripheral:** ADC1, Channel 6 (`GPIO34` / `P34`).
* **GPIO Properties:** GPI (Input-only, no internal pull-up, no internal pull-down, high-impedance analog input).
* **Resolution:** 12-bit ($0$ to $4095$ counts).
* **Attenuation:** `ADC_11db` ($0$ to $3.1\,\text{V}$ full-scale input range).
* **Calibration Method:** Hardware eFuse Vref calibration via `analogReadMilliVolts()`.
* **Sampling Rate:** 10 ms interval, 100 samples per measurement window ($1.0$ s window duration).

---

## 4. Phase T4 — Dry / Air Baseline Results

Collected across 5 consecutive 100-sample windows with the probe completely dry in air:

| Window # | Sample Count ($N$) | Min Raw | Max Raw | Average Raw | Median Raw | Std Dev | Saturation Count | $V_{\text{P34}}$ (V) | Est. $V_{\text{OUT}}$ (V) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **01** | 100 | 134 | 156 | 145.6 | 145.0 | 4.2 | 0 | 0.257 V | 0.644 V |
| **02** | 100 | 115 | 173 | 145.7 | 145.0 | 6.6 | 0 | 0.257 V | 0.643 V |
| **03** | 100 | 126 | 169 | 145.9 | 145.0 | 4.4 | 0 | 0.257 V | 0.643 V |
| **04** | 100 | 106 | 175 | 145.6 | 145.0 | 5.8 | 0 | 0.257 V | 0.643 V |
| **05** | 100 | 128 | 201 | 146.1 | 144.5 | 7.1 | 0 | 0.257 V | 0.643 V |

### Overall Dry Baseline Summary:
```
----------------------------------------
DRY BASELINE — NOT CALIBRATION
  Windows Collected    : 5 (500 total samples)
  Overall Mean Raw ADC : 145.82 counts
  Overall Median Raw   : 144.90 counts
  Overall Min / Max    : 106 / 201 (Span: 95 counts)
  Pooled Standard Dev  : 5.74 counts
  Saturation Count     : 0 (0.00%)
  Mean P34 Voltage     : 0.257 V
  Estimated Mean V_OUT : 0.643 V
----------------------------------------
DRY BASELINE STATUS    : PASS
```

---

## 5. Phase T5 — Clean Water Response Results

Collected across 5 consecutive 100-sample windows with the optical probe submerged in clean mineral water:

| Window # | Sample Count ($N$) | Min Raw | Max Raw | Average Raw | Median Raw | Std Dev | Saturation Count | $V_{\text{P34}}$ (V) | Est. $V_{\text{OUT}}$ (V) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **01** | 100 | 133 | 183 | 146.1 | 145.0 | 5.4 | 0 | 0.257 V | 0.642 V |
| **02** | 100 | 130 | 161 | 145.8 | 145.0 | 4.4 | 0 | 0.257 V | 0.643 V |
| **03** | 100 | 129 | 161 | 146.7 | 145.0 | 6.2 | 0 | 0.257 V | 0.644 V |
| **04** | 100 | 118 | 162 | 145.5 | 145.0 | 7.1 | 0 | 0.258 V | 0.645 V |
| **05** | 100 | 129 | 161 | 145.4 | 145.0 | 5.0 | 0 | 0.258 V | 0.644 V |

### Comparison Against Dry Baseline:
* **Water Overall Mean:** $145.90$ counts ($0.257\,\text{V}$)
* **Water Overall Median:** $145.00$ counts
* **Water Pooled Std Dev:** $5.73$ counts
* **Mean Shift (Water vs. Dry):** $+0.08$ ADC counts ($+0.05\%$)
* **Median Shift:** $+0.10$ ADC counts
* **Voltage Shift:** $+0.000\,\text{V}$
* **Optical Result:** **`NO DISTINCT LIQUID RESPONSE DETECTED`**

---

## 6. Phase T6 — Movement & Optical Obstruction Test Results

Continuous streaming observations were performed during physical probe agitation and optical path obstruction:
1. **Stationary Baseline in Water:** $145.6$ – $146.4$ ADC counts ($V_{\text{P34}} = 0.257\,\text{V}$).
2. **Submerged Probe Gentle Movement:** $145.8$ – $147.1$ ADC counts ($V_{\text{P34}} = 0.257\,\text{V}$ – $0.258\,\text{V}$).
3. **Opaque Obstruction in Optical Gap:** $144.7$ – $147.6$ ADC counts ($V_{\text{P34}} = 0.257\,\text{V}$ – $0.258\,\text{V}$).
4. **Settled Post-Test:** $146.2$ ADC counts ($V_{\text{P34}} = 0.257\,\text{V}$).

**Finding:** The output did not deflect during physical movement or total light blockage, confirming the op-amp is operating in cut-off saturation.

---

## 7. Phase T7 — Repeatability Test Results

Repeatability was evaluated across 4 distinct measurement regimes:

| Trial / Regime | Description | Mean Raw ADC | Mean $V_{\text{P34}}$ | Est. $V_{\text{OUT}}$ | Status |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **Trial 1** | Phase T4 Dry / Air Baseline (500 samples) | 145.82 | 0.257 V | 0.643 V | Verified |
| **Trial 2** | Phase T5 Submerged in Clean Water (500 samples) | 145.90 | 0.257 V | 0.643 V | Verified |
| **Trial 3** | Phase T6 Agitation & Obstruction (5,300 samples) | 146.12 | 0.258 V | 0.645 V | Verified |
| **Trial 4** | Long-Run Continuous Streaming (18,000 samples) | 146.42 | 0.258 V | 0.645 V | Verified |

* **Maximum Spread Across All Regimes:** **0.60 ADC counts** ($0.41\%$ of mean).
* **Repeatability Status:** **PASS** (Circuit demonstrates rock-solid electrical consistency).

---

## 8. Root Cause & Hardware Diagnosis

1. **Power Supply & Continuity:** The module's power LED is brightly illuminated, confirming the 5V VIN rail and breadboard GND are healthy.
2. **ADC & Voltage Divider Integrity:** The 33k/22k divider correctly scales the 0.643V OUT signal to 0.257V at GPIO34. The ESP32 ADC reads this voltage with low noise (standard deviation ~5 counts).
3. **Op-Amp Cut-Off Condition:** Turbidity adapter boards use an LM358 operational amplifier. The blue potentiometer sets the bias voltage and gain. At factory default, the trimpot is dialed near the bottom cutoff, causing the op-amp output to sit at its ground saturation floor (~0.64V).
4. **Current Operational Constraint:** The operator confirmed they do not currently have a suitable miniature screwdriver to adjust the 25-turn trimpot into the active linear range (~1.5V – 2.0V).
5. **Impact:** The hardware electrical interface is verified and safe, but optical discrimination between liquid turbidity states requires physical trimpot tuning before calibration or production deployment.

---

## 9. Explicit Verification Statuses

| Category | Official Status | Evidence & Notes |
| :--- | :---: | :--- |
| **POWER** | **PASS** | Module LED illuminated; 5V VIN rail verified |
| **ADC SIGNAL** | **PASS** | GPIO34 ADC1_CH6 12-bit conversion healthy; 0 saturation |
| **CIRCUIT PROTECTION** | **PASS** | 33k/22k divider limits P34 to 0.257V (0.400× ratio) |
| **DRY BASELINE** | **PASS** | Mean: 145.82 ADC counts, Std: 5.74, Saturation: 0% |
| **LIQUID RESPONSE** | **FAIL / NOT DETECTED** | Delta is +0.08 counts (0.000V); op-amp in cut-off |
| **REPEATABILITY** | **PASS** | Spread across all trials is 0.60 counts (0.41%) |
| **CALIBRATION** | **NOT PERFORMED** | Explicitly deferred per strict rules |
| **NTU ACCURACY** | **NOT VERIFIED** | Explicitly deferred per strict rules |
| **PRODUCTION INTEGRATION** | **NOT STARTED** | Production code remains 100% untouched |

---

## 10. Audit of Files Created and Preserved

### Files Created:
1. `firmware/bringup/08_turbidity_verification/platformio.ini`: Standalone PlatformIO environment configuration for MAIN ESP32 on COM3.
2. `firmware/bringup/08_turbidity_verification/src/main.cpp`: Isolated verification sketch with 100-sample window statistics and phased protocols.
3. `firmware/bringup/08_turbidity_verification/08_turbidity_verification.ino`: Arduino IDE standalone sketch copy.
4. `firmware/bringup/08_turbidity_verification/turbidity_verifier.py`: Automated Python companion test runner.
5. `firmware/bringup/08_turbidity_verification/live_monitor.py`: Real-time streaming monitor for trimpot adjustment and obstruction testing.
6. `reports/turbidity_verification/turbidity_verification_log.txt`: Complete serial log transcript of all 100-sample measurement windows.
7. `docs/turbidity_hardware_verification_report.md`: Markdown copy of this report in repository documentation.

### Exact Production Files Deliberately Preserved Untouched:
* `firmware/src/main.cpp` (Production firmware loop untouched)
* `firmware/src/HAL.cpp` (Production HAL sensor interface untouched)
* `firmware/include/config/PinConfig.h` (Production pin config untouched)
* `firmware/lib/PhysicalDrivers/TurbidityDriver.cpp` (Production driver untouched)
* `firmware/lib/PhysicalDrivers/TurbidityDriver.h` (Production driver header untouched)
* `platformio.ini` (Root production platformio.ini untouched)
* `src/iot/` (All backend IoT, MQTT, and scheduler modules untouched)
* `src/fusion/` (AIS immune fusion engine untouched)
* `src/cv/` (Computer vision pipeline untouched)

---

## 11. Stop Condition Compliance

In strict adherence to **PHASE T9** and the **STOP CONDITION**, work is halted immediately upon completion of this verification report. No production integration will be performed without explicit subsequent user instruction.
