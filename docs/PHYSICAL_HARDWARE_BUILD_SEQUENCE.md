# STAGED HARDWARE BUILD SEQUENCE & VALIDATION PLAN

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Milestone:** Physical Hardware Design Phase — Staged Integration & Testing Protocol  
**Document Version:** 1.0.0 (August 18, 2026)  
**Status:** Software Verified / Protocol Defined / Physical Execution Pending  

---

## 1. 13-Stage Hardware Integration Sequence

> [!CAUTION]
> **SAFETY STAGING RULE**  
> NEVER connect all sensors, relays, and microcontrollers simultaneously on the initial power-up. Follow the 13-stage verification procedure sequentially, validating power rail voltages and logic levels at every step before introducing new hardware modules.

```
Stage 1: Power Rails ──► Stage 2: Main ESP32 ──► Stage 3: Temp Sensor ──► Stage 4: Analog Probes (1-by-1)
                                                                                  │
Stage 8: Relay (No Load) ◄── Stage 7: Buzzer ◄── Stage 6: LEDs ◄── Stage 5: GPS ◄─┘
         │
         ▼
Stage 9: ESP32-CAM ──► Stage 10: MQTT Network ──► Stage 11: Gateway ──► Stage 12: Pump Load ──► Stage 13: Full System Test
```

### Stage 1: Power System Verification
- **Procedure**: Connect 12V DC adapter to LM2596 buck converter. Adjust trimmer potentiometer until 5.0V DC is output.
- **Verification**: Measure 5.0V $\pm$ 0.1V on multimeter before connecting microcontrollers.

### Stage 2: ESP32-WROOM Main MCU Power & Flash
- **Procedure**: Mount ESP32-WROOM module on breadboard. Connect 5V output to VIN / 5V pin. Connect Micro-USB.
- **Verification**: Verify power LED turns ON and serial monitor outputs bootloader logs at 115200 baud.

### Stage 3: DS18B20 Temperature Sensor Integration
- **Procedure**: Wire DS18B20 VCC to 3.3V, GND to GND, and DQ to GPIO 18 with 4.7 kΩ pull-up resistor.
- **Verification**: Flash temperature diagnostic sketch; verify ambient temperature readings (~20°C - 25°C).

### Stage 4: Analog Sensor Probes (One-by-One Assembly)
- **Procedure**: Wire pH (GPIO 32), Turbidity (GPIO 33), DO (GPIO 34), and Salinity (GPIO 36) modules sequentially.
- **Voltage Safety Check**: Measure analog output voltage at ESP32 GPIO pins with multimeter. Ensure voltage never exceeds **3.0V DC**. Adjust voltage dividers if necessary.

### Stage 5: GPS UART Module Integration
- **Procedure**: Wire NEO-6M VCC (5V), GND, TX to GPIO 16 (RX), RX to GPIO 17 (TX).
- **Verification**: Verify GPS PPS LED blinks upon satellite lock and NMEA sentences stream over UART2.

### Stage 6: Indicator LEDs Integration
- **Procedure**: Connect Green LED (GPIO 19), Yellow LED (GPIO 21), Red LED (GPIO 22) through 220 Ω resistors.
- **Verification**: Flash GPIO test sketch; confirm LEDs toggle ON/OFF sequentially.

### Stage 7: Audio Alarm Buzzer Integration
- **Procedure**: Connect 2N2222 transistor base to GPIO 23 (1kΩ resistor), collector to Buzzer (-), emitter to GND.
- **Verification**: Trigger GPIO 23 HIGH; confirm audio tone sounds.

### Stage 8: 5V Relay Module Integration (Unloaded)
- **Procedure**: Connect Relay VCC (5V), GND, and IN1 to GPIO 27. **Do NOT connect the 12V aerator pump yet**.
- **Verification**: Toggle GPIO 27; hear relay click and verify LED on relay module illuminates.

### Stage 9: ESP32-CAM Board Flashing & Power Check
- **Procedure**: Connect FTDI programmer (3.3V/5V) to ESP32-CAM. Jumper GPIO 0 to GND. Flash firmware. Remove jumper.
- **Verification**: Verify camera initializes OV2640 sensor and acquires 224x224 test frame.

