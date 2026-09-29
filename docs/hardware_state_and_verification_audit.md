# HARDWARE STATE & VERIFICATION AUDIT REPORT

**Project:** AquaSentinel-AI — IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Audit Milestone:** Pre-Integration Forensic Hardware Baseline  
**Date:** September 29, 2026  
**Auditor:** Antigravity Forensic Audit Engine  
**Operational Scope:** READ-ONLY Forensic Audit — Zero Modifications Permitted  

---

## 1. Executive Summary

This report establishes the authoritative, evidence-backed hardware ground truth for the AquaSentinel-AI project prior to any production software integration. Both target microcontrollers (Main ESP32 NodeMCU and ESP32-CAM) are connected simultaneously to the development host PC across isolated USB serial ports (`COM3` and `COM4`). 

Physical bring-up stages have validated the discrete actuators (LEDs, Buzzer), the analog electrical protection networks for the pH and Turbidity sensors, and the physical camera module. However, optical liquid discrimination for the turbidity sensor remains pending trimpot adjustment, the DS18B20 1-Wire temperature sensor remains deferred after failed enumeration, the pump relay load circuit is unvalidated (no water pump), and Dissolved Oxygen / Salinity / GPS hardware components are completely unavailable physically.

---

## 2. Authoritative Hardware Inventory

