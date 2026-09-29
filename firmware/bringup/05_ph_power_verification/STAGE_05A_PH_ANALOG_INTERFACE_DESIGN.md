# Stage 05A: Safe pH Analog Output Interface Design

**Subsystem:** Analog pH Sensor Module (PH-4502C Signal Conditioning Board + Glass Probe)  
**Target MCU:** NodeMCU ESP-32S (38-pin Dev Module, ESP32-D0WD-V3)  
**Document Status:** Design & Safety Specification (Physical Connection Frozen)  
**Reference Stage:** Stage 05 Power Verification (Frozen) $\rightarrow$ Stage 05A Interface Design  

---

## 1. Hardware State & Operational Context

The current physical hardware state remains strictly preserved as verified in Stage 05:
- **pH Probe:** Connected to module BNC connector.
- **pH Module V+:** Connected to ESP32 `5V / VIN` pin (powered via USB rail).
- **pH Module G:** Connected to ESP32 `GND` (common system ground).
- **pH Module Po:** **DISCONNECTED** (Open-circuit / isolated).
- **pH Module To:** **DISCONNECTED** (Unused analog temperature output).
- **pH Module Do:** **DISCONNECTED** (Unused digital threshold output).
- **Secondary G:** **DISCONNECTED** (Redundant ground).
- **DS18B20 Probe:** Deferred on GPIO 33; untouched.
- **Production Firmware:** Untouched (`firmware/src/main.cpp` and `firmware/platformio.ini` preserved).
- **Measurement Tool Availability:** **NO digital multimeter (DMM) is available.** Therefore, passive hardware protection via a resistor divider is mandatory to guarantee ESP32 electrical safety before any wire connects to an MCU pin.

---

## 2. GPIO Pin Assignment & Conflict Audit

### 2.1 Selected Analog Pin: GPIO 32 (ADC1_CH4)
- **silicon Channel:** ADC1 Channel 4 (`ADC1_CH4`).
- **Physical Header:** Left Header, Pin 7 on NodeMCU ESP-32S.
- **Electrical Type:** Analog Input / Touch 9 / RTC GPIO 9.

### 2.2 Why ADC1 is Required (Wi-Fi Coexistence)
The ESP32 features two internal analog-to-digital converters:
- **ADC2** (GPIOs 0, 2, 4, 12, 13, 14, 15, 25, 26, 27): Internally arbitrated with the ESP32 Wi-Fi / Bluetooth baseband SAR controller. Whenever Wi-Fi is active, sampling ADC2 fails or causes fatal conflicts.
- **ADC1** (GPIOs 32, 33, 34, 35, 36, 39): Completely independent of the Wi-Fi subsystem.
Because the AquaSentinel-AI production architecture requires continuous telemetry over MQTT via Wi-Fi, the pH sensor **must** reside on **ADC1**.

### 2.3 Verification Against Project Documentation & Codebase
1. **`firmware/include/config/PinConfig.h`**:
   Line 8 explicitly sets:
   ```cpp
   int phPin = 32;
   ```
2. **`docs/V4_8_1_FINAL_PIN_MAPPING_PROPOSAL.md`**:
   Lines 47, 88, 144, 227 uniformly assign pH to `GPIO 32 (ADC1_CH4)` as the optimal analog sensor pin.
3. **`docs/PHYSICAL_WIRING_PLAN.md`**:
   Line 16 assigns `PH_PO` to `GPIO 32`.
4. **`docs/PHYSICAL_HARDWARE_BOM.md`**:
   Line 21 documents `GPIO 32 (ADC1)` for the pH Sensor Kit.

### 2.4 Conflict Verification with All Frozen Bring-Up Stages
| Hardware Stage | Component Tested | GPIO Used | Conflict with GPIO 32? |
| :--- | :--- | :--- | :--- |
| **Stage 01** | LEDs, Buzzer, Relay | GPIO 19, 21, 22, 23, 27 | **None** |
| **Stage 02** | Bring-up LEDs | GPIO 25, 26, 27 | **None** |
| **Stage 03** | Buzzer Verification | GPIO 14 | **None** |
| **Stage 04** | DS18B20 Temp Probe (Deferred)| GPIO 33 | **None** (GPIO 33 is untouched) |
| **Stage 05** | pH Module Power | V+ (VIN), G (GND) | **None** |

**Conclusion:** `GPIO 32` is completely free, unassigned in all active bring-up stages, perfectly matches `PinConfig.h`, and avoids all pin conflicts.

---

## 3. Resistor Inventory Audit

Per project documentation ([PHYSICAL_HARDWARE_BOM.md](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/PHYSICAL_HARDWARE_BOM.md) Item 33, [V4_8_5_PHYSICAL_HARDWARE_BASELINE_AUDIT.md](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/V4_8_5_PHYSICAL_HARDWARE_BASELINE_AUDIT.md) Item 7 & Line 191, and [V4_8_6_PRE_HARDWARE_INTEGRATION_GATE.md](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/V4_8_6_PRE_HARDWARE_INTEGRATION_GATE.md) Line 222), the confirmed available resistors in the Resistor Kit Box are:

- **220 Ω** (5mm LED current-limiting)
- **330 Ω** (Alternative LED current-limiting)
- **1 kΩ** (Buzzer NPN transistor base resistor)
- **4.7 kΩ** (DS18B20 OneWire bus pull-up)
- **10 kΩ** (Precision voltage dividers)
- **20 kΩ** (Precision voltage dividers)

No other resistor values exist or may be assumed.

---

