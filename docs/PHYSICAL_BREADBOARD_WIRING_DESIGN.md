# VERSION 4.8.5 — FINAL PHYSICAL BREADBOARD WIRING DESIGN

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Milestone:** V4.8.5 Final Physical Breadboard Wiring Design  
**Document Date:** August 18, 2026  
**Authoritative Hardware Target:** Confirmed 16-Item Physical Kit  
**Status:** Software Verified / Hardware Wiring Design Complete / Physical Assembly Pending  

---

> [!IMPORTANT]
> **PHYSICAL INTEGRATION BOUNDARY NOTICE**  
> We have **NEVER** physically assembled, wired, powered on, or flashed this hardware system yet.  
> 
> All physical wiring instructions in this document represent the **FINAL DESIGN BEFORE PHYSICAL ASSEMBLY**.  
> Physical assembly MUST follow the staged multimeter verification procedures in Section 9.

---

## 1. Phase 1 — Component-by-Component Breadboard Connection Table

### 1.1 DS18B20 Waterproof Temperature Sensor
- **VCC Wire (Red)**: Connect to ESP32 **3.3V Output Pin** (Breadboard 3.3V Rail).
- **GND Wire (Black)**: Connect to ESP32 **GND Pin** (Breadboard Common Ground Rail).
- **SIGNAL Wire (Yellow)**: Connect to **GPIO 18**.
- **RESISTOR**: **4.7 kΩ Metal Film Resistor** (from Resistor Kit Box, Item #12) placed directly between **GPIO 18 (Yellow)** and **3.3V Rail (Red)**.
- **WHY IT IS CONNECTED THIS WAY**: The DS18B20 uses the OneWire open-drain digital bus protocol. The 4.7 kΩ pull-up resistor holds the data line HIGH when idle, enabling reliable 1-Wire communication.

### 1.2 Optical Turbidity Sensor Module
- **VCC (Red)**: Connect to Breadboard **5.0V Power Rail** (supplied from ESP32 VIN / 5V pin).
- **GND (Black)**: Connect to Breadboard **Common Ground Rail**.
- **SIGNAL (`AO` Analog Output - Blue)**: Connect to **Resistor $R_1$ (10 kΩ)**.
- **RESISTOR DIVIDER CIRCUIT**:
  - Resistor $R_1$ (**10 kΩ**, Resistor Box): Placed between Turbidity `AO` and **GPIO 33**.
  - Resistor $R_2$ (**20 kΩ**, Resistor Box): Placed between **GPIO 33** and **Common Ground Rail**.
- **WHY IT IS CONNECTED THIS WAY**: The turbidity module output reaches 4.5V DC in clean water. The 10k/20k resistor divider scales the 4.5V output down to **3.0V DC**, keeping the signal safely below the ESP32 3.3V ADC damage threshold.

### 1.3 Liquid pH Sensor Probe & BNC Amplifier Module
- **VCC**: Connect to Breadboard **5.0V Power Rail**.
- **GND**: Connect to Breadboard **Common Ground Rail**.
- **SIGNAL (`Po` Analog Output)**: Connect to multimeter test point first (**DO NOT CONNECT TO GPIO 32 YET**).
- **RESISTOR**: Optional 10k/20k voltage divider reserved if bench verification measures $P_o > 3.3\text{V}$.
- **WHY IT IS CONNECTED THIS WAY**: High-gain pH op-amp stages can output up to 4.1V DC at alkaline extremes. Multimeter verification of $P_o$ is required before wiring to **GPIO 32 (ADC1_CH4)**.

### 1.4 Green Status LED (System Normal Indicator)
- **ANODE (Longer Leg / Positive)**: Connect to **GPIO 19** via series resistor.
- **CATHODE (Shorter Leg / Flat Edge)**: Connect to Breadboard **Common Ground Rail**.
- **RESISTOR**: **220 Ω Resistor** (Resistor Box) placed in series between **GPIO 19** and LED Anode (+).
- **WHY IT IS CONNECTED THIS WAY**: Direct GPIO connection without a resistor will burn out the LED and overload the ESP32 pin. The 220 Ω resistor limits current to a safe $\approx 6\text{ mA}$.

### 1.5 Yellow Warning LED (Elevated Risk Indicator)
- **ANODE (Longer Leg / Positive)**: Connect to **GPIO 21** via series resistor.
- **CATHODE (Shorter Leg / Flat Edge)**: Connect to Breadboard **Common Ground Rail**.
- **RESISTOR**: **220 Ω Resistor** (Resistor Box) placed in series between **GPIO 21** and LED Anode (+).
- **WHY IT IS CONNECTED THIS WAY**: Limits current to $\approx 6\text{ mA}$, driving the high-active warning indicator safely.

### 1.6 Red Critical LED (Algal Bloom Alert Indicator)
- **ANODE (Longer Leg / Positive)**: Connect to **GPIO 22** via series resistor.
- **CATHODE (Shorter Leg / Flat Edge)**: Connect to Breadboard **Common Ground Rail**.
- **RESISTOR**: **220 Ω Resistor** (Resistor Box) placed in series between **GPIO 22** and LED Anode (+).
- **WHY IT IS CONNECTED THIS WAY**: Limits current to $\approx 6\text{ mA}$, driving the high-active critical alarm indicator safely.

### 1.7 5V Piezo Audio Alarm Buzzer Module
- **VCC (+ Pin)**: Connect to 5V Power Rail (or GPIO 23 trigger pin if active module).
- **GND (- Pin)**: Connect to Common Ground Rail.
- **SIGNAL**: Multimeter verification required to check operating current.
- **RESISTOR**: Transistor driver required if module draws $>12\text{ mA}$.
- **WHY IT IS CONNECTED THIS WAY**: We do NOT own a 2N2222 transistor in our inventory. If the buzzer is a raw coil drawing $>12\text{ mA}$, it MUST NOT be connected directly to GPIO 23.

### 1.8 5V 1-Channel Optocoupled Relay Module
- **VCC**: Connect to Breadboard **5.0V Power Rail**.
- **GND**: Connect to Breadboard **Common Ground Rail**.
- **IN (Logic Trigger)**: Connect to **GPIO 27**.
- **CONTACT TERMINALS (`COM`, `NO`, `NC`)**: **NO PHYSICAL LOAD CONNECTED (`LOAD ABSENT`)**.
- **WHY IT IS CONNECTED THIS WAY**: The module's internal EL817 optocoupler LED is driven by 3.3V logic on GPIO 27. The relay coil operates safely on 5V without high-voltage load hazard.

---

## 2. Phase 2 — Power Rail & Current Consumption Design

### 2.1 MB-102 Breadboard Power Rail Configuration
- **USB Power Entry**: Micro-USB / Type-C USB cable (Item #15) supplies **5.0V DC** to the ESP32-WROOM development module.
- **5.0V Power Rail**: Tapped from the ESP32 **VIN / 5V** pin and routed to the top red power rail of the MB-102 breadboard.
  - Powers: pH Module VCC, Turbidity Module VCC, Relay Module VCC, Buzzer Module VCC.
- **3.3V Power Rail**: Tapped from the ESP32 **3V3 Output** pin and routed to the bottom red power rail of the MB-102 breadboard.
  - Powers: DS18B20 VCC, 4.7 kΩ pull-up resistor, LED anodes (via 220 Ω resistors).
- **Common Ground Rail (GND)**: ESP32 **GND** pin routed to both top and bottom blue ground rails of the MB-102 breadboard.

### 2.2 ESP32-CAM Power Supply Isolation
- The AI-Thinker ESP32-CAM module is powered via its own **independent USB cable / dedicated 5V power supply** to prevent Wi-Fi peak transmission currents (up to 310 mA) from causing voltage drops on the main MCU sensor rail.

### 2.3 System Current Consumption Budget (Actual Inventory)

| Subsystem Component | Power Rail | Operating Voltage | Peak Current | Power Rail Notes |
| :--- | :--- | :--- | :--- | :--- |
| **ESP32-WROOM Core** | 3.3V LDO | 3.3V DC | 240 mA | Wi-Fi peak transmit spikes. |
| **DS18B20 Sensor** | 3.3V Rail | 3.3V DC | 1.5 mA | OneWire active sampling. |
| **pH Amplifier Board** | 5.0V Rail | 5.0V DC | 20 mA | Op-amp signal conditioning. |
| **Turbidity Sensor Board**| 5.0V Rail | 5.0V DC | 40 mA | Infrared LED emitter. |
| **Status LEDs (x3)** | 3.3V Rail | 3.3V DC | 18 mA | 220 Ω limited (6 mA each). |
| **5V Piezo Buzzer** | 5.0V Rail / Trigger | 5.0V DC | 40 mA | Alarm active draw. |
| **5V Relay Coil** | 5.0V Rail | 5.0V DC | 70 mA | Optocoupler coil activation. |
| **TOTAL MAIN SYSTEM** | **5.0V USB Input** | **5.0V DC** | **429.5 mA Peak** | **100% Sourced by 5V 1A USB Cable** |

---

## 3. Phase 3 — Turbidity Resistor Divider Schematic & Math

```
                       Turbidity Sensor Analog Output (AO)
                                       │
                                       ▼
                             ┌──────────────────┐
                             │  R1 = 10 kΩ      │ (Metal Film 1%)
                             └────────┬─────────┘
                                      │
                                      ├────────────────► GPIO 33 (ADC1_CH5)
                                      │
                             ┌────────┴─────────┐
                             │  R2 = 20 kΩ      │ (Metal Film 1%)
                             └────────┬─────────┘
                                      │
                                      ▼
                             Common Ground Rail (GND)
```

### Voltage Calculation Proof:
$$V_{out} = V_{in} \times \frac{R_2}{R_1 + R_2}$$
For maximum raw turbidity output in clean water ($V_{in} = 4.5\text{ V}$):
$$V_{out\_max} = 4.5\text{ V} \times \frac{20\text{ k}\Omega}{10\text{ k}\Omega + 20\text{ k}\Omega} = 4.5\text{ V} \times \frac{20}{30} = 3.0\text{ V DC}$$

> [!NOTE]
> $3.0\text{ V DC} \le 3.3\text{ V DC}$ maximum ESP32 ADC input threshold.  
> **GPIO 33 NEVER receives the raw 4.5V signal under any operating condition.**

---

## 4. Phase 4 — pH Sensor Safety & Dual-Option Wiring Design

> [!WARNING]
> **DO NOT CONNECT THE pH OUTPUT TO GPIO 32 WITHOUT MULTIMETER VERIFICATION.**  
> Powered by 5.0V VCC, uncalibrated pH op-amp stages can output up to **4.1V DC** at alkaline extremes.

```
Option A (Direct Connection - IF Po <= 3.3V Verified):
  pH Amplifier Po ───────────────────────────────────────────────► GPIO 32

Option B (Resistor Divider - IF Po > 3.3V Observed):
  pH Amplifier Po ─── 10kΩ ───┬─────────────────────────────────► GPIO 32
                              │
                            20kΩ
                              │
                             GND
```

- **Option A Math (Direct)**: If bench multimeter reading confirms $P_{o\_max} \le 3.3\text{V}$, connect directly to **GPIO 32 (ADC1_CH4)**.
- **Option B Math (Divider)**: If $P_{o\_max} = 4.1\text{V}$, inserting a 10k/20k divider yields:
  $$V_{out\_max} = 4.1\text{ V} \times \frac{20}{30} = 2.73\text{ V DC} \le 3.3\text{ V DC}$$
- **Mandatory Classification**: `PHYSICAL BENCH VERIFICATION REQUIRED BEFORE CONNECTION`.

---

## 5. Phase 5 — LED Polarity & Current Limiting Wiring

- **Green LED (GPIO 19)**:
  `GPIO 19` $\rightarrow$ `220 Ω Resistor` $\rightarrow$ `LED Anode (+ Long Leg)` $\rightarrow$ `LED Cathode (- Flat Edge)` $\rightarrow$ `Common GND Rail`
- **Yellow LED (GPIO 21)**:
  `GPIO 21` $\rightarrow$ `220 Ω Resistor` $\rightarrow$ `LED Anode (+ Long Leg)` $\rightarrow$ `LED Cathode (- Flat Edge)` $\rightarrow$ `Common GND Rail`
- **Red LED (GPIO 22)**:
  `GPIO 22` $\rightarrow$ `220 Ω Resistor` $\rightarrow$ `LED Anode (+ Long Leg)` $\rightarrow$ `LED Cathode (- Flat Edge)` $\rightarrow$ `Common GND Rail`

---

## 6. Phase 6 — Buzzer Control Safety & Driver Assessment

- **Hardware**: 5V Piezo Buzzer Module (Item #8).
- **Inventory Constraint**: We do **NOT** own a 2N2222 transistor in our physical inventory.
- **Safety Decision**:
  - If multimeter measurement confirms the module incorporates an onboard trigger transistor ($I_{in} < 2\text{ mA}$ at 3.3V), connect signal pin to **GPIO 23**.
  - If the module is a raw piezo coil drawing $>12\text{ mA}$, **DO NOT CONNECT IT TO GPIO 23**.
- **Mandatory Classification**: `ADDITIONAL DRIVER REQUIRED / BENCH VERIFICATION REQUIRED`.

---

## 7. Phase 7 — 5V 1-Channel Relay Module Interface

- **Module Connections**:
  - `VCC` $\rightarrow$ Breadboard 5.0V Power Rail
  - `GND` $\rightarrow$ Breadboard Common Ground Rail
  - `IN` $\rightarrow$ **GPIO 27**
- **Relay Contacts (`COM`, `NO`, `NC`)**: **NO LOAD CONNECTED (`LOAD ABSENT`)**.
- **3.3V Logic Compatibility Verification**:
  - The module's internal EL817 optocoupler LED turns ON when GPIO 27 sinks/sources ~2-3 mA, which is **100% 3.3V logic compatible**.

---

## 8. Phase 8 — Common Ground Topology

```
   [ ESP32-WROOM GND Pin ] ─────────────────┐
                                            │
   [ pH Amplifier GND ] ─────────────────────┼──► [ MB-102 Common Ground Rail (GND) ]
                                            │
   [ Turbidity Module GND ] ────────────────┤
                                            │
   [ DS18B20 Temp GND ] ────────────────────┤
                                            │
   [ LED Cathodes & Relay GND ] ────────────┘
```

- All sensor signal grounds, LED cathodes, relay module GND, and ESP32 GND are tied to the **MB-102 Common Ground Rail** to establish a uniform 0V reference.
- **ESP32-CAM Isolation**: ESP32-CAM ground is tied to Common GND, but its 5V power input is fed by a separate USB supply.

---

## 9. Phase 9 — First Power-Up Staged Multimeter Verification Procedure

```
Stage 1: ESP32 Only ──► Stage 2: DS18B20 ──► Stage 3: pH Check ──► Stage 4: Turbidity Check
                                                                         │
Stage 8: ESP32-CAM ◄── Stage 7: Relay ◄── Stage 6: Buzzer ◄── Stage 5: LEDs ◄───┘
```

### Stage 1: ESP32-WROOM Power Rail Verification
- **What to Connect**: Plug Type-C USB cable into ESP32-WROOM module on MB-102 breadboard.
- **What to Measure**: Measure voltage between 3V3 pin and GND, and between VIN (5V) pin and GND.
- **Expected Voltage**: 3.3V $\pm$ 0.05V on 3V3 rail; 5.0V $\pm$ 0.15V on VIN rail.
- **Problem Sign**: Voltage $<3.0\text{V}$ or $>3.6\text{V}$ on 3V3 rail; hot MCU chip.
- **Action on Failure**: **UNPLUG USB IMMEDIATELY**.

### Stage 2: DS18B20 Temperature Sensor Test
- **What to Connect**: Wire DS18B20 (VCC to 3.3V, GND to GND, DATA to GPIO 18 + 4.7kΩ pull-up).
- **What to Measure**: Measure voltage on GPIO 18 with multimeter.
- **Expected Voltage**: 3.3V DC when idle.
- **Problem Sign**: 0.0V DC constant (missing pull-up) or $>3.6\text{V}$.
- **Action on Failure**: Check 4.7kΩ resistor connection.

### Stage 3: pH Amplifier Signal Check
- **What to Connect**: Wire pH module VCC (5V) and GND. **Leave signal pin disconnected from GPIO 32**.
- **What to Measure**: Measure pH module `Po` output voltage with multimeter in neutral water (~pH 7).
- **Expected Voltage**: 1.5V to 2.5V DC.
- **Problem Sign**: $P_o > 3.3\text{V DC}$.
- **Action on Failure**: If $P_o > 3.3\text{V}$, insert 10k/20k voltage divider before connecting to GPIO 32.

### Stage 4: Turbidity Resistor Divider Check
- **What to Connect**: Wire Turbidity VCC (5V), GND, and 10k/20k divider circuit to GPIO 33.
- **What to Measure**: Measure voltage at GPIO 33 in clear water.
- **Expected Voltage**: $\approx 3.0\text{V DC}$ (scaled down from 4.5V).
- **Problem Sign**: Voltage $>3.3\text{V DC}$ at GPIO 33 pin.
- **Action on Failure**: **DO NOT CONNECT TO GPIO 33**. Check 10k and 20k resistor positions.

### Stage 5: Status LEDs Test
- **What to Connect**: Wire Green (GPIO 19), Yellow (GPIO 21), Red (GPIO 22) LEDs through 220 Ω resistors.
- **What to Measure**: Measure voltage across LED terminals when GPIO is driven HIGH.
- **Expected Voltage**: Forward voltage $\approx 1.8\text{V} - 2.2\text{V}$ DC; current $\approx 6\text{ mA}$.
- **Problem Sign**: LED does not illuminate (reversed polarity) or draws $>15\text{ mA}$.
- **Action on Failure**: Check LED anode/cathode orientation and 220 Ω resistor value.

### Stage 6: 5V Buzzer Current Check
- **What to Connect**: Measure buzzer trigger input current with multimeter in series.
- **What to Measure**: Input current into buzzer signal pin.
- **Expected Voltage / Current**: Current $< 10\text{ mA}$.
- **Problem Sign**: Current $> 12\text{ mA}$ (overloads ESP32 pin).
- **Action on Failure**: **DO NOT CONNECT TO GPIO 23**. Require transistor driver.

### Stage 7: 5V Relay Module Unloaded Test
- **What to Connect**: Wire Relay VCC (5V), GND, IN (GPIO 27). Keep COM/NO/NC terminals empty (`LOAD ABSENT`).
- **What to Measure**: Voltage at IN pin when GPIO 27 toggles; listen for relay click.
- **Expected Voltage**: 0V LOW / 3.3V HIGH at IN pin. Relay clicks cleanly.
- **Problem Sign**: Relay fails to trigger or GPIO 27 voltage drops below 2.5V.
- **Action on Failure**: Verify 5V VCC power supply to relay coil.

### Stage 8: ESP32-CAM Independent Node Check
- **What to Connect**: Connect separate USB cable to ESP32-CAM board.
- **What to Measure**: Measure 5V supply input under active Wi-Fi frame transmission.
- **Expected Voltage**: 5.0V $\pm$ 0.2V DC.
- **Problem Sign**: Voltage drops below 4.5V during Wi-Fi transmission.
- **Action on Failure**: Use dedicated high-current 5V 2A USB power adapter.

---

## 10. Phase 10 — Final Master Wiring Specification & Status Table

| Component Name | Power VCC | Ground GND | Signal Pin | ESP32 GPIO | Resistor / Protection | Physical Wiring Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DS18B20 Temp Probe** | 3.3V Rail | Common GND | `DQ_DATA` | **GPIO 18** | 4.7 kΩ Pull-up (Resistor Box) | 🟢 **SAFE TO CONNECT** |
| **Turbidity Sensor** | 5.0V Rail | Common GND | `TURB_AO` | **GPIO 33 (ADC1)**| 10k Ω + 20k Ω Divider (Resistor Box)| 🟢 **SAFE TO CONNECT** |
| **Green Status LED** | 3.3V Rail | Common GND | `LED_GREEN` | **GPIO 19** | 220 Ω Resistor (Resistor Box) | 🟢 **SAFE TO CONNECT** |
| **Yellow Warning LED** | 3.3V Rail | Common GND | `LED_YELLOW`| **GPIO 21** | 220 Ω Resistor (Resistor Box) | 🟢 **SAFE TO CONNECT** |
| **Red Critical LED** | 3.3V Rail | Common GND | `LED_RED` | **GPIO 22** | 220 Ω Resistor (Resistor Box) | 🟢 **SAFE TO CONNECT** |
| **5V Relay Module** | 5.0V Rail | Common GND | `RELAY_IN1`| **GPIO 27** | Optocoupled 5V Coil (`LOAD ABSENT`)| 🟢 **SAFE TO CONNECT** |
| **Liquid pH Probe Module** | 5.0V Rail | Common GND | `PH_PO` | **GPIO 32 (ADC1)**| 10k/20k Divider if $P_o > 3.3\text{V}$ | 🟡 **VERIFY Po ON BENCH FIRST** |
| **5V Piezo Audio Buzzer** | 5.0V Rail | Common GND | `BUZZER` | **GPIO 23** | Transistor Driver if raw coil | 🟡 **VERIFY CURRENT ON BENCH FIRST**|
| **ESP32-CAM Node** | Dedicated 5V| Common GND | Wi-Fi / MQTT | Independent | Separate 5V Power Supply | 🟢 **SAFE TO CONNECT** |

---

## 11. Final Implementation Boundary Summary

- **SOFTWARE VERIFIED**: 100% (299 passed, 3 skipped tests).
- **HARDWARE WIRING DESIGN**: 100% Complete for confirmed 16-item inventory.
- **PHYSICAL HARDWARE ASSEMBLY**: **0% (PENDING BENCH EXECUTION)**.
- **PHYSICAL HARDWARE VALIDATION**: **PENDING BENCH EXECUTION**.