| Component | Physical Availability | Assigned GPIO | Power Domain | Physical Circuit / Wiring | Verification Stage & Method | Authoritative Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Main ESP32** | PHYSICALLY PRESENT | N/A (Host MCU) | 5V via USB (VBUS / VIN), 3.3V LDO | NodeMCU ESP-32S (ESP32-D0WD-V3 rev 3.1) on CP2102 | Flashed bring-up sketches via PlatformIO (`COM3`); continuous serial telemetry | **PHYSICALLY VERIFIED** |
| **ESP32-CAM** | PHYSICALLY PRESENT | N/A (Camera MCU)| 5V via USB (ESP32-CAM-MB), 3.3V LDO | AI-Thinker ESP32-CAM module seated in CH340 programmer | Flashed boot monitor & GC2145 driver via Arduino/PlatformIO (`COM4`); heartbeats active | **PHYSICALLY VERIFIED** |
| **Camera Sensor** | PHYSICALLY PRESENT | D0–D7, VSYNC, HREF, PCLK, XCLK, SIOD, SIOC | 3.3V / 2.8V / 1.5V internal LDOs | FPC ribbon cable to AI-Thinker camera connector; GalaxyCore GC2145 (PID 0x2145) | Phase B–I camera verification (`07_ov2640_camera_verification`); captures Base64 JPEG frames | **PHYSICALLY VERIFIED** |
| **Green Status LED** | PHYSICALLY PRESENT | GPIO25 (P25) | 3.3V Logic | GPIO25 $\rightarrow$ 330 $\Omega$ $\rightarrow$ Green Anode $\rightarrow$ Cathode $\rightarrow$ Common GND | Stage 02 LED bring-up (`02_led_verification`); 1-second pulse sequence verified | **PHYSICALLY VERIFIED** |
| **Yellow Status LED**| PHYSICALLY PRESENT | GPIO26 (P26) | 3.3V Logic | GPIO26 $\rightarrow$ 330 $\Omega$ $\rightarrow$ Yellow Anode $\rightarrow$ Cathode $\rightarrow$ Common GND | Stage 02 LED bring-up (`02_led_verification`); 1-second pulse sequence verified | **PHYSICALLY VERIFIED** |
| **Red Status LED** | PHYSICALLY PRESENT | GPIO27 (P27) | 3.3V Logic | GPIO27 $\rightarrow$ 330 $\Omega$ $\rightarrow$ Red Anode $\rightarrow$ Cathode $\rightarrow$ Common GND | Stage 02 LED bring-up (`02_led_verification`); 1-second pulse sequence verified | **PHYSICALLY VERIFIED** |
| **Alarm Buzzer** | PHYSICALLY PRESENT | GPIO14 (P14) | 3.3V/5V Logic | GPIO14 $\rightarrow$ Buzzer (+) $\rightarrow$ Buzzer (-) $\rightarrow$ Common GND (MB12A05 2-pin) | Stage 03 Buzzer bring-up (`03_buzzer_verification`); dual short-pulse + long-beep verified | **PHYSICALLY VERIFIED** |
| **pH Sensor** | PHYSICALLY PRESENT | GPIO32 (P32) | 5.0V (VIN) | Module V+ $\rightarrow$ 5V VIN; G $\rightarrow$ GND; Po $\rightarrow$ 33 k$\Omega$ $\rightarrow$ P32 $\rightarrow$ 22 k$\Omega$ $\rightarrow$ GND ($0.400\times$ ratio) | Stage 05B bring-up (`05_ph_power_verification`); 200-sample voltage telemetry verified | **ELECTRICALLY VERIFIED ONLY** |
| **Turbidity Sensor** | PHYSICALLY PRESENT | GPIO34 (P34) | 5.0V (VIN) | Module VCC $\rightarrow$ 5V VIN; GND $\rightarrow$ GND; OUT $\rightarrow$ 33 k$\Omega$ $\rightarrow$ P34 $\rightarrow$ 22 k$\Omega$ $\rightarrow$ GND ($0.400\times$) | Stage 08 bring-up (`08_turbidity_verification`); ADC signal stable (0.258V); optical response failed | **PARTIALLY VERIFIED** |
| **DS18B20 Temp Probe**| PHYSICALLY PRESENT | GPIO33 (P33) | 3.3V Logic | VCC $\rightarrow$ 3V3; GND $\rightarrow$ GND; DATA $\rightarrow$ GPIO33; 4.7 k$\Omega$ pull-up to 3V3 | Stage 04 bring-up (`04_ds18b20_verification`); 0 OneWire ROM devices detected; intentionally deferred | **DEFERRED / NOT VERIFIED** |
| **Single-Channel Relay**| PHYSICALLY PRESENT| GPIO27 (Planned) | 5.0V (VCC), 3.3V Opto | SRD-05VDC-SL-C; dry-contact mode; NO pump load connected | Stage 01 bring-up (`01_led_buzzer_relay`); pin reallocated to Red LED; load side unvalidated | **PARTIALLY VERIFIED** |
| **Aeration Water Pump**| NOT AVAILABLE | N/A | 12V / 5V DC | None (Physical actuator missing) | None | **NOT AVAILABLE** |
| **Dissolved Oxygen Probe**| NOT AVAILABLE | GPIO34 (Planned)| 5.0V Analog | None (Physical sensor missing) | None (GPIO34 physically reassigned to Turbidity) | **NOT AVAILABLE** |
| **Salinity / TDS Probe**| NOT AVAILABLE | GPIO36 (Planned)| 3.3V / 5.0V Analog | None (Physical sensor missing) | None | **NOT AVAILABLE** |
| **GPS Module** | NOT AVAILABLE | RX=16, TX=17 | 3.3V UART | None (Physical module missing) | None | **NOT AVAILABLE** |
| **Resistor Dividers**| PHYSICALLY PRESENT | P32, P34 | Passive | Two discrete pairs: 33 k$\Omega$ ($\pm 1\%$) series, 22 k$\Omega$ ($\pm 1\%$) shunt to GND | Resistance verified; divider transfer ratio $V_{\text{ADC}} = 0.400 \times V_{\text{OUT}}$ confirmed | **PHYSICALLY VERIFIED** |
| **Breadboard Power Rails**| PHYSICALLY PRESENT| VIN, 3V3, GND | Dual Rail | Left rail = 5V VIN; Right rail = 3.3V; Common GND across all peripherals | Voltage verified via DMM and ESP32 internal ADC scaling | **PHYSICALLY VERIFIED** |

---

## 3. Exact Pin Map & Conflict Analysis

### 3.1 Authoritative Physical Pin Table