### Stage 10: Local Wi-Fi & MQTT Connectivity
- **Procedure**: Boot main ESP32 and ESP32-CAM on Wi-Fi network. Monitor MQTT broker topic subscriptions.
- **Verification**: Confirm telemetry published on `aquatic/+/telemetry` and raw camera frames on `aquatic/+/camera/raw`.

### Stage 11: Gateway Multimodal Integration
- **Procedure**: Start Gateway host runtime (`temporal_validator.py`, PyTorch MobileNetV3 model, `FusionEngine`).
- **Verification**: Gateway ingests multimodal evidence, performs inference, and publishes decisions to `aquatic/+/decision`.

### Stage 12: 12V Aerator Pump Load Wiring
- **Procedure**: Wire 12V DC pump motor across Relay NO contacts. Install 1N4007 flyback diode across pump terminals.
- **Verification**: Trigger CRITICAL alert state; verify relay energizes and 12V aerator pump runs smoothly.

### Stage 13: Full System End-to-End Stress Test
- **Procedure**: Execute complete aquatic monitoring cycle under simulated normal, turbidity, and bloom fault states.
- **Verification**: Validate complete sensor telemetry $\rightarrow$ camera acquisition $\rightarrow$ multimodal fusion $\rightarrow$ FSM actuation pipeline.

---

## 2. Comprehensive Hardware Validation Protocol

| Validation Test Case | Test Description | Target Specification | Validation Type | Execution Status |
| :--- | :--- | :--- | :--- | :--- |
| **V-01: Power Rail Voltage** | Multimeter measurement of 5V and 3.3V rails | 5.0V $\pm$ 0.1V, 3.3V $\pm$ 0.05V | `PHYSICAL HARDWARE TEST` | **PENDING** |
| **V-02: Sensor Pin Voltage Safety**| Multimeter check of analog sensor outputs | Max voltage $\le$ 3.0V DC | `PHYSICAL HARDWARE TEST` | **PENDING** |
| **V-03: DS18B20 Temp Readings** | Compare reading against reference thermometer | Accuracy $\pm$ 0.5°C | `PHYSICAL HARDWARE TEST` | **PENDING** |
| **V-04: pH Probe Calibration** | 2-Point buffer calibration (pH 4.01 & 7.00) | Linear fit $R^2 > 0.98$ | `PHYSICAL HARDWARE TEST` | **PENDING** |
| **V-05: Turbidity Calibration** | Zero NTU distilled water vs turbid sample | Voltage delta $> 1.0\text{V}$ | `PHYSICAL HARDWARE TEST` | **PENDING** |
| **V-06: DO Sensor Calibration** | Zero DO solution vs air-saturated water | Linear span calibration | `PHYSICAL HARDWARE TEST` | **PENDING** |
| **V-07: TDS Sensor Calibration** | 1413 µS/cm conductivity standard solution | Span calibration $\pm 5\%$ | `PHYSICAL HARDWARE TEST` | **PENDING** |
| **V-08: GPS Satellite Lock** | NMEA sentence parsing & fix acquisition | Latitude / Longitude fix | `PHYSICAL HARDWARE TEST` | **PENDING** |
| **V-09: ESP32-CAM Capture** | 224x224 JPEG acquisition & Base64 encode | Frame size 10-25 KB | `PHYSICAL HARDWARE TEST` | **PENDING** |
| **V-10: MQTT Transport Rate** | Frame delivery at 0.1 FPS over Wi-Fi | Latency $< 200\text{ ms}$ | `PHYSICAL HARDWARE TEST` | **PENDING** |
| **V-11: SNTP Time Sync** | Wall-clock ISO timestamp acquisition | `time_sync_status == SYNCED` | `PHYSICAL HARDWARE TEST` | **PENDING** |
| **V-12: PyTorch Inference** | MobileNetV3 inference execution on Gateway | Latency $< 15\text{ ms}$ | `SOFTWARE TEST` | 🟢 **PASSED** |
| **V-13: Multimodal Fusion** | Sensor + Visual fusion evaluation | Correct threat state | `SOFTWARE TEST` | 🟢 **PASSED** |
| **V-14: Temporal Safety** | Unsynced clock / stale frame fallback | Fallback to `CAMERA_FAULT` | `SOFTWARE TEST` | 🟢 **PASSED** |
| **V-15: Relay Safety Interlock** | Spurious comms drop safety check | Relay stays OFF | `SOFTWARE TEST` | 🟢 **PASSED** |
