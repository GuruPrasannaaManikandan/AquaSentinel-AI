# VERSION 4.8.5 — COMPONENT-LEVEL ELECTRICAL SPECIFICATION VERIFICATION

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Milestone:** V4.8.5 Component-Level Electrical Specification Audit  
**Document Date:** August 18, 2026  
**Target Hardware:** Confirmed 16-Item Physical Kit  
**Status:** Component Electrical Audit Complete / Hardware Wiring Pending  

---

> [!IMPORTANT]
> **STRICT COMPONENT INVENTORY CONSTRAINTS**  
> 1. **Transistor Status**: No 2N2222 transistor is currently in our confirmed inventory. If a module requires an active transistor driver, it is explicitly classified as **`ADDITIONAL COMPONENT REQUIRED FOR SAFE PHYSICAL IMPLEMENTATION`**.  
> 2. **Pump Status**: No physical pump or motor is in our inventory. The 5V 1-channel relay module is classified as **`RELAY PRESENT / LOAD ABSENT`**. NO 12V motor circuits or flyback diodes are claimed.  
> 3. **Hardware Boundary**: NO physical wiring, soldering, or board powering has occurred yet.

---

## 1. Task 1 — Component-Level Electrical Verification Matrix

| Component Name | Power Supply (VCC) | Signal Voltage Range | Max Output Voltage | Operating Current | Interface Type | Safe Direct ESP32 Connect? | Required Protection / Conditioning | Inventory Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Liquid pH Module (PH-4502C / SEN0161)** | 5.0V DC | 0.0V - 4.1V (Raw Op-Amp) | 4.1V (Alkaline extreme) | 10 - 20 mA | Analog Voltage | 🟠 **REQUIRES DIVIDER OR CALIBRATION** | Voltage Divider (10k/20k) or Potentiometer Offset | 🟢 **PHYSICALLY PRESENT** |
| **2. Optical Turbidity Module (TS-300B / DFRobot)** | 5.0V DC | 0.0V - 4.5V (Clear Water) | 4.5V DC | 30 - 40 mA | Analog Voltage | 🔴 **UNSAFE WITHOUT DIVIDER** | Precision Voltage Divider (10k/20k to 3.0V max) | 🟢 **PHYSICALLY PRESENT** |
| **3. DS18B20 Temp Probe** | 3.3V DC | 3.3V Logic | 3.3V DC | 1.0 - 1.5 mA | OneWire Digital | 🟢 **SAFE DIRECT CONNECT** | 4.7 kΩ Pull-up Resistor to 3.3V | 🟢 **PHYSICALLY PRESENT** |
| **4. 5V Audio Buzzer Module** | 5.0V DC / 3.3V Trigger | 3.3V Logic Trigger | N/A | 20 - 40 mA | Digital High-Active | 🟠 **MODULE SPEC DEPENDENT** | Transistor Driver if raw coil ($>12\text{mA}$) | 🟢 **PHYSICALLY PRESENT** |
| **5. 5V 1-Channel Relay Module** | 5.0V DC (Coil) | 3.3V Optocoupler IN | N/A | 50 - 70 mA (Coil) | Optocoupled Digital | 🟢 **SAFE DIRECT CONTROL (IN)**| NO LOAD CONNECTED (`LOAD ABSENT`) | 🟢 **PHYSICALLY PRESENT** |
| **6. ESP32-WROOM 38-Pin Dev Board** | 5.0V USB / 3.3V LDO | 3.3V Logic (Max 3.6V) | 3.3V DC | 80 - 240 mA | Dual-Core MCU | N/A (Main Controller) | 3.3V MAX ADC Input Limit (No 5V Input!) | 🟢 **PHYSICALLY PRESENT** |
| **7. AI-Thinker ESP32-CAM Board** | 5.0V USB / 5V Rail | 3.3V Logic | N/A | 120 - 310 mA | Optical Capture | N/A (Independent Node) | Dedicated 5V Supply (Peak 310 mA) | 🟢 **PHYSICALLY PRESENT** |