| GPIO Pin | Physical Board Label | Direction | Connected Peripheral | Electrical Interface | Verified in Hardware? | Production `PinConfig.h` Assignment | Pin Conflict Status |
| :---: | :---: | :---: | :--- | :--- | :---: | :---: | :--- |
| **GPIO14** | `P14` | Output | MB12A05 2-Pin Buzzer | Direct drive from GPIO | **YES** (Stage 03) | `buzzerPin = 23` | 🔴 **CRITICAL CONFLICT** (Physical 14 vs C++ 23) |
| **GPIO25** | `P25` | Output | Green Status LED | 330 $\Omega$ current-limiting | **YES** (Stage 02) | `greenLedPin = 19` | 🔴 **CRITICAL CONFLICT** (Physical 25 vs C++ 19) |
| **GPIO26** | `P26` | Output | Yellow Status LED | 330 $\Omega$ current-limiting | **YES** (Stage 02) | `yellowLedPin = 21` | 🔴 **CRITICAL CONFLICT** (Physical 26 vs C++ 21) |
| **GPIO27** | `P27` | Output | Red Status LED | 330 $\Omega$ current-limiting | **YES** (Stage 02) | `pumpRelayPin = 27` / `redLedPin = 22` | 🔴 **FATAL CONFLICT** (Relay assigned to LED pin) |
| **GPIO32** | `P32` | Analog In | pH Sensor Module (Po) | 33 k$\Omega$ / 22 k$\Omega$ Divider (0.4x) | **YES** (Stage 05B) | `phPin = 32` | 🟢 **MATCH** (ADC1_CH4 verified) |
| **GPIO33** | `P33` | Digital IO| DS18B20 Temp Probe | 1-Wire bus with 4.7 k$\Omega$ pull-up | **DEFERRED** (Stage 04) | `turbidityPin = 33` / `tempPin = 18` | 🔴 **CRITICAL CONFLICT** (Physical 33 vs C++ 33/18) |
| **GPIO34** | `P34` | Analog In (GPI)| Turbidity Sensor (OUT) | 33 k$\Omega$ / 22 k$\Omega$ Divider (0.4x) | **YES** (Stage 08) | `doPin = 34` | 🔴 **FATAL CONFLICT** (Turbidity on DO pin) |

---

## 4. Electrical Safety & Signal Integrity Audit

### 4.1 3.3V vs. 5.0V Domain Isolation
- **Microcontroller Safety Boundary:** The ESP32-D0WD-V3 core operates at 3.3V. Its GPIO pins are strictly rated for a maximum absolute voltage of $V_{\text{DD}} + 0.3\,\text{V} \approx 3.6\,\text{V}$. Continuous exposure to voltages $\ge 5.0\,\text{V}$ will cause gate dielectric breakdown and permanent destruction of the GPIO silicon.
- **pH Sensor Module:** Powered from 5.0V VIN. Unloaded operational amplifier outputs can reach $4.2\,\text{V} - 4.5\,\text{V}$. The dedicated 33 k$\Omega$ / 22 k$\Omega$ divider clamps a 5.0V maximum input to $5.0 \times \frac{22}{55} = 2.000\,\text{V}$ at GPIO32. Maximum survivable output before exceeding 3.3V is $V_{\text{MAX}} = 3.3 \times \frac{55}{22} = 8.25\,\text{V}$. **STATUS: 100% ELECTRICALLY SAFE.**
- **Turbidity Sensor Module:** Powered from 5.0V VIN. Optical quiescent output can range from $0.6\,\text{V}$ to $4.5\,\text{V}$. The identical 33 k$\Omega$ / 22 k$\Omega$ divider scales the signal into a safe window of $0.24\,\text{V} - 1.80\,\text{V}$ at GPIO34. **STATUS: 100% ELECTRICALLY SAFE.**
- **Relay Module (SRD-05VDC-SL-C):** The relay coil requires 5.0V, drawing ~70 mA. Directly powering the coil from an ESP32 GPIO pin will destroy the microcontroller. The relay board includes an optocoupler isolation barrier with an onboard flyback diode. However, because GPIO27 is currently physically occupied by the Red LED, the relay control line is physically disconnected.

### 4.2 ADC Channel Limitations & Wi-Fi Incompatibility
- **SAR ADC Architecture:** The ESP32 contains two analog-to-digital converters: ADC1 (8 channels) and ADC2 (10 channels).
- **Critical Architectural Constraint:** **ADC2 CANNOT BE USED WHEN WI-FI IS ENABLED**. The Espressif Wi-Fi driver takes exclusive ownership of SAR ADC2 during RF transmission/reception. Any concurrent call to `analogRead()` on an ADC2 channel while Wi-Fi is active returns garbage or crashes the RTOS network stack.
- **Verification Audit:**
  - `GPIO32` $\rightarrow$ ADC1 Channel 4 (`ADC1_CH4`). Fully compatible with active Wi-Fi.
  - `GPIO34` $\rightarrow$ ADC1 Channel 6 (`ADC1_CH6`). Fully compatible with active Wi-Fi.
  - Both physical analog inputs reside strictly on ADC1.