## 4. Voltage Divider Topology & Electrical Sizing

### 4.1 Problem Definition & Overvoltage Hazard
- The pH signal conditioning board (PH-4502C) is powered from the **5.0V** rail.
- In alkaline environments or uncalibrated trimmer states, the high-impedance op-amp output stage ($P_o$) can output up to **4.10V DC** (and up to ~4.5V under operational extremes).
- The ESP32 ADC input pins are **not 5V tolerant** and have an absolute maximum rating of **3.30V DC** (silicon limit 3.6V).
- Because **no multimeter is available** to measure and confirm the trimmer voltage prior to connection, connecting $P_o$ directly to GPIO 32 presents an unacceptable risk of overvoltage damage to the ESP32 ADC1 module.

### 4.2 Circuit Schematic
Using the confirmed **10 kΩ** and **20 kΩ** resistors from the inventory:

```
                  +-----------------------------------+
                  | pH Sensor Board (PH-4502C)        |
                  |                                   |
                  |  [ Po ] Analog Output             |
                  +----+------------------------------+
                       |
                       |  (V_in: 0.0V to 4.10V DC)
                       ▼
                 [ Upper Resistor R1 = 10 kΩ ]
                       │
                       ├──────────────────────────────► To ESP32 GPIO 32 (ADC1_CH4)
                       │                                (V_ADC: 0.0V to 2.73V DC)
                 [ Lower Resistor R2 = 20 kΩ ]
                       │
                       ▼
                  ESP32 Common GND Rail (0V)
```

### 4.3 Mathematical Derivation & Safety Limits

1. **Voltage Division Ratio ($K$):**
   $$K = \frac{R_2}{R_1 + R_2} = \frac{20\text{ k}\Omega}{10\text{ k}\Omega + 20\text{ k}\Omega} = \frac{20}{30} = \frac{2}{3} \approx 0.6667$$

2. **Calculated Maximum ADC Voltage ($V_{ADC\_max}$):**
   At documented maximum op-amp output ($P_{o\_max} = 4.10\text{ V DC}$):
   $$V_{ADC\_max} = V_{in\_max} \times K = 4.10\text{ V} \times \frac{2}{3} = \mathbf{2.733\text{ V DC}}$$

3. **Overvoltage Safety Margin:**
   $$\Delta V_{margin} = V_{ESP32\_max} - V_{ADC\_max} = 3.30\text{ V} - 2.733\text{ V} = \mathbf{+0.567\text{ V DC}}$$
   This provides a **17.2% safety headroom** below the 3.3V ceiling.

4. **Extreme Fault Condition Assessment (Op-Amp Rail Saturation at 5.0V):**
   Even if the op-amp saturates directly against the 5.0V power rail ($P_o = 5.00\text{ V DC}$):
   $$V_{ADC\_fault} = 5.00\text{ V} \times \frac{2}{3} = \mathbf{3.333\text{ V DC}}$$
   This stays comfortably within the ESP32 absolute maximum rating ($V_{abs\_max} = 3.60\text{ V}$), preventing silicon destruction under catastrophic fault conditions.

5. **Thevenin Source Impedance ($R_{th}$):**
   $$R_{th} = R_1 \parallel R_2 = \frac{10\text{ k}\Omega \times 20\text{ k}\Omega}{10\text{ k}\Omega + 20\text{ k}\Omega} = \mathbf{6.67\text{ k}\Omega}$$
   Espressif specifies a recommended source impedance of $< 10\text{ k}\Omega$ for the internal SAR ADC sampling capacitor. Since $6.67\text{ k}\Omega < 10\text{ k}\Omega$, no buffer amplifier or impedance-matching capacitor is strictly required for dc sampling.

6. **Current Loading on Op-Amp ($I_{divider}$):**
   $$I_{divider} = \frac{4.10\text{ V}}{10\text{ k}\Omega + 20\text{ k}\Omega} = \frac{4.10\text{ V}}{30\text{ k}\Omega} \approx 0.137\text{ mA} = 137\text{ }\mu\text{A}$$
   The PH-4502C op-amp output stage can source several milliamperes; a $137\text{ }\mu\text{A}$ load causes virtually zero signal loading or thermal drift.

---

## 5. Summary Specification for Physical Connection

When physical connection is authorized in the subsequent stage, the wiring shall strictly follow:

| Node | Physical Component / Pin | Notes |
| :--- | :--- | :--- |
| **Input Source** | pH Module `Po` Pin | Open circuit until wired |
| **Upper Resistor ($R_1$)** | **10 kΩ** Metal Film Resistor | Connected between `Po` and breadboard junction row |
| **Junction Row** | Breadboard Tie-Point | Connects $R_1$, $R_2$, and jumper wire to ESP32 |
| **ADC Interface Line** | Breadboard Junction $\rightarrow$ **ESP32 GPIO 32** | ADC1_CH4 Analog Input |
| **Lower Resistor ($R_2$)** | **20 kΩ** Metal Film Resistor | Connected between breadboard junction row and Common GND |
| **Ground Reference** | ESP32 GND Rail | Common ground with pH module `G` pin |

---

## 6. Safety Enforcements & Boundaries

- [x] **No physical connection:** `Po` remains disconnected.
- [x] **No firmware changes:** Production firmware files are untouched.
- [x] **No calibration:** No pH calibration or conversion equation has been applied.
- [x] **No operational claims:** The pH sensor is **NOT** claimed to be operational or verified.
- [x] **Execution stopped:** Awaiting explicit authorization before physical wiring.