---

## 2. Task 2 — pH Sensor Safety Analysis

- **Module Supply Voltage**: 5.0V DC.
- **Amplifier Signal Output (`Po`)**: High-impedance op-amp stage. Depending on module gain calibration, raw output ranges from **0.0V (extreme acid) to ~4.1V (extreme base)**.
- **Safety Assessment**:
  > [!WARNING]
  > Because the pH module is powered by 5.0V, an uncalibrated or out-of-range pH probe signal can output up to **4.1V DC**, exceeding the safe **3.3V limit of ESP32 GPIO 32 (ADC1_CH4)**.
- **Safety Resolution**:
  - Option A: Insert a **10 kΩ / 20 kΩ resistor divider** between pH `Po` output and ESP32 GPIO 32, scaling maximum 4.1V down to **2.73V DC**.
  - Option B: Adjust the pH module's onboard potentiometer (`Trimmer R1`) to shift the zero-point voltage ($V_{pH7}$) down to **1.5V DC**, capping maximum voltage at **3.0V DC**.
- **Verification Status**: 🟠 **PHYSICAL SPECIFICATION REQUIRES VERIFICATION ON BENCH**.

---

## 3. Task 3 — Turbidity Sensor Safety & Resistor Divider Calculation

- **Module Supply Voltage**: 5.0V DC.
- **Analog Output Range (`AO`)**: 0.0V (high turbidity) to **4.5V DC** (clean water).
- **ESP32 ADC Compatibility**: 4.5V output **exceeds the 3.3V maximum ADC threshold** of ESP32 **GPIO 33 (ADC1_CH5)**.
- **Voltage Divider Design**:
  Using resistors from the confirmed Resistor Kit Box (Item #7):
  - $R_1 = 10\text{ k}\Omega$ (Series resistor from Turbidity `AO` to GPIO 33)
  - $R_2 = 20\text{ k}\Omega$ (Pull-down resistor from GPIO 33 to GND)
- **Mathematical Formula & Output Calculation**:
  $$V_{out} = V_{in} \times \frac{R_2}{R_1 + R_2}$$
  $$V_{out\_max} = 4.5\text{ V} \times \frac{20\text{ k}\Omega}{10\text{ k}\Omega + 20\text{ k}\Omega} = 4.5\text{ V} \times \frac{2}{3} = 3.0\text{ V DC}$$
- **Safety Verification**:
  $$3.0\text{ V DC} \le 3.3\text{ V DC (Maximum ESP32 ADC Input)}$$
- **Verification Status**: 🟢 **VERIFIED FROM COMPONENT/SOFTWARE EVIDENCE**.

---

## 4. Task 4 — DS18B20 Temperature Probe Safety Analysis

- **VCC Pin**: 3.3V DC (Red wire connected to ESP32 3.3V Rail).
- **GND Pin**: Ground (Black wire connected to Common Ground Rail).
- **DATA Pin**: OneWire digital line (Yellow wire connected to **GPIO 18**).
- **Pull-Up Resistor Check**: Requires a **4.7 kΩ pull-up resistor** between `DATA` (GPIO 18) and `3.3V`.
- **Inventory Check**: Provided by the confirmed **Resistor Kit Box (Item #7)**.
- **Verification Status**: 🟢 **VERIFIED FROM COMPONENT/SOFTWARE EVIDENCE**.

---

## 5. Task 5 — 5V Audio Alarm Buzzer Drive Analysis

- **Confirmed Inventory Hardware**: 5V Piezo Audio Buzzer Module (Item #12).
- **Current Requirement**: Active piezo buzzers draw $20\text{ mA} - 40\text{ mA}$ at 5V.
- **ESP32 Direct Drive Assessment**:
  > [!CAUTION]
  > ESP32 GPIO pins have a absolute maximum current rating of **12 mA**. Connecting a raw buzzer coil directly to GPIO 23 will overload the pin and cause brownout crashes or silicon degradation.
- **Inventory Check**: No 2N2222 transistor is currently in our confirmed inventory.
- **Resolution Categories**:
  - **If owned module is an Active 3.3V/5V Trigger Module** (incorporates onboard S8050 transistor / driver circuit): GPIO 23 directly drives the low-current logic trigger pin ($<2\text{ mA}$). 🔵 **SAFE DESIGN DECISION**.
  - **If owned module is a Raw Passive/Active Piezo Coil**: 
    - **Classification**: 🟡 **ADDITIONAL COMPONENT REQUIRED FOR SAFE PHYSICAL IMPLEMENTATION (NPN Transistor / MOSFET Driver)**.
- **Verification Status**: 🟠 **PHYSICAL SPECIFICATION REQUIRES VERIFICATION ON BENCH**.

---

## 6. Task 6 — 5V 1-Channel Relay Module Interface Analysis

- **Confirmed Inventory Hardware**: 5V 1-Channel Optocoupled Relay Module (Item #16).
- **Module Terminals**:
  - `VCC`: Connected to 5.0V DC Power Rail (powers 5V relay coil, ~50mA).
  - `GND`: Connected to Common Ground Rail.
  - `IN`: Connected to **GPIO 27** (3.3V Logic output).
- **Optocoupler 3.3V Logic Compatibility**: The module utilizes an **EL817 optocoupler** input. The optocoupler LED turns ON when GPIO 27 sinks/sources ~2-3 mA, which is **100% 3.3V logic compatible**.
- **Contact Terminal Status (`COM`, `NO`, `NC`)**:
  > [!IMPORTANT]
  > **LOAD ABSENT STATUS**  
  > NO high-voltage AC or motor loads are connected to the relay contacts. The relay operates safely as a 5V dry-contact logic indicator for software decision testing.
- **Verification Status**: 🔵 **SAFE DESIGN DECISION**.

---

## 7. Task 7 — Power Architecture (Actual Owned Hardware Only)

```
                            USB Type-C 5V DC Power Input (Data Cable)
                                                │
                                                ▼
                                   ESP32-WROOM-32 Dev Module
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 │                                                             │
                 ▼                                                             ▼
         5.0V Main Power Rail                                           3.3V LDO Output Rail
                 │                                                             │
   ┌─────────────┼─────────────┬─────────────┐                   ┌─────────────┼─────────────┐
   ▼             ▼             ▼             ▼                   ▼             ▼             ▼
  pH Board   Turbidity Board Relay Coil  Buzzer (+5V)       DS18B20 (3.3V) Status LEDs  ESP32 Logic
 (5V VCC)     (5V VCC)       (5V VCC)   (Trigger/VCC)       (via 4.7kΩ)    (via 220Ω)   (Core MCU)
```

### System Current Consumption Budget (No Pump)

| Subsystem Component | Supply Rail | Operating Voltage | Peak Current Draw | Power Source |
| :--- | :--- | :--- | :--- | :--- |
| **ESP32-WROOM-32 MCU** | 3.3V Rail (via LDO) | 3.3V DC | 240 mA | USB Type-C Input |
| **DS18B20 Temp Sensor**| 3.3V Rail | 3.3V DC | 1.5 mA | ESP32 3.3V Pin |
| **pH Amplifier Module** | 5.0V Power Rail | 5.0V DC | 20 mA | USB 5V Power Rail |
| **Turbidity Sensor Board**| 5.0V Power Rail | 5.0V DC | 40 mA | USB 5V Power Rail |
| **Status LEDs (x3)** | 3.3V Rail | 3.3V DC | 18 mA | ESP32 GPIOs (220 Ω) |
| **5V Piezo Buzzer** | 5.0V Rail / Trigger | 5.0V DC | 40 mA | USB 5V Power Rail |
| **5V Relay Module Coil**| 5.0V Power Rail | 5.0V DC | 70 mA | USB 5V Power Rail |
| **TOTAL MAIN SYSTEM** | **5.0V USB Input** | **5.0V DC** | **429.5 mA Peak** | **100% Powered by Standard 5V 1A USB** |

---

## 8. Task 8 — Master Safe Wiring Specification Table

| Component Name | Power VCC | Ground GND | Signal Pin | ESP32 GPIO | Additional Hardware Component | Electrical Safety Requirement | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DS18B20 Temp Probe** | 3.3V Pin | Common GND | `DQ_DATA` | **GPIO 18** | 4.7 kΩ Resistor (Resistor Box) | Pull-up to 3.3V rail | 🟢 **VERIFIED** |
| **pH Probe Module** | 5.0V Rail | Common GND | `PH_PO` | **GPIO 32 (ADC1)**| Optional 10k/20k Divider | Max 3.0V ADC input | 🟠 **REQUIRES BENCH CHECK** |
| **Turbidity Sensor** | 5.0V Rail | Common GND | `TURB_AO` | **GPIO 33 (ADC1)**| 10k Ω + 20k Ω Resistors (Resistor Box)| $V_{out\_max} = 3.0\text{V}$ | 🟢 **VERIFIED** |
| **Green Status LED** | 3.3V Rail | Common GND | `LED_GREEN` | **GPIO 19** | 220 Ω Resistor (Resistor Box) | Current limit ~6 mA | 🟢 **VERIFIED** |
| **Yellow Warning LED** | 3.3V Rail | Common GND | `LED_YELLOW`| **GPIO 21** | 220 Ω Resistor (Resistor Box) | Current limit ~6 mA | 🟢 **VERIFIED** |
| **Red Critical LED** | 3.3V Rail | Common GND | `LED_RED` | **GPIO 22** | 220 Ω Resistor (Resistor Box) | Current limit ~6 mA | 🟢 **VERIFIED** |
| **5V Piezo Buzzer** | 5.0V Rail | Common GND | `BUZZER` | **GPIO 23** | Transistor Driver if raw coil | Max 12 mA pin draw | 🟠 **REQUIRES BENCH CHECK** |
| **5V Relay Module** | 5.0V Rail | Common GND | `RELAY_IN1`| **GPIO 27** | None (`LOAD ABSENT`) | 3.3V optocoupler input | 🔵 **SAFE DESIGN DECISION** |
| **ESP32-CAM Board** | 5.0V Input | Common GND | Wi-Fi / MQTT | Independent | Dedicated USB Cable | Separate 5V Supply | 🔵 **SAFE DESIGN DECISION** |

---

## 9. Task 9 — Final Categorized Status Overview

1. 🟢 **VERIFIED FROM COMPONENT/SOFTWARE EVIDENCE**:
   - DS18B20 4.7 kΩ pull-up on GPIO 18 (Resistor Kit Box).
   - Turbidity sensor 10k/20k voltage divider scaling 4.5V to 3.0V max for ESP32 ADC1 safety.
   - Status LEDs current limiting via 220 Ω resistors on GPIO 19, 21, 22.
   - Software interface stability (299 passed, 3 skipped tests).

2. 🔵 **SAFE DESIGN DECISION**:
   - Optocoupled 5V relay module on GPIO 27 with `LOAD ABSENT`.
   - Independent ESP32-CAM board transmitting JPEG payloads over MQTT.
   - 5V USB Type-C single power supply topology (429.5 mA peak).

3. 🟡 **ENGINEERING RECOMMENDATIONS**:
   - Mount sensor op-amp modules externally on dry MB-102 breadboard outside the 2500 mL water box.
   - If buzzer is a raw coil drawing >12 mA, acquire an NPN transistor driver before powering.

4. 🟠 **PHYSICAL SPECIFICATIONS REQUIRING VERIFICATION**:
   - pH amplifier module maximum voltage output range on physical bench.
   - Buzzer module internal circuit (active trigger module vs raw passive piezo coil).

5. 🔴 **UNSAFE / BLOCKED**:
   - Direct connection of raw 4.5V turbidity output to ESP32 ADC without resistor divider is **BLOCKED AS UNSAFE**.
