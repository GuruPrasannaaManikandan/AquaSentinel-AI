# HARDWARE ↔ SOFTWARE CROSS-AUDIT REPORT

**Project:** AquaSentinel-AI — IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Audit Milestone:** Pre-Integration Forensic Cross-Consistency Matrix  
**Date:** September 29, 2026  
**Auditor:** Antigravity Forensic Audit Engine  
**Operational Scope:** READ-ONLY Forensic Audit — Zero Modifications Permitted  

---

## 1. Executive Summary

This cross-audit cross-references the findings of the **Hardware State & Verification Audit** (`docs/hardware_state_and_verification_audit.md`) against the **Software Architecture & Integration Readiness Audit** (`docs/software_architecture_and_integration_readiness_audit.md`). 

Every discrepancy between physical reality, electronic circuits, compiled C++ firmware headers, and Python gateway models has been cataloged and categorized by severity.

---

## 2. Critical Mismatches

| Discrepancy ID | Subsystem | Physical Ground Truth | Software / Repository Assumption | Impact & Forensic Risk |
| :---: | :--- | :--- | :--- | :--- |
| **CRIT-01** | **Actuator Pin Contention** | `GPIO 27` is physically soldered to the **Red Status LED** (verified Stage 02). | `PinConfig.h:19` assigns `pumpRelayPin = 27`. `device_config.json:31` assigns `pump_relay: 27`. | 🔴 **FATAL:** Activating the water pump relay in production will toggle the Red LED, and energizing both simultaneously risks over-current or silent actuator failure. |
| **CRIT-02** | **Analog Pin Contention** | `GPIO 34` is physically connected to the **Turbidity Sensor** via 33k/22k divider. | `PinConfig.h:10` assigns `doPin = 34`. `device_config.json:25` assigns `dissolved_oxygen: 34`. | 🔴 **FATAL:** If physical drivers are activated, the Dissolved Oxygen driver will read the Turbidity voltage, and Turbidity driver (assigned to 33) will read an unconnected pin. |
| **CRIT-03** | **OneWire Pin Collision** | `GPIO 33` is wired with a 4.7k$\Omega$ pull-up for the **DS18B20 Temp Probe**. | `PinConfig.h:9` assigns `turbidityPin = 33`. `PinConfig.h:11` assigns `tempPin = 18`. | 🔴 **CRITICAL:** Turbidity driver will attempt to read analog voltages on a digital 1-Wire bus held high by a 4.7k$\Omega$ pull-up resistor. |
| **CRIT-04** | **Discrete Actuator Discrepancy**| Green=`P25`, Yellow=`P26`, Red=`P27`, Buzzer=`P14`. | `PinConfig.h`: Green=`19`, Yellow=`21`, Red=`22`, Buzzer=`23`. | 🔴 **CRITICAL:** Production firmware toggles unpopulated GPIO pins (19, 21, 22, 23); zero physical LEDs or buzzer will respond to FSM states. |
| **CRIT-05** | **Camera Silicon Incompatibility**| Physical module is **GalaxyCore GC2145** (PID `0x2145`). Lacks hardware JPEG encoder. | `firmware/esp32_cam/main_esp32_cam.cpp:101` requests `PIXFORMAT_JPEG` assuming **OV2640**. | 🔴 **FATAL:** Calling `esp_camera_init` with `PIXFORMAT_JPEG` on GC2145 crashes or fails camera startup. Production firmware will not boot the camera. |
| **CRIT-06** | **Voltage Divider Omission** | Physical sensors use a $0.400\times$ voltage divider ($V_{\text{ADC}} = 0.4 \times V_{\text{SENSOR}}$). | `PHDriver.cpp:26` and `TurbidityDriver.cpp:25` calculate $V = \text{ADC} \times \frac{3.3}{4095}$ without $2.5\times$ multiplier. | 🔴 **CRITICAL:** Output voltage is suppressed by $60\%$. pH 7.0 (2.0V) calculates as 0.8V ($\text{pH} \approx 2.8$), triggering permanent sensor fault and acid alarms. |
| **CRIT-07** | **Production Firmware Mock Lock**| Microcontrollers are physically present and verified on `COM3` & `COM4`. | `firmware/src/main.cpp:36` hardcodes `ACTIVE_MODE = DriverMode::MOCK`. | 🔴 **CRITICAL:** Production firmware completely ignores physical hardware; only in-memory mock drivers run. |
| **CRIT-08** | **Network Broker Disconnect** | Microcontrollers, Gateway, and Backend must communicate via a common IP. | `main.cpp` uses `broker.hivemq.com`; `main_esp32_cam` uses `192.168.1.100`; `gateway.py` uses `InMemoryBroker`. | 🔴 **CRITICAL:** Microcontrollers and backend are broadcasting to completely disconnected networks. |

---

## 3. Non-Critical Mismatches

| Discrepancy ID | Subsystem | Description | Impact |
| :---: | :--- | :--- | :--- |
| **NONCRIT-01** | Directory Naming | Directory `firmware/bringup/07_ov2640_camera_verification/` contains `ov2640` in its path, but internally drives the GC2145 sensor. | Purely cosmetic; code functionality is fully verified. |
| **NONCRIT-02** | Documentation Stale Pins | `docs/HARDWARE_INTEGRATION_GUIDE.md` references strapping pins GPIO 12 and 15 from an early design draft. | Stale documentation; superseded by `docs/hardware_state_and_verification_audit.md`. |
| **NONCRIT-03** | Sampling Intervals | `main.cpp` samples sensors every 5000 ms; `device_config.json` specifies 10 seconds; `main_esp32_cam.cpp` captures every 10000 ms. | Minor timing variance; within operational requirements. |