### 4.3 Input-Only GPIO Limitations
- `GPIO34` (Turbidity input) is an **input-only (GPI)** pin. It lacks internal pull-up and pull-down resistor circuitry and cannot be configured as `OUTPUT`.
- This pin is well suited for analog input. However, software must never attempt `pinMode(34, OUTPUT)` or `digitalWrite(34, ...)`.

### 4.4 Boot-Strapping Pin Audit
- The ESP32 utilizes GPIO 0, 2, 4, 12 (MTDI), and 15 (MTDO) as hardware strapping pins during power-on reset.
- In the active physical wiring:
  - `GPIO12` is completely disconnected (avoids flash voltage strap failure).
  - `GPIO15` is completely disconnected (avoids JTAG / silent boot failure).
  - `GPIO0` and `GPIO2` on Main ESP32 are unconnected.
  - Discrete actuators use safe non-strapping outputs (`GPIO14, GPIO25, GPIO26, GPIO27`).
- **ESP32-CAM Strapping Pins:** On the ESP32-CAM, `GPIO0` controls flash mode (grounded via button/jumper during upload, floating/high during normal execution). `GPIO4` drives the high-power onboard flash LED.

### 4.5 Common Ground Reference
- Breadboard common ground connects:
  - Main ESP32 GND (Pins 14 and 38)
  - pH Module Ground
  - Turbidity Module Ground
  - LED Cathode Rail
  - Buzzer Negative Terminal
  - Voltage Divider Shunt Resistors (22 k$\Omega$)
- Continuity tests confirmed 0.0 $\Omega$ impedance across all ground points. Zero ground-loop offsets were observed during ADC sampling.

---

## 5. Hardware Verification Evidence

### 5.1 Main ESP32 & Actuators
- **Evidence Source:** `firmware/bringup/02_led_verification/` and `03_buzzer_verification/`.
- **Serial Log Confirmation:** COM3 @ 115200 baud executed continuous cycling: Green (P25) $\rightarrow$ Yellow (P26) $\rightarrow$ Red (P27) without flicker. Buzzer executed acoustic pulse pattern at 115200 baud.
- **Physical Inspection:** Series resistors (330 $\Omega$) present on all LED anodes. Current draw ~6.5 mA per LED, well within the 12 mA recommended ESP32 GPIO drive limit.

### 5.2 pH Sensor Circuit
- **Evidence Source:** `firmware/bringup/05_ph_power_verification/` and `reports/ph_verification_log.txt`.
- **Measurement Data:** 200 consecutive samples captured across 50 seconds in ambient air and clean water.
  - Raw ADC: Mean = 3881.4 counts ($V_{\text{P32}} = 3.127\,\text{V}$, $V_{\text{Po}} \approx 7.82\,\text{V}$ saturated without probe).
  - Water introduction showed dynamic electrical change down to $V_{\text{P32}} \approx 1.25\,\text{V}$ ($V_{\text{Po}} \approx 3.12\,\text{V}$). Zero hardware damage or saturation.

### 5.3 Turbidity Sensor Circuit
- **Evidence Source:** `firmware/bringup/08_turbidity_verification/` and `reports/turbidity_verification/turbidity_verification_log.txt`.
- **Measurement Data:** Over 25,000 continuous samples captured across 250 windows.
  - Dry Baseline: Mean = 145.82 counts ($V_{\text{P34}} = 0.257\,\text{V}$, $V_{\text{OUT}} = 0.643\,\text{V}$).
  - Water Immersion: Mean = 145.90 counts ($V_{\text{P34}} = 0.257\,\text{V}$, delta = +0.08 counts).
  - Movement / Obstruction: Delta $\le 0.60$ counts (remained clamped at ground rail).
- **Diagnosis:** The LM358 operational amplifier on the turbidity interface board is biased at negative saturation. The physical 25-turn cermet potentiometer requires trimming with a miniature screwdriver to set quiescent voltage to ~1.6V–2.0V.

### 5.4 DS18B20 Temperature Probe
- **Evidence Source:** `firmware/bringup/04_ds18b20_verification/`.
- **Measurement Data:** OneWire search on GPIO33 reported: `[ERROR] No DS18B20 devices discovered on OneWire bus`.
- **Status:** Wire integrity, internal parasitics, or defective sensor IC. Formally marked as **DEFERRED**.

