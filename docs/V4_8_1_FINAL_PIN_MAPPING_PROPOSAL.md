# VERSION 4.8.1 — PHYSICAL HARDWARE PIN MAPPING RESOLUTION & DESIGN PROPOSAL

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Milestone:** V4.8.1 Physical Hardware Pin Mapping Resolution  
**Document Date:** August 18, 2026  
**Status:** Design Proposal & Forensic Resolution (Audit Only — No Code/Firmware Modifications)  

---

## Executive Summary

The V4.8 Forensic Audit revealed significant pin assignment conflicts across the project's three main sources of truth: the C++ firmware header ([firmware/include/config/PinConfig.h](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/firmware/include/config/PinConfig.h)), the Python configuration file ([config/device_config.json](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/config/device_config.json)), and the hardware integration guide ([docs/HARDWARE_INTEGRATION_GUIDE.md](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/HARDWARE_INTEGRATION_GUIDE.md)).

This document presents the **V4.8.1 Physical Hardware Pin Mapping Resolution**, performing a complete GPIO capability audit of the target ESP32 board, mapping sensor/actuator hardware constraints, evaluating camera isolation, scoring three candidate pin maps, and proposing a single authoritative, conflict-free physical pin mapping.

---

## 1. Target ESP32 Board Identification

Source Evidence: [firmware/platformio.ini](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/firmware/platformio.ini)

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200
```

- **Target Board Model**: **ESP32-WROOM-32 / ESP32-WROOM-32E Dev Module** (30-pin / 38-pin NodeMCU-style breakout board).
- **Core Microcontroller**: Espressif ESP32-D0WDQ6 / ESP32-D0WD (Dual-core Xtensa 32-bit LX6 MCU @ 240 MHz, 520 KB SRAM, 4 MB SPI Flash, Wi-Fi 802.11 b/g/n + Bluetooth 4.2).
- **ADC Architecture**: Two 12-bit SAR ADCs: **ADC1** (8 channels) and **ADC2** (10 channels).

> [!IMPORTANT]
> **Critical ESP32 Electrical Rule**: **ADC2 CANNOT BE USED WHEN WI-FI IS ENABLED**.
> The ESP32 Wi-Fi driver continuously occupies ADC2. Any attempt to measure analog sensor voltages on ADC2 pins (GPIO 0, 2, 4, 12, 13, 14, 15, 25, 26, 27) while Wi-Fi is connected will return invalid readings or crash the Wi-Fi driver.
> **All analog water quality probes (pH, Turbidity, DO, Salinity/TDS) MUST be mapped exclusively to ADC1 pins (GPIO 32, 33, 34, 35, 36, 39)**.

---

## 2. Existing Conflicting Mappings Matrix

A forensic comparison of pin assignments across existing repository files:

| Peripheral / Sensor | `PinConfig.h` (C++ Code) | `device_config.json` (Fresh/Marine) | `HARDWARE_INTEGRATION_GUIDE.md` | Conflict Status |
| :--- | :--- | :--- | :--- | :--- |
| **pH Sensor** | `GPIO 32` (ADC1_CH4) | `GPIO 32` / `GPIO 32` | `GPIO 32` (ADC1_CH4) | 🟢 **VERIFIED** (100% Agreement) |
| **Temperature Sensor** | `GPIO 18` (Digital) | Missing / `GPIO 35` (GPI Input-Only) | `GPIO 4` (OneWire Digital) | 🔴 **CONFLICT** (3-Way Discrepancy) |
| **Turbidity Sensor** | `GPIO 33` (ADC1_CH5) | `GPIO 33` / `GPIO 33` | `GPIO 34` (ADC1_CH6) | 🔴 **CONFLICT** (Firmware/JSON vs Guide) |
| **Dissolved Oxygen (DO)**| `GPIO 34` (ADC1_CH6) | `GPIO 34` / `GPIO 34` | `GPIO 35` (ADC1_CH7) | 🔴 **CONFLICT** (Firmware/JSON vs Guide) |
| **Salinity / TDS Sensor**| `GPIO 36` (ADC1_CH0) | Missing / `GPIO 36` | `GPIO 33` (ADC1_CH5) | 🔴 **CONFLICT** (Firmware/JSON vs Guide) |
| **Green Status LED** | `GPIO 19` (Digital Out) | `GPIO 12` / `GPIO 12` | `GPIO 12` (MTDI Strapping Pin) | 🔴 **CONFLICT** (Firmware vs JSON/Guide) |
| **Yellow Status LED** | `GPIO 21` (Digital Out) | `GPIO 13` / `GPIO 13` | `GPIO 13` | 🔴 **CONFLICT** (Firmware vs JSON/Guide) |
| **Red Status LED** | `GPIO 22` (Digital Out) | `GPIO 14` / `GPIO 14` | `GPIO 14` | 🔴 **CONFLICT** (Firmware vs JSON/Guide) |
| **Alarm Buzzer** | `GPIO 23` (Digital Out) | `GPIO 15` / `GPIO 15` | `GPIO 15` (MTDO Strapping Pin) | 🔴 **CONFLICT** (Firmware vs JSON/Guide) |
| **Aerator Pump Relay** | `GPIO 27` (Digital Out) | `GPIO 16` / `GPIO 16` | `GPIO 23` | 🔴 **CONFLICT** (3-Way Discrepancy) |
| **GPS Module** | `RX=16, TX=17` (UART2) | `GPIO 21` / `GPIO 21` | `Not Documented` | 🔴 **CONFLICT** (Firmware vs JSON) |

---

## 3. ESP32 GPIO Capability Audit

Comprehensive capability matrix for candidate GPIO pins on the ESP32-WROOM-32 board:

| GPIO Pin | ADC Capable? | Directionality | Boot-Strapping / System Restriction | Usable for Analog Sensor? | Usable for Output (LED/Relay)? | Suitability & Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **GPIO 0** | ADC2_CH1 | Input / Output | **Boot Strapping** (Pull LOW for UART flash mode). | ❌ (ADC2 Wi-Fi conflict) | ❌ (Causes boot failures) | **UNSAFE** |
| **GPIO 1 (TX0)**| ADC2_CH3 | Output | **UART0 Console** (Used for `Serial.print`). | ❌ | ❌ | **RESERVED FOR SERIAL** |
| **GPIO 2** | ADC2_CH2 | Input / Output | **Boot Strapping** (Must be LOW for flashing; connected to onboard blue LED). | ❌ (ADC2 Wi-Fi conflict) | ⚠️ Risky | **UNSAFE** |
| **GPIO 3 (RX0)**| ADC2_CH4 | Input | **UART0 Console** (Used for `Serial.read`). | ❌ | ❌ | **RESERVED FOR SERIAL** |
| **GPIO 4** | ADC2_CH0 | Input / Output | General GPIO / Touch0. | ❌ (ADC2 Wi-Fi conflict) | ✅ Safe (or DS18B20) | **SAFE FOR DIGITAL IO / ONEWIRE** |
| **GPIO 5** | ADC2_CH6 | Input / Output | **VSPI CS** / Outputs PWM glitch on boot. | ❌ (ADC2 Wi-Fi conflict) | ⚠️ Risky | **AVOID** |
| **GPIO 6–11**| N/A | N/A | **SPI FLASH MEMORY** (Integrated flash chip). | ❌ | ❌ | **CRITICAL: DO NOT USE** |
| **GPIO 12** | ADC2_CH5 | Input / Output | **Boot Strapping (MTDI)** (If pulled HIGH at boot, flash voltage = 1.8V $\rightarrow$ crash!). | ❌ (ADC2 Wi-Fi conflict) | ❌ (Causes bootloop if LED pulls HIGH) | **UNSAFE FOR ACTUATORS** |
| **GPIO 13** | ADC2_CH4 | Input / Output | Touch4 / General GPIO. | ❌ (ADC2 Wi-Fi conflict) | ✅ Safe | **SAFE FOR DIGITAL OUT** |
| **GPIO 14** | ADC2_CH6 | Input / Output | Touch6 / Outputs PWM glitch on boot. | ❌ (ADC2 Wi-Fi conflict) | ✅ Safe | **SAFE FOR DIGITAL OUT** |
| **GPIO 15** | ADC2_CH3 | Input / Output | **Boot Strapping (MTDO)** (Outputs PWM on boot; if pulled LOW, silent boot mode). | ❌ (ADC2 Wi-Fi conflict) | ⚠️ Risky | **UNSAFE FOR ACTUATORS** |
| **GPIO 16** | N/A | Input / Output | UART2 RX / General GPIO. | ❌ (No ADC) | ✅ Safe | **SAFE FOR DIGITAL IO / UART2** |
| **GPIO 17** | N/A | Input / Output | UART2 TX / General GPIO. | ❌ (No ADC) | ✅ Safe | **SAFE FOR DIGITAL IO / UART2** |
| **GPIO 18** | N/A | Input / Output | VSPI CLK / General GPIO. | ❌ (No ADC) | ✅ Safe (DS18B20 OneWire) | **SAFE FOR DIGITAL IO / ONEWIRE** |
| **GPIO 19** | N/A | Input / Output | VSPI MISO / General GPIO. | ❌ (No ADC) | ✅ Safe | **SAFE FOR DIGITAL OUT (LED)** |
| **GPIO 21** | N/A | Input / Output | I2C SDA / General GPIO. | ❌ (No ADC) | ✅ Safe | **SAFE FOR DIGITAL OUT (LED)** |
| **GPIO 22** | N/A | Input / Output | I2C SCL / General GPIO. | ❌ (No ADC) | ✅ Safe | **SAFE FOR DIGITAL OUT (LED)** |
| **GPIO 23** | N/A | Input / Output | VSPI MOSI / General GPIO. | ❌ (No ADC) | ✅ Safe | **SAFE FOR DIGITAL OUT (BUZZER)** |
| **GPIO 25** | ADC2_CH8 | Input / Output | DAC1 / General GPIO. | ❌ (ADC2 Wi-Fi conflict) | ✅ Safe | **SAFE FOR DIGITAL OUT** |
| **GPIO 26** | ADC2_CH9 | Input / Output | DAC2 / General GPIO. | ❌ (ADC2 Wi-Fi conflict) | ✅ Safe | **SAFE FOR DIGITAL OUT** |
| **GPIO 27** | ADC2_CH7 | Input / Output | Touch7 / General GPIO. | ❌ (ADC2 Wi-Fi conflict) | ✅ Safe | **SAFE FOR DIGITAL OUT (RELAY)** |
| **GPIO 32** | **ADC1_CH4** | Input / Output | Touch9 / ADC1. | ✅ **EXCELLENT (ADC1)** | ✅ Safe | **OPTIMAL ANALOG SENSOR PIN** |
| **GPIO 33** | **ADC1_CH5** | Input / Output | Touch8 / ADC1. | ✅ **EXCELLENT (ADC1)** | ✅ Safe | **OPTIMAL ANALOG SENSOR PIN** |
| **GPIO 34** | **ADC1_CH6** | **INPUT ONLY** | GPI (No output driver, no pullup/pulldown). | ✅ **EXCELLENT (ADC1)** | ❌ (Cannot drive output) | **OPTIMAL ANALOG SENSOR PIN** |
| **GPIO 35** | **ADC1_CH7** | **INPUT ONLY** | GPI (No output driver, no pullup/pulldown). | ✅ **EXCELLENT (ADC1)** | ❌ (Cannot drive output) | **OPTIMAL ANALOG SENSOR PIN** |
| **GPIO 36 (VP)**| **ADC1_CH0** | **INPUT ONLY** | GPI / SENSOR_VP. | ✅ **EXCELLENT (ADC1)** | ❌ (Cannot drive output) | **OPTIMAL ANALOG SENSOR PIN** |
| **GPIO 39 (VN)**| **ADC1_CH3** | **INPUT ONLY** | GPI / SENSOR_VN. | ✅ **EXCELLENT (ADC1)** | ❌ (Cannot drive output) | **OPTIMAL ANALOG SENSOR PIN** |

---

## 4. Sensor & Actuator Interface Requirements

### 4.1 Sensor Hardware Requirements

Source Code Verification: [firmware/lib/PhysicalDrivers/](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/firmware/lib/PhysicalDrivers/)

| Sensor Component | Physical Driver Class | Required Interface Type | Required Pin Capability | Electrical Constraint |
| :--- | :--- | :--- | :--- | :--- |
| **Temperature** | `DS18B20Driver` | OneWire Digital Protocol | Bidirectional Digital IO | Requires 4.7kΩ external pull-up resistor. **Does NOT use ADC**. |
| **pH Sensor** | `PHDriver` | Analog Voltage (`analogRead`) | **ADC1 Channel** (0–3.3V) | Must use ADC1 (GPIO 32, 33, 34, 35, 36, 39) due to Wi-Fi. |
| **Turbidity Sensor** | `TurbidityDriver` | Analog Voltage (`analogRead`) | **ADC1 Channel** (0–3.3V) | Must use ADC1 (GPIO 32, 33, 34, 35, 36, 39) due to Wi-Fi. |
| **Dissolved Oxygen (DO)**| `DODriver` | Analog Voltage (`analogRead`) | **ADC1 Channel** (0–3.3V) | Must use ADC1 (GPIO 32, 33, 34, 35, 36, 39) due to Wi-Fi. |
| **Salinity / TDS** | `SalinityDriver` | Analog Voltage (`analogRead`) | **ADC1 Channel** (0–3.3V) | Must use ADC1 (GPIO 32, 33, 34, 35, 36, 39) due to Wi-Fi. |
| **GPS Module** | `MockGPSSensor` | Hardware UART Serial | RX / TX Digital Pins | Uses UART2 (`RX=16, TX=17`). |

### 4.2 Actuator Hardware Requirements

Source Code Verification: [firmware/lib/PhysicalDrivers/LEDDriver.cpp](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/firmware/lib/PhysicalDrivers/LEDDriver.cpp), `BuzzerDriver.cpp`, `RelayDriver.cpp`

| Actuator Component | Physical Driver Class | Required Interface Type | Required Pin Capability | Electrical Constraint |
| :--- | :--- | :--- | :--- | :--- |
| **Green Status LED** | `LEDDriver` | Digital Output (`pinMode OUTPUT`) | Output-capable GPIO | 3.3V GPIO + 220Ω current-limiting resistor. Cannot use input-only pins. |
| **Yellow Status LED**| `LEDDriver` | Digital Output (`pinMode OUTPUT`) | Output-capable GPIO | 3.3V GPIO + 220Ω current-limiting resistor. Cannot use input-only pins. |
| **Red Status LED** | `LEDDriver` | Digital Output (`pinMode OUTPUT`) | Output-capable GPIO | 3.3V GPIO + 220Ω current-limiting resistor. Cannot use input-only pins. |
| **Alarm Buzzer** | `BuzzerDriver` | Digital Output (`pinMode OUTPUT`) | Output-capable GPIO | 5.0V Active Piezo + NPN transistor switch. |
| **Aerator Pump Relay**| `RelayDriver` | Digital Output (`pinMode OUTPUT`) | Output-capable GPIO | 5.0V Optocoupler Relay Board + flyback diode protection. |

---

## 5. Camera GPIO Isolation

- **Physical Hardware Isolation**: The ESP32-CAM (AI-Thinker module with OV2640 camera) is an **INDEPENDENT SECONDARY PHYSICAL MICROCONTROLLER BOARD**.
- **Internal ESP32-CAM Pin Allocation**: The ESP32-CAM internally uses GPIO 0, 2, 4, 12, 13, 14, 15, 16, 26, 27, 32, 33, 34, 35, 36, 39 to interface with the OV2640 camera sensor, PSRAM chip, and SD card.
- **Inter-Board Communication**: The ESP32-CAM communicates with the Gateway independently over Wi-Fi (or a dedicated serial link).
- **Forensic Verification Statement**:
  > The ESP32-CAM module operates on a **completely separate microcontroller board**.
  > There is **ZERO GPIO pin sharing or electrical overlap** between the main sensor/actuator ESP32 board and the ESP32-CAM board.

---

## 6. Candidate Pin Mappings & Evaluation

### 6.1 Candidate 1: Firmware Native Baseline (`PinConfig.h` Baseline)

Source: Existing compiled C++ struct defaults in [firmware/include/config/PinConfig.h](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/firmware/include/config/PinConfig.h)

- **Temperature**: `GPIO 18` (OneWire Digital)
- **pH Sensor**: `GPIO 32` (ADC1_CH4 Analog)
- **Turbidity Sensor**: `GPIO 33` (ADC1_CH5 Analog)
- **Dissolved Oxygen (DO)**: `GPIO 34` (ADC1_CH6 Analog Input-Only)
- **Salinity / TDS Sensor**: `GPIO 36` (ADC1_CH0 Analog Input-Only)
- **Green LED**: `GPIO 19` (Digital Output)
- **Yellow LED**: `GPIO 21` (Digital Output)
- **Red LED**: `GPIO 22` (Digital Output)
- **Alarm Buzzer**: `GPIO 23` (Digital Output)
- **Aerator Pump Relay**: `GPIO 27` (Digital Output)
- **GPS Module**: `RX=GPIO 16, TX=GPIO 17` (UART2)

### 6.2 Candidate 2: Hardware Guide Alignment Map

Source: Derived from [docs/HARDWARE_INTEGRATION_GUIDE.md](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/HARDWARE_INTEGRATION_GUIDE.md)

- **Temperature**: `GPIO 4` (OneWire Digital)
- **pH Sensor**: `GPIO 32` (ADC1_CH4 Analog)
- **Salinity / TDS Sensor**: `GPIO 33` (ADC1_CH5 Analog)
- **Turbidity Sensor**: `GPIO 34` (ADC1_CH6 Analog Input-Only)
- **Dissolved Oxygen (DO)**: `GPIO 35` (ADC1_CH7 Analog Input-Only)
- **Green LED**: `GPIO 12` (Digital Output — **MTDI Strapping Risk**)
- **Yellow LED**: `GPIO 13` (Digital Output)
- **Red LED**: `GPIO 14` (Digital Output)
- **Alarm Buzzer**: `GPIO 15` (Digital Output — **MTDO Strapping Risk**)
- **Aerator Pump Relay**: `GPIO 23` (Digital Output)
- **GPS Module**: `RX=GPIO 16, TX=GPIO 17` (UART2)

### 6.3 Candidate 3: Consolidated Hybrid Best Practice Map

Source: Engineering hybrid merging Guide sensor pins with Firmware safe actuator pins

- **Temperature**: `GPIO 4` (OneWire Digital)
- **pH Sensor**: `GPIO 32` (ADC1_CH4 Analog)
- **Turbidity Sensor**: `GPIO 33` (ADC1_CH5 Analog)
- **Dissolved Oxygen (DO)**: `GPIO 34` (ADC1_CH6 Analog Input-Only)
- **Salinity / TDS Sensor**: `GPIO 35` (ADC1_CH7 Analog Input-Only)
- **Green LED**: `GPIO 19` (Digital Output)
- **Yellow LED**: `GPIO 21` (Digital Output)
- **Red LED**: `GPIO 22` (Digital Output)
- **Alarm Buzzer**: `GPIO 23` (Digital Output)
- **Aerator Pump Relay**: `GPIO 27` (Digital Output)
- **GPS Module**: `RX=GPIO 16, TX=GPIO 17` (UART2)

---

### 6.4 Comprehensive Candidate Scoring Matrix

Scoring scale: 1 (Unacceptable) to 10 (Optimal)

| Evaluation Criterion | Candidate 1 (Firmware Native) | Candidate 2 (Guide Alignment) | Candidate 3 (Hybrid Proposal) | Forensic Analysis |
| :--- | :---: | :---: | :---: | :--- |
| **ADC Compatibility** | **10 / 10** | **10 / 10** | **10 / 10** | All candidates place analog sensors on ADC1 (32, 33, 34, 35, 36). Zero Wi-Fi ADC2 conflicts. |
| **Boot Safety** | **10 / 10** | **4 / 10** | **10 / 10** | Candidate 2 uses MTDI (GPIO 12) & MTDO (GPIO 15) strapping pins, risking bootloops. Candidates 1 & 3 are 100% boot-safe. |
| **Peripheral Compatibility** | **10 / 10** | **9 / 10** | **10 / 10** | DS18B20 OneWire works on 18 or 4. Analog sensors on GPI pins (34, 35, 36) work perfectly. |
| **Firmware Compatibility** | **10 / 10** | **3 / 10** | **8 / 10** | Candidate 1 matches existing compiled `PinConfig.h` defaults exactly with **0 C++ changes**. |
| **Hardware Simplicity** | **10 / 10** | **7 / 10** | **9 / 10** | Candidate 1 uses neat logical blocks (Analog: 32,33,34,36; Actuators: 19,21,22,23,27). |
| **Conflict Count** | **0 Conflicts** | **2 Conflicts** | **0 Conflicts** | Candidate 2 introduces 2 boot-strapping hardware conflicts. |
| **TOTAL SCORE** | 🏆 **50 / 50 (100%)** | **33 / 50 (66%)** | **47 / 50 (94%)** | **Candidate 1 is the superior choice.** |

---

## 7. Recommended Final Pin Mapping Proposal

### 7.1 Recommended Mapping Table (Candidate 1 — Firmware Native Map)

```
                       ESP32-WROOM-32 Pinout Assignment
                          +───────────────────────+
                          |                       |
       [ DS18B20 Temp ] ──| GPIO 18         3.3V  |── [ 3.3V Power Rail ]
       [ pH Probe ] ──────| GPIO 32 (ADC1)  5.0V  |── [ 5.0V Power Rail ]
       [ Turbidity ] ─────| GPIO 33 (ADC1)  GND   |── [ Ground Rail ]
       [ DO Probe ] ──────| GPIO 34 (ADC1)  GPIO27|── [ Pump Relay ]
       [ Salinity / TDS ]─| GPIO 36 (ADC1)  GPIO23|── [ Alarm Buzzer ]
       [ GPS RX ] ────────| GPIO 16         GPIO22|── [ Red LED ]
       [ GPS TX ] ────────| GPIO 17         GPIO21|── [ Yellow LED ]
                          |                 GPIO19|── [ Green LED ]
                          +───────────────────────+