---

## 4. Unverified Assumptions

1. **pH Linear Transformation:** The formula $\text{pH} = 3.5 \times V$ in `CalibrationProfiles.cpp` assumes a standard factory calibration curve with a 2.0V neutral point. The physical probe has never undergone reference buffer calibration (pH 4.01, 7.00, 10.01).
2. **Turbidity Quadratic NTU Polynomial:** The equation $\text{NTU} = -1120.4 \times V^2 + 5742.3 \times V - 4352.9$ assumes a direct 5.0V optical sensor reading without divider, calibrated against formazin NTU standards. Its accuracy with the physical probe and divider is unverified.
3. **Relay Optical Isolation Behavior:** `RelayDriver.cpp` assumes an active-low optocoupler board (`digitalWrite(_pin, LOW)` = ON). While typical for 5V relay modules, physical actuation of this specific board has not been tested with load.
4. **SNTP Time Drift Stability:** `CameraTransportReceiver` expects timestamp drift $\Delta t \le 30.0$ seconds. Field Wi-Fi jitter or lack of internet NTP access has not been evaluated outdoors.

---

## 5. Missing Integration Points

1. **Physical Driver Activation in Production Firmware:** `firmware/src/main.cpp` must be updated to instantiate real drivers when configured, linking `PHDriver`, `TurbidityDriver`, `LEDDriver`, and `BuzzerDriver`.
2. **GC2145 Software JPEG Integration:** The tested software JPEG conversion (`fmt2jpg`) from `firmware/bringup/07_ov2640_camera_verification/` must be ported into `firmware/esp32_cam/main_esp32_cam.cpp`.
3. **Gateway Real Broker Mode:** `src/iot/gateway.py` must be configured with `use_mock=False` to connect to an external MQTT broker listening for Main ESP32 and ESP32-CAM topics.
4. **Backend Ingestion Decoupling:** `src/backend/services.py` must allow connecting to live gateway telemetry rather than spawning synthetic `DeviceRuntimeManager` threads.

---

## 6. Blockers

| Blocker ID | Affected Subsystem | Root Cause | Prerequisite to Unblock |
| :---: | :--- | :--- | :--- |
| **BLOCK-01** | **Turbidity Sensor Integration** | Physical LM358 op-amp is biased at negative ground saturation ($0.258\,\text{V}$). Optical response to water fails. | Operator must use a miniature screwdriver to trim the 25-turn trimpot to ~1.6V–2.0V in clean water. |
| **BLOCK-02** | **DS18B20 Temp Integration** | OneWire bus scan discovered 0 ROM devices on GPIO33. Probe is deferred. | Resolve physical wiring / pull-up / sensor defect, or maintain in mock mode. |
| **BLOCK-03** | **Pump Relay Integration** | GPIO 27 is occupied by the Red LED; water pump hardware is not present. | Reassign relay to a free pin (e.g. GPIO 18, 19, or 23); operate in dry-contact indicator mode. |
| **BLOCK-04** | **Missing Sensors (DO, Salinity, GPS)** | Physical sensor hardware does not exist in the laboratory setup. | Formally designate these channels as synthetic/mock in production data contracts. |

---

## 7. Items Requiring Human Decision

Before integration begins, the project team must review and decide:

1. **Pin Assignment Formalization:**
   - *Option A (Recommended):* Update `firmware/include/config/PinConfig.h` and `config/device_config.json` to match the physically verified bench wiring:
     - Green LED = `GPIO 25`
     - Yellow LED = `GPIO 26`
     - Red LED = `GPIO 27`
     - Buzzer = `GPIO 14`
     - pH Probe = `GPIO 32`
     - Turbidity = `GPIO 34`
     - Temperature = `GPIO 33` (when re-introduced)
     - Pump Relay = Reassign to `GPIO 19` (safe, non-strapping digital output)
   - *Option B:* Rewire the physical breadboard to match the old `PinConfig.h` proposal. (High risk of strapping pin and ADC2 conflicts).

2. **Turbidity Staging Strategy:**
   - *Option A:* Keep Turbidity in mock/stub mode in production firmware until a miniature screwdriver is available to bias the trimpot.
   - *Option B:* Integrate the Turbidity ADC driver with a software flag marking calibration as pending, displaying raw ADC voltage in telemetry.

3. **Missing Hardware Handling Policy:**
   - Formally approve running a **Hybrid Production Architecture** where physically verified components (pH, Turbidity, LEDs, Buzzer, GC2145 Camera) operate on real hardware, while unavailable components (Dissolved Oxygen, Salinity, GPS, Water Pump) are populated by safe simulated baselines in the Gateway feature mapping.

4. **MQTT Broker Deployment:**
   - Designate the authoritative broker for development and capstone demonstration:
     - Local Mosquitto Broker on developer laptop (`localhost:1883`, accessible over LAN at e.g. `192.168.1.x:1883`).
     - Public Cloud Broker (`broker.hivemq.com`).

5. **Camera Frame Uplink Path:**
   - Confirm whether the ESP32-CAM will publish Base64 JPEGs over Wi-Fi MQTT directly to the Gateway, or if a companion serial transport daemon on `COM4` is desired for bench demos where local Wi-Fi may be unavailable.