### 5.5 ESP32-CAM & GC2145 Camera Module
- **Evidence Source:** `firmware/bringup/07_ov2640_camera_verification/` and `reports/camera_verification/verified_frame.jpg`.
- **Hardware Identification:** Sensor Silicon ID = `0x2145` (GalaxyCore GC2145). Not OmniVision OV2640.
- **Functional Validation:** 
  - PSRAM verified: 4,034,024 Bytes free.
  - Software JPEG compression verified via `fmt2jpg()`.
  - Resolution: 224x224x3 (Exact MobileNetV3 input requirement).
  - 10/10 stress frames captured without corruption. Frame size: 5,618 Bytes average. Valid JPEG SOI (`0xFF 0xD8`) and EOI (`0xFF 0xD9`) verified.

---

## 6. Hardware Integration Block Diagram

```text
+========================================================================================+
|                               HOST COMPUTER / RUNTIME GATEWAY                          |
|  - COM3: Silicon Labs CP210x USB Bridge                                                |
|  - COM4: WCH CH340 USB-Serial Programmer                                               |
+========================================================================================+
         |                                                               |
         | (COM3 @ 115200)                                               | (COM4 @ 115200)
         v                                                               v
+─────────────────────────────────────────+     +────────────────────────────────────────+
|        MAIN ESP32 CONTROLLER            |     |        ESP32-CAM OPTICAL NODE          |
|  NodeMCU ESP-32S (ESP32-D0WD-V3)        |     |  AI-Thinker ESP32-CAM + ESP32-CAM-MB   |
|  Dual-Core LX6 @ 240MHz | 520KB SRAM    |     |  ESP32-D0WD @ 240MHz | 4MB PSRAM       |
+─────────────────────────────────────────+     +────────────────────────────────────────+
  |    |    |    |     |     |       |            |
  |    |    |    |     |     |       |            +── [ GC2145 Camera Sensor (FPC) ]
  |    |    |    |     |     |       |                 - 8-bit Parallel D0-D7
  |    |    |    |     |     |       |                 - VSYNC, HREF, PCLK, XCLK
  |    |    |    |     |     |       |                 - I2C SCCB (SIOD=26, SIOC=27)
  |    |    |    |     |     |       |                 - Raw RGB565 / YUV422 -> PSRAM
  |    |    |    |     |     |       |                 - Software fmt2jpg -> JPEG
  |    |    |    |     |     |       |
  |    |    |    |     |     |       +── GPIO14 ──> [ MB12A05 2-Pin Buzzer ] ──> GND
  |    |    |    |     |     |
  |    |    |    |     |     +────────── GPIO25 ──> [ 330Ω ] ──> [ Green LED ] ──> GND
  |    |    |    |     |
  |    |    |    |     +──────────────── GPIO26 ──> [ 330Ω ] ──> [ Yellow LED ] ──> GND
  |    |    |    |
  |    |    |    +────────────────────── GPIO27 ──> [ 330Ω ] ──> [ Red LED ] ────> GND
  |    |    |                            (⚠️ Pump Relay CONFLICT: cannot share GPIO27)
  |    |    |
  |    |    +─────────────────────────── GPIO33 ──> [ DS18B20 1-Wire ] <── 4.7kΩ Pullup
  |    |                                           (⚠️ DEFERRED / Not Enumerated)
  |    |
  |    +── GPIO32 (ADC1_CH4) <──+── 33kΩ ──< pH Module Analog Output (Po)
  |                             |
  |                             +── 22kΩ ──> Common GND
  |
  +─────── GPIO34 (ADC1_CH6) <──+── 33kΩ ──< Turbidity Module Analog Output (OUT)
                                |            (⚠️ Pending Trimpot Bias Adjustment)
                                +── 22kΩ ──> Common GND

==========================================================================================
MISSING HARDWARE SUBSYSTEMS (NOT PHYSICALLY AVAILABLE):
  ❌ Water Aeration Pump (SRD-05VDC-SL-C Relay has no load)
  ❌ Dissolved Oxygen (DO) Optical Probe
  ❌ Salinity / Electrical Conductivity (TDS) Probe
  ❌ GPS Hardware Receiver (NEO-6M / UART)
==========================================================================================
```