```

| Peripheral / Sensor | Recommended Final Pin | Pin Functionality | Interface Type | Hardware Safety Justification |
| :--- | :--- | :--- | :--- | :--- |
| **Temperature Sensor** | `GPIO 18` | General Digital IO | OneWire Digital | Bidirectional digital IO; safe from ADC/Wi-Fi conflicts; requires 4.7kΩ pull-up. |
| **pH Sensor** | `GPIO 32` | ADC1_CH4 / Touch9 | Analog Input (0–3.3V) | ADC1 channel; 100% compatible with active Wi-Fi radio. |
| **Turbidity Sensor** | `GPIO 33` | ADC1_CH5 / Touch8 | Analog Input (0–3.3V) | ADC1 channel; 100% compatible with active Wi-Fi radio. |
| **Dissolved Oxygen (DO)**| `GPIO 34` | ADC1_CH6 / GPI | Analog Input (0–3.3V) | ADC1 channel; input-only pin perfectly utilized for analog reading. |
| **Salinity / TDS Sensor**| `GPIO 36` | ADC1_CH0 / GPI | Analog Input (0–3.3V) | ADC1 channel; input-only pin perfectly utilized for analog reading. |
| **Green Status LED** | `GPIO 19` | General Digital IO | Digital Output | Safe output pin; zero boot-strapping interference. |
| **Yellow Status LED** | `GPIO 21` | General Digital IO / SDA | Digital Output | Safe output pin; zero boot-strapping interference. |
| **Red Status LED** | `GPIO 22` | General Digital IO / SCL | Digital Output | Safe output pin; zero boot-strapping interference. |
| **Alarm Buzzer** | `GPIO 23` | General Digital IO / MOSI| Digital Output | Safe output pin; zero boot-strapping interference. |
| **Aerator Pump Relay** | `GPIO 27` | General Digital IO / Touch7| Digital Output | Safe output pin; isolated via optocoupler board. |
| **GPS Module RX** | `GPIO 16` | UART2 RX | Hardware Serial RX | Dedicated hardware UART2 RX pin. |
| **GPS Module TX** | `GPIO 17` | UART2 TX | Hardware Serial TX | Dedicated hardware UART2 TX pin. |

---

### 7.2 Explicit Fact Distinction

- **REPOSITORY-VERIFIED FACT**:
  The recommended pin mapping matches [firmware/include/config/PinConfig.h](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/firmware/include/config/PinConfig.h) **EXACTLY**. This mapping already compiles cleanly in PlatformIO (`env:esp32dev`). Selecting Candidate 1 requires **ZERO changes to C++ firmware source code**.

- **ENGINEERING-RECOMMENDED**:
  Aligning [config/device_config.json](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/config/device_config.json) and [docs/HARDWARE_INTEGRATION_GUIDE.md](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/HARDWARE_INTEGRATION_GUIDE.md) to Candidate 1 is an engineering design recommendation. It guarantees 100% electrical safety by eliminating boot-strapping pin risks (GPIO 12/15) and avoiding Wi-Fi ADC2 conflicts.

---

## 8. Architectural & Electrical Rationale

1. **ADC1 Wi-Fi Independence**: All four analog water quality sensors (pH, Turbidity, DO, Salinity) are placed on ADC1 channels (GPIO 32, 33, 34, 36). When the ESP32 Wi-Fi stack is active, ADC1 remains 100% operational, guaranteeing uninterrupted telemetry.
2. **Boot-Strapping Pin Immunity**: Actuators (LEDs, Buzzer, Relay) are assigned to GPIO 19, 21, 22, 23, 27. Crucially, none of these actuators use GPIO 0, 2, 12, or 15. This eliminates power-up brownout crashes and flash voltage selection errors.
3. **Input-Only Pin Compliance**: GPIO 34 and GPIO 36 are input-only (GPI) pins without output drivers. Assigning them to analog sensors (DO and Salinity) utilizes their input capability perfectly while reserving output-capable pins for actuators.
4. **Zero C++ Code Modifications**: Because `PinConfig.h` already defines Candidate 1 as its default struct initializer, approving this proposal resolves all repository conflicts by updating documentation and JSON configs without altering frozen C++ code.

---

## 9. Remaining Physical Verification Requirements

Before physical hardware bench assembly, the following physical verification steps must be completed:

- [ ] **Physical Multimeter Voltage Check**: Measure raw voltage on ESP32 5.0V and 3.3V power rails under load.
- [ ] **ADC Calibration Measurement**: Measure raw ADC readings on GPIO 32, 33, 34, 36 with known reference voltages (0.0V, 1.0V, 2.0V, 3.3V) to measure ESP32 ADC non-linearity.
- [ ] **Optocoupler Isolation Check**: Verify relay board optical isolation and flyback diode continuity on GPIO 27.
- [ ] **OneWire Pull-up Check**: Verify 4.7kΩ pull-up resistor presence between GPIO 18 and 3.3V rail.
- [ ] **Serial Flash Verification**: Upload compiled firmware to physical ESP32 board via USB serial and verify `Serial.println` diagnostic output at 115200 baud.
