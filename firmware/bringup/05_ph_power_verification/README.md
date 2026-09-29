# Stage 05: pH Sensor Module Power-Stage Verification

**Subsystem:** Analog pH Sensor Module (PH-4502C / SEN0161 conditioning board + glass probe)  
**MCU:** NodeMCU ESP-32S (38-pin Dev Module) on CP2102 (`COM3`)  
**Status:** Isolated Hardware Bring-Up Stage 05 — Power Isolation Stage  

---

## 1. Physical Wiring Setup

| Module Pin | Wire / Connection Target | Electrical Potential | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **BNC** | Glass pH Probe | High-impedance mV | **CONNECTED** | Attached to module BNC socket |
| **V+** | **ESP32 5V / VIN** | +5.0V DC (Nominal) | **CONNECTED** | Main module supply from USB rail |
| **G** | **ESP32 GND** | 0V (Common Ground) | **CONNECTED** | Primary ground reference |
| **Po** | *(Open / Floating)* | 0.0V - 4.1V Analog | **DISCONNECTED** | **DO NOT CONNECT TO ESP32 GPIO** |
| **To** | *(Open / Disconnected)*| Temperature out | **DISCONNECTED** | Unused analog temperature pin |
| **Do** | *(Open / Disconnected)*| Digital trigger | **DISCONNECTED** | Unused digital threshold pin |
| **G (2nd)**| *(Open / Disconnected)*| 0V | **DISCONNECTED** | Secondary ground pin |

---

## 2. Power-Stage Safety & Electrical Assessment

### Can the module be safely powered from the current connection?
**YES.**  
- The ESP32 `5V / VIN` pin is tied directly to the incoming USB 5V rail (via a forward-biased Schottky diode on the NodeMCU board).
- The pH sensor module (PH-4502C) requires a nominal 5.0V DC supply and draws a quiescent current of approximately **10 mA to 20 mA**.
- Standard USB 2.0 provides up to 500 mA, which effortlessly satisfies both the ESP32 (~80-160 mA) and the pH module without voltage droop.

### Can the ESP32 electrically measure the module's V+ voltage in firmware?
**NO.**  
- The NodeMCU ESP-32S development board has **no internal routing or voltage divider** connecting the external 5V/VIN pin to an internal ADC channel.
- The ESP32 microcontroller only exposes internal ADC channels (ADC1 and ADC2) to external GPIO pins.
- **Therefore, the ESP32 firmware cannot directly or electrically measure the V+ rail voltage without additional external measurement hardware (such as a digital multimeter or an external resistor divider).**
- In accordance with rigorous engineering standards, this firmware explicitly reports this architectural boundary rather than fabricating an artificial or simulated measurement.

---

## 3. Bench Verification Checklist

1. **Visual Indicator (Onboard LED):**
   - Locate the power LED on the pH conditioning board (typically labeled `PWR` or `LED1`).
   - When the ESP32 is plugged in via USB and V+/GND are connected, this LED should glow steadily red.
2. **Manual Multimeter Check (Optional / Recommended):**
   - Set Digital Multimeter (DMM) to DC Volts.
   - Probe between module `V+` and module `G`: Expected reading **4.75V – 5.10V DC**.
   - Probe between module `Po` and module `G` while probe is resting: Observe open-circuit output voltage (typically ~1.5V – 3.0V depending on trimmer adjustment).
   - Verify that `Po` voltage does not exceed 3.3V prior to any future integration.
3. **Firmware Diagnostic Heartbeat:**
   - Compile and upload the Stage 05 firmware to verify ESP32 system stability while the module is powered on the 5V bus.

---

## 4. PlatformIO Commands

### A. Compile Firmware (Without Uploading)
```bash
pio run -d "firmware/bringup/05_ph_power_verification"
```

### B. Flash to ESP32 (COM3)
```bash
pio run -d "firmware/bringup/05_ph_power_verification" -t upload --upload-port COM3
```

### C. Open Serial Monitor (115200 Baud)
```bash
pio device monitor -d "firmware/bringup/05_ph_power_verification" -p COM3 -b 115200
```

---

## 5. Stage 05 Acceptance Criteria

- [x] pH module V+ connected to ESP32 5V/VIN.
- [x] pH module G connected to ESP32 GND.
- [x] pH module Po is strictly **DISCONNECTED** from ESP32 GPIO.
- [x] Zero ESP32 ADC pins initialized or read.
- [x] Production firmware files (`firmware/src/main.cpp`, `firmware/platformio.ini`) remain 100% untouched.
- [x] No claim is made that the pH sensor is verified.
