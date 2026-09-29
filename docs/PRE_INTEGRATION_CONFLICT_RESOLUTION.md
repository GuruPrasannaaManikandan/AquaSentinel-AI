# AquaSentinel-AI Pre-Integration Conflict Resolution & Authoritative Architecture Contract

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems (AquaSentinel-AI)  
**Milestone:** Pre-Integration Architecture Reconciliation  
**Document Status:** AUTHORITATIVE ARCHITECTURAL CONTRACT (READ-ONLY AUDIT & FORENSIC RECONCILIATION)  
**Target Microcontrollers:** NodeMCU ESP-32S (Main MCU, COM3) & AI-Thinker ESP32-CAM (Optical Node, COM4)  
**Classification Standard:** Strictly evidence-backed (`VERIFIED FACT`, `REPOSITORY FACT`, `PHYSICAL VERIFICATION`, `INFERENCE`, `HUMAN DECISION REQUIRED`, `FUTURE IMPLEMENTATION REQUIREMENT`).  

---

## 1. Purpose

This document establishes the single authoritative, evidence-backed hardware/software contract for the AquaSentinel-AI capstone project. 

Following the completion of physical hardware bring-up (discrete actuators, pH power/divider, turbidity ADC/divider, and ESP32-CAM optical acquisition) and the repository-wide forensic audit, multiple critical contradictions were identified between physical bench wiring, C++ firmware definitions (`PinConfig.h`), Python backend schemas (`device_config.json`), calibration mathematics, sensor health state machines, computer vision drivers, and network communications.

### Absolute Scope Rules
1. **Zero Production Changes:** No production source code, firmware headers, driver implementations, JSON configuration schemas, or build configurations have been modified during this reconciliation.
2. **Zero Firmware Flashing:** No binary has been uploaded to either microcontroller during this turn.
3. **Zero Physical Wiring Changes:** The physical bench wiring established during bring-up remains frozen.
4. **Authoritative Single Source of Truth:** This document reconciles all 13 discovered conflicts and outlines the precise preconditions and sequence required before authorized integration commences.

---

## 2. Evidence Sources

The findings and resolutions within this contract are directly derived from the following forensic evidence sources:

### 2.1 Physical Bench Measurements & Hardware Testing
- **Main ESP32 Serial Logs & Hardware Registers:** Verified via Silicon Labs CP210x on `COM3` (NodeMCU ESP-32S 38-pin, ESP32-D0WD-V3, rev 3.1).
- **ESP32-CAM Serial Logs & Hardware Registers:** Verified via WCH CH340 on `COM4` (ESP32-CAM-MB, ESP32-D0WD-V3 rev 3.1, 4MB PSRAM, GalaxyCore GC2145 PID `0x2145`).
- **Stage 01/02 LED Bring-Up Evidence:** `firmware/bringup/02_led_verification/src/main.cpp` (Physical GPIO 25, 26, 27).
- **Stage 03 Buzzer Bring-Up Evidence:** `firmware/bringup/03_buzzer_verification/src/main.cpp` (Physical GPIO 14).
- **Stage 04 DS18B20 Bring-Up Evidence:** `firmware/bringup/04_ds18b20_verification/src/main.cpp` (GPIO 33, 4.7 kΩ pull-up; 0 OneWire ROM devices detected).
- **Stage 05/05A pH Bring-Up Evidence:** `firmware/bringup/05_ph_power_verification/STAGE_05A_PH_ANALOG_INTERFACE_DESIGN.md` (33 kΩ / 22 kΩ divider on GPIO 32).
- **Stage 07 ESP32-CAM Bring-Up Evidence:** `firmware/bringup/07_ov2640_camera_verification/07_ov2640_camera_verification.ino` (PID `0x2145` detection, RGB565 to JPEG conversion).
- **Stage 08 Turbidity Bring-Up Evidence:** `firmware/bringup/08_turbidity_verification/08_turbidity_verification.ino` and `reports/turbidity_verification/turbidity_verification_report.json` (33 kΩ / 22 kΩ divider on GPIO 34, op-amp low saturation at 0.258V).

### 2.2 Repository Source Files Audited
- **Firmware Headers & Definitions:** `firmware/include/config/PinConfig.h`, `firmware/include/config/TelemetryData.h`, `firmware/include/config/SensorType.h`.
- **Firmware Core & Orchestration:** `firmware/src/main.cpp`, `firmware/src/DriverFactory.cpp`, `firmware/src/HAL.cpp`.
- **Physical Drivers:** `firmware/lib/PhysicalDrivers/` (`PHDriver.cpp`, `TurbidityDriver.cpp`, `DS18B20Driver.cpp`, `LEDDriver.cpp`, `BuzzerDriver.cpp`, `RelayDriver.cpp`).
- **Calibration Engine:** `firmware/lib/Calibration/` (`CalibratedSensor.cpp`, `CalibrationManager.cpp`, `CalibrationProfiles.cpp`, `CalibrationMath.cpp`).
- **Finite State Machine:** `firmware/lib/FSM/` (`FSM.cpp`, `TransitionTable.cpp`, `Event.h`, `State.h`, `FSMEvent.h`).
- **Camera Firmware:** `firmware/esp32_cam/main_esp32_cam.cpp`.
- **Configuration & Schemas:** `config/device_config.json`, `config/device_registry.json`, `config/fusion_policy.json`, `config/sensor_feature_mapping.json`.
- **AI/ML Model Artifacts & Code:** `models/model_registry.json`, `src/models/deployment_loader.py`, `src/ais/ais_loader.py`.
- **Gateway & Fusion Engine:** `src/iot/gateway.py`, `src/iot/mqtt_client.py`, `src/iot/sensor_quality.py`, `src/fusion/fusion_engine.py`, `src/fusion/decision_pipeline.py`, `src/fusion/temporal_intelligence.py`.

---

## 3. Verified Physical Hardware Baseline

The following table summarizes the authoritative physical bench state. Any claim diverging from this baseline is classified as non-physical or unverified.

| Subsystem / Component | Physical Device Identification | Board Pin / Channel | Power Rail | External Circuit / Protection | Physical Status | Forensic Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Main MCU** | NodeMCU ESP-32S (ESP32-D0WD-V3) | COM3 (Silicon Labs CP210x) | USB 5V | On-board 3.3V AMS1117 LDO | Operational | `PHYSICAL VERIFICATION` |
| **Green Status LED** | 5mm Green Diode | GPIO 25 (`P25`) | 3.3V Logic | 330 Ω series resistor to GND | Verified Active | `PHYSICAL VERIFICATION` |
| **Yellow Status LED** | 5mm Yellow Diode | GPIO 26 (`P26`) | 3.3V Logic | 330 Ω series resistor to GND | Verified Active | `PHYSICAL VERIFICATION` |
| **Red Status LED** | 5mm Red Diode | GPIO 27 (`P27`) | 3.3V Logic | 330 Ω series resistor to GND | Verified Active | `PHYSICAL VERIFICATION` |
| **Acoustic Alarm** | MB12A05 2-Pin Buzzer | GPIO 14 (`P14`) | 3.3V Logic | Negative pin to Common GND | Verified Active | `PHYSICAL VERIFICATION` |
| **pH Probe & Circuit** | PH-4502C Board + Glass Electrode | GPIO 32 (`P32`, ADC1_CH4)| ESP32 5V (VIN) | 33 kΩ / 22 kΩ Divider ($K=0.400$) | Electrically Verified | `PHYSICAL VERIFICATION` |
| **Turbidity Probe & Board** | Optical Transmittance Board | GPIO 34 (`P34`, ADC1_CH6)| ESP32 5V (VIN) | 33 kΩ / 22 kΩ Divider ($K=0.400$) | ADC Valid / Optical Pending | `PARTIALLY VERIFIED` |
| **Temperature Sensor** | DS18B20 Waterproof Probe | GPIO 33 (`P33`, Digital) | 3.3V Rail | 4.7 kΩ pull-up to 3.3V | 0 Devices Found | `DEFERRED / NOT VERIFIED` |
| **Aerator Relay** | SRD-05VDC-SL-C 5V Relay | Disconnected / Floating | 5V Rail | Optocoupled isolation | Hardware Exists / No Pump | `DEFERRED / NOT VERIFIED` |
| **Optical Edge Node** | AI-Thinker ESP32-CAM | COM4 (WCH CH340 Programmer) | USB 5V | 4MB External PSRAM Active | Operational | `PHYSICAL VERIFICATION` |
| **Camera Sensor** | GalaxyCore GC2145 (PID `0x2145`) | Dedicated DVP Ribbon Bus | 3.3V/1.8V (LDO) | No Hardware JPEG Engine | Optical Frames Verified | `PHYSICAL VERIFICATION` |
| **Dissolved Oxygen (DO)**| None | N/A | N/A | N/A | Not Available | `REPOSITORY FACT` (Missing) |
| **Salinity / TDS** | None | N/A | N/A | N/A | Not Available | `REPOSITORY FACT` (Missing) |
| **GPS Module** | None | N/A | N/A | N/A | Not Available | `REPOSITORY FACT` (Missing) |
| **Water Pump** | None | N/A | N/A | N/A | Not Available | `REPOSITORY FACT` (Missing) |

---

## 4. Authoritative GPIO Map

Based on physical bench verification, ESP32 silicon errata (ADC2 Wi-Fi contention), and pin safety audits, the following authoritative GPIO map is established:

```
                                  ESP32-WROOM-32 (NodeMCU ESP-32S 38-Pin)
                                              +---------------+
                                          3V3 |               | GND
                                           EN |               | GPIO 23 (Free Digital IO / VSPI MOSI)
                     (Free ADC1)  GPIO 36 / VP|               | GPIO 22 (Free Digital IO / I2C SCL)
                     (Free ADC1)  GPIO 39 / VN|               | GPIO 1 (UART0 TX - Serial Console)
                     (Free ADC1)  GPIO 34 / P34 <---- OUT     | GPIO 3 (UART0 RX - Serial Console)
                     (Free ADC1)  GPIO 35 / P35| (Turbidity)   | GPIO 21 (Free Digital IO / I2C SDA)
   (pH Module Po via Divider)     GPIO 32 / P32 <---- Po      | GND
(DS18B20 1-Wire via 4.7k Pullup)  GPIO 33 / P33 <---- DATA    | GPIO 19 (Free Digital IO / VSPI MISO) [CANDIDATE: RELAY]
                     (Buzzer (+)) GPIO 14 / P14 <---- BUZZER  | GPIO 18 (Free Digital IO / VSPI CLK)
                                  GPIO 12     | (MTDI-UNSAFE) | GPIO 5  (VSPI CS / PWM Boot Glitch)
                                  GPIO 13     |               | GPIO 17 (Free UART2 TX)
                                  GPIO 9      | (FLASH D2)    | GPIO 16 (Free UART2 RX)
                                  GPIO 10     | (FLASH D3)    | GPIO 4  (Free Digital IO / Touch 0)
                                  GPIO 11     | (FLASH CMD)   | GPIO 0  (Boot Strapping / Flash Jumper)
                                  GPIO 6      | (FLASH CLK)   | GPIO 2  (Strapping / On-board Blue LED)
                                  GPIO 7      | (FLASH D0)    | GPIO 15 (MTDO Strapping / PWM Glitch)
                                  GPIO 8      | (FLASH D1)    | GPIO 8  (FLASH D1)
                       (Green LED)GPIO 25 / P25 <---- GREEN   | GPIO 27 (Red LED) <---- RED
                      (Yellow LED)GPIO 26 / P26 <---- YELLOW  | GND
                                  5V / VIN    |               | 3V3
                                              +---------------+
```

| GPIO | Board Label | Direction | Silicon Domain | Bench Function | Physical Verification | Production Assignment Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GPIO 14** | `P14` | Output | Digital IO (ADC2_CH6) | Audio Alarm Buzzer | Verified (Stage 03) | **CONFIRMED** |
| **GPIO 19** | `P19` | Output | Digital IO (VSPI MISO)| Unassigned (Relay Candidate) | Tested in Stage 01 | **PRIMARY RELAY CANDIDATE** |
| **GPIO 25** | `P25` | Output | Digital IO (ADC2_CH8) | Green Status LED | Verified (Stage 02) | **CONFIRMED** |
| **GPIO 26** | `P26` | Output | Digital IO (ADC2_CH9) | Yellow Status LED | Verified (Stage 02) | **CONFIRMED** |
| **GPIO 27** | `P27` | Output | Digital IO (ADC2_CH7) | Red Status LED | Verified (Stage 02) | **CONFIRMED (RELAY CONFLICT)** |
| **GPIO 32** | `P32` | Input | Analog (ADC1_CH4) | Analog pH Module ($Po$) | Verified (Stage 05A)| **CONFIRMED** |
| **GPIO 33** | `P33` | In/Out | Digital (ADC1_CH5) | DS18B20 1-Wire DQ | Attempted (Stage 04) | **RESERVED FOR TEMPERATURE** |
| **GPIO 34** | `P34` | Input | Analog (ADC1_CH6, GPI) | Turbidity Board ($OUT$)| Verified (Stage 08) | **CONFIRMED (GPI INPUT-ONLY)**|

---

## 5. GPIO Conflicts

A comprehensive cross-comparison of physical bench wiring versus repository files reveals major pin collisions that would cause catastrophic hardware conflicts or silent telemetry corruption if loaded into production code:

| Peripheral / Channel | Physical Bench Wiring | `PinConfig.h` (C++) | `device_config.json` | `PHYSICAL_WIRING_PLAN.md` | Nature of Conflict | Impact & Hazard |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Red Status LED** | **GPIO 27** | `redLedPin = 22` | `red_led: 22` | `GPIO 22` | Direct pin mismatch | Firmware writes to GPIO 22; Red LED on GPIO 27 never illuminates. |
| **Pump Relay** | **Unassigned** | `pumpRelayPin = 27` | `pump_relay: 27` | `GPIO 27` | **CRITICAL COLLISION** | Firmware toggles relay; physical hardware toggles Red LED! If relay is wired to 27, it overloads LED line. |
| **Green Status LED**| **GPIO 25** | `greenLedPin = 19` | `green_led: 19` | `GPIO 19` | Direct pin mismatch | Firmware toggles GPIO 19; physical Green LED on GPIO 25 remains dark. |
| **Yellow Status LED**| **GPIO 26**| `yellowLedPin = 21`| `yellow_led: 21` | `GPIO 21` | Direct pin mismatch | Firmware toggles GPIO 21; physical Yellow LED on GPIO 26 remains dark. |
| **Audio Buzzer** | **GPIO 14** | `buzzerPin = 23` | `buzzer: 23` | `GPIO 23` | Direct pin mismatch | Firmware toggles GPIO 23; physical Buzzer on GPIO 14 never sounds. |
| **Turbidity Sensor**| **GPIO 34** | `turbidityPin = 33`| `turbidity: 33` | `GPIO 33` | **CRITICAL COLLISION** | Turbidity driver reads GPIO 33 (DS18B20 1-Wire pin pulled up to 3.3V). Reads constant 3.3V. |
| **Dissolved Oxygen**| **NOT AVAILABLE** | `doPin = 34` | `dissolved_oxygen: 34` | `GPIO 34` | **CRITICAL COLLISION** | DO driver reads GPIO 34 (the physical Turbidity sensor!). Turbidity optical signal is treated as DO. |
| **Temperature** | **GPIO 33 (Deferred)**| `tempPin = 18` | `temperature: 18` | `GPIO 18` | Direct pin mismatch | OneWire driver listens on GPIO 18; physical probe is wired to GPIO 33. |
| **Salinity / TDS** | **NOT AVAILABLE** | `salinityPin = 36`| `salinity: 36` | `GPIO 36` | Missing hardware | Driver reads floating high-impedance ADC pin. |
| **GPS RX / TX** | **NOT AVAILABLE** | `gpsRx=16, gpsTx=17`| `gps_rx:16, gps_tx:17`| `RX=16, TX=17` | Missing hardware | UART2 reads open lines. |

---

## 6. Relay Assignment Candidates

Because `GPIO 27` is physically occupied by the Red Status LED, the aerator pump relay requires an alternative GPIO pin assignment. All available ESP32 pins have been audited for electrical safety, boot-strapping interference, ADC2 Wi-Fi contention, and physical availability:

| Candidate GPIO | Silicon Capabilities | Boot/Strap Concerns | Wi-Fi / ADC Concerns | Physical Conflict | Suitability Assessment | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GPIO 19** | Digital IO, VSPI MISO | None (Standard IO) | None (Digital output) | Completely free | **OPTIMAL**: Clean digital output, tested in Stage 01. | **RECOMMENDED PRIMARY** |
| **GPIO 23** | Digital IO, VSPI MOSI | None (Standard IO) | None (Digital output) | Completely free | **OPTIMAL**: Clean digital output, zero boot artifacts. | Alternative Candidate 1 |
| **GPIO 18** | Digital IO, VSPI CLK | None (Standard IO) | None (Digital output) | Free if DS18B20 remains on 33 | **EXCELLENT**: Standard digital output. | Alternative Candidate 2 |
| **GPIO 4** | Digital IO, Touch 0 | None (Standard IO) | ADC2 (Output unaffected) | Free on main MCU | **GOOD**: Usable digital output. | Alternative Candidate 3 |
| **GPIO 16** | Digital IO, UART2 RX | None (Standard IO) | None (Digital output) | Free (GPS absent) | **GOOD**: Usable if GPS UART2 is disabled. | Alternative Candidate 4 |
| **GPIO 12** | Digital IO, MTDI | **FATAL HAZARD**: MTDI strap | Flash brownout if pulled HIGH | Avoid | **UNSAFE**: Will brick boot if relay module pulls up. | **REJECTED** |
| **GPIO 15** | Digital IO, MTDO | Outputs PWM glitch on boot | Silences boot logs if pulled LOW| Avoid | **UNSAFE**: Relay will click violently on MCU reboot. | **REJECTED** |
| **GPIO 0, 2** | Boot Strapping Pins | Flashing mode selector | Boot failure hazard | Avoid | **UNSAFE**: Interferes with UART flashing and bootloader.| **REJECTED** |
| **GPIO 34-39** | GPI (Input-Only) | None | N/A | No output drivers | **IMPOSSIBLE**: Input-only silicon pins cannot drive relay.| **REJECTED** |

### Human Decision D02
> `GPIO 19` is the technically recommended candidate for the pump relay. However, physical jumpering and software configuration requires human authorization before implementation.

---

## 7. Sensor Verification State

Every sensor channel is classified into a rigorous verification status based on physical evidence:

```
  [pH Sensor]        Power: PASS | Divider: PASS | ADC: PASS | Accuracy: PENDING (Buffer Cal Required)
  [Turbidity Sensor] Power: PASS | Divider: PASS | ADC: PASS | Optical Liquid Discrimination: PENDING (Trimpot Low)
  [DS18B20 Temp]     Wiring: PASS | Pull-up: PASS | OneWire Scan: 0 Devices | Status: DEFERRED / NOT VERIFIED
  [Dissolved Oxygen] Hardware: NOT AVAILABLE | Status: SIMULATION / MOCK ONLY
  [Salinity / TDS]   Hardware: NOT AVAILABLE | Status: SIMULATION / MOCK ONLY
  [GPS Module]       Hardware: NOT AVAILABLE | Status: SIMULATION / MOCK ONLY
  [Water Pump]       Hardware: NOT AVAILABLE | Status: SIMULATION / MOCK ONLY
  [GC2145 Camera]    Power: PASS | PSRAM: PASS | Sensor ID: PASS (0x2145) | Image Capture: PASS (RGB565+JPEG)
```

1. **pH Sensor:** Electrically verified. Operating safely through a $33\text{ k}\Omega / 22\text{ k}\Omega$ voltage divider on GPIO 32. Output tracks op-amp potential, but calibrated accuracy across standard buffer solutions (pH 4.01, 7.00, 10.01) is not established.
2. **Turbidity Sensor:** Electrically and safety verified. Operating safely through a $33\text{ k}\Omega / 22\text{ k}\Omega$ voltage divider on GPIO 34. ADC sampling is stable (mean raw $\approx 320$, $V_{P34} \approx 0.103\text{ V}$, reconstructed $V_{OUT} \approx 0.258\text{ V}$). However, optical liquid response is **NOT VERIFIED** because the LM358 op-amp on the breakout board is biased into near-ground saturation; trimpot adjustment with a miniature screwdriver is pending.
3. **DS18B20 Temperature Sensor:** Designed and physically wired on GPIO 33 with a 4.7 kΩ pull-up resistor. During Stage 04 bring-up, the OneWire bus scan discovered **0 ROM devices**. Sensor hardware is classified as **DEFERRED / NOT VERIFIED**.
4. **Dissolved Oxygen, Salinity, GPS, and Water Pump:** Classified as **NOT AVAILABLE**.

---

## 8. pH Voltage / Data Contract

### 8.1 Physical Circuit & Voltage Division
- The PH-4502C signal conditioning module operates from the **5.0V** rail.
- In alkaline environments or uncalibrated trimmer offsets, the op-amp output ($P_o$) can swing up to $4.10\text{ V DC}$.
- To protect the ESP32 ADC (maximum 3.30V), a precision voltage divider is physically inserted:
  $$K = \frac{R_{bottom}}{R_{top} + R_{bottom}} = \frac{22\text{ k}\Omega}{33\text{ k}\Omega + 22\text{ k}\Omega} = \frac{22}{55} = 0.400$$
- The voltage present at GPIO 32 ($V_{P32}$) relates to the module op-amp output ($V_{module}$) as:
  $$V_{P32} = 0.400 \times V_{module} \quad \Longleftrightarrow \quad V_{module} = 2.500 \times V_{P32}$$

### 8.2 Forensic Data Path Trace
```
Physical pH Probe
      ↓
PH-4502C Analog Out (V_module: ~0.0V - 4.1V)
      ↓ (33kΩ / 22kΩ Divider: K = 0.400)
ESP32 GPIO 32 (V_P32: ~0.0V - 1.64V)
      ↓
PHDriver::read() [firmware/lib/PhysicalDrivers/PHDriver.cpp:26]
   Calculates: voltage = rawAdc * (3.3 / 4095.0)  --> Returns V_P32 (MISSING 2.5x FACTOR)
      ↓
CalibratedSensor::read() [firmware/lib/Calibration/CalibratedSensor.cpp:29]
   Passes raw voltage to CalibrationManager::calibrate(SensorType::PH, rawValue)
      ↓
CalibrationProfiles::getCoefficients(SensorType::PH) [firmware/lib/Calibration/CalibrationProfiles.cpp:9]
   Formula: pH = slope * V + intercept = 3.5 * V + 0.0
      ↓
HAL::readAllSensors() [firmware/src/HAL.cpp:61]
   Assigns: data.ph = calibrated_ph
      ↓
TelemetryData [firmware/include/config/TelemetryData.h:10]
      ↓
BackendGateway / MQTT [firmware/src/main.cpp:178]
      ↓
Gateway::on_message_received [src/iot/gateway.py:180]
      ↓
SensorQualityEvaluator [src/iot/sensor_quality.py:261]
      ↓
FusionEngine [src/fusion/fusion_engine.py:188]
```

### 8.3 The Forensic Mathematical Error
- `CalibrationProfiles.cpp` defines $pH = 3.5 \times V$.
- For neutral water, standard pH modules output $V_{module} \approx 2.0\text{ V}$.
- Under the original un-attenuated design: $pH = 3.5 \times 2.0\text{ V} = 7.00$ (Neutral).
- Under the physical $0.400\times$ divider: $V_{P32} = 0.400 \times 2.0\text{ V} = 0.800\text{ V}$.
- Currently, `PHDriver.cpp` returns $0.800\text{ V}$. `CalibratedSensor` applies $3.5 \times 0.800\text{ V} = \mathbf{2.80\text{ pH}}$.
- **Result:** Neutral water produces an extreme acid reading ($pH = 2.80$), immediately violating `ValidationThresholds::minCritical = 4.0` in `FreshwaterProfile`, triggering a `CRITICAL` fault!

### 8.4 Authoritative Future Contract
The $2.500\times$ reconstruction must be placed inside `PHDriver.cpp` so that the driver contract satisfies:
$$\text{Output of } PHDriver::read() \equiv V_{module} = \left(\text{rawAdc} \times \frac{3.3}{4095.0}\right) \times 2.500$$
This preserves the semantic integrity of `CalibrationProfiles.cpp`, `device_config.json`, and all downstream validation models.

---

## 9. Turbidity Voltage / Data Contract

### 9.1 Physical Circuit & Attenuation
- Turbidity signal conditioning board powered from **5.0V** rail.
- Physical interface board pins: `VCC`, `OUT`, `GND`.
- Identical divider network physically wired: $33\text{ k}\Omega$ top, $22\text{ k}\Omega$ bottom to GND ($K = 0.400$).
  $$V_{P34} = 0.400 \times V_{OUT} \quad \Longleftrightarrow \quad V_{OUT} = 2.500 \times V_{P34}$$

### 9.2 Forensic Data Path Trace & The DFRobot Quadratic Model
```
Optical Liquid Transmittance
      ↓
Breakout Board Output (V_OUT: 0.0V - 4.5V)
      ↓ (33kΩ / 22kΩ Divider: K = 0.400)
ESP32 GPIO 34 (V_P34: 0.0V - 1.80V) [INPUT-ONLY GPI]
      ↓
TurbidityDriver::read() [firmware/lib/PhysicalDrivers/TurbidityDriver.cpp:26]
   Calculates: voltage = rawAdc * (3.3 / 4095.0)  --> Returns V_P34 (MISSING 2.5x FACTOR)
      ↓
CalibratedSensor::read()
      ↓
CalibrationManager::calibrate() [firmware/lib/Calibration/CalibrationManager.cpp:38]
   Calls: CalibrationMath::applyTurbidity(rawValue, a, b, c)
      Formula: NTU = -1120.4 * V^2 + 5742.3 * V - 4352.9
```

### 9.3 The Mathematical Catastrophe
- The standard quadratic formula ($NTU = -1120.4 V^2 + 5742.3 V - 4352.9$) is parameterized exclusively for **5V module voltage $V_{OUT}$**:
  - Clear Water ($V_{OUT} = 4.20\text{ V}$): $NTU = -1120.4(4.2)^2 + 5742.3(4.2) - 4352.9 \approx \mathbf{0.96\text{ NTU}}$ (Nominal).
  - Turbid Water ($V_{OUT} = 2.50\text{ V}$): $NTU = -1120.4(2.5)^2 + 5742.3(2.5) - 4352.9 \approx \mathbf{3000\text{ NTU}}$ (Clamped to 500 NTU).
- However, with the physical divider, the maximum voltage reaching GPIO 34 is $V_{P34} \le 1.80\text{ V}$.
- At $V = 1.0\text{ V}$: $NTU = -1120.4(1.0) + 5742.3(1.0) - 4352.9 = \mathbf{269\text{ NTU}}$.
- At $V = 0.103\text{ V}$ (current bench state): $NTU = -1120.4(0.0106) + 5742.3(0.103) - 4352.9 = -3773\text{ NTU} \rightarrow \mathbf{0.0\text{ NTU}}$ (clamped).
- Furthermore, `CalibrationProfiles.cpp:11` sets `maxRawVolts = 3.2f`. If $V_{OUT} = 4.2\text{ V}$ were passed directly, `CalibrationManager.cpp:30` rejects it as an out-of-bounds hardware fault (`return -999.0f`)!

### 9.4 Authoritative Future Contract
1. `TurbidityDriver.cpp` must reconstruct $V_{OUT} = V_{P34} \times 2.500$.
2. `CalibrationProfiles.cpp` must update `maxRawVolts = 5.0f` to accommodate the reconstructed 5V domain.
3. Until the physical trimpot is adjusted and verified with clean water vs turbid samples, NTU values cannot be claimed as calibrated.

---

## 10. DS18B20 Contract

### 10.1 Physical & Driver Health State Contract
During Stage 04 bring-up on GPIO 33, the DallasTemperature bus scan detected 0 devices. The software contract must strictly accommodate this hardware reality:

```
[DS18B20 Hardware State]
       │
       ├── Devices Discovered == 0 ──► initialize() returns FALSE ──► Health: SENSOR_DISCONNECTED
       │                                                                  ↓
       │                                                              read() returns -999.0f
       │                                                                  ↓
       │                                                              CalibratedSensor: FAULT
       │                                                                  ↓
       └── Devices Discovered >= 1 ──► Normal Sampling ─────────────► Health: OK
```

| Operating State | Driver Return Value | `DriverHealth` Enum | `CalibratedSensor` Status | Gateway Telemetry Value | System Health Flag |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **VERIFIED (Active)** | Actual Temp in °C | `DriverHealth::OK` | `"OK"` | Actual float (e.g. 24.2) | Nominal |
| **NOT_VERIFIED (Deferred)**| `-999.0f` | `DriverHealth::NOT_INITIALIZED`| `"FAULT"` | `None` / `null` | Warning |
| **DISCONNECTED (Current)** | `-999.0f` | `DriverHealth::SENSOR_DISCONNECTED`| `"FAULT"` | `None` / `null` | Sensor Degraded |
| **CRC_FAILURE (Bus Error)**| `-999.0f` | `DriverHealth::CRC_FAILURE` | `"FAULT"` | `None` / `null` | Sensor Degraded |

### 10.2 Downstream Safety Rules
1. `HAL::runSelfTest()` must NOT enter a fatal bootloop if DS18B20 returns `SENSOR_DISCONNECTED`.
2. `gateway.py` and `sensor_quality.py` must check for `-999.0f`, `None`, or `NaN` and mark `temperature_c` as unavailable rather than passing `-999.0` into thermal growth models.

---

## 11. Missing Hardware Contract

Four components in the project design have no physical presence on the bench:
- **Dissolved Oxygen Sensor**
- **Salinity / TDS Sensor**
- **GPS Module**
- **Aerator Water Pump**

### Architectural Representation Options

#### Option A: Explicitly Represented as Unavailable (Recommended)
- Firmware reports `-999.0f` or omits the fields.
- JSON telemetry sends `null` for `dissolved_oxygen_mg_l`, `salinity_ppt`, and `latitude`/`longitude`.
- Gateway marks modalities as `MISSING` in `MultimodalSnapshot`.
- `SensorQualityEvaluator` computes $q_{sensor}$ based strictly on active sensors.
- `ConcordanceEngine` and `FusionEngine` dynamically adjust modality weights without penalty.

#### Option B: Explicitly Tagged as Synthetic / Simulated
- If downstream models require synthetic inputs to prevent crashes, values are generated by `MockDrivers` or `sensor_simulator.py`.
- **Mandatory Tagging:** The telemetry payload must include an explicit provenance tag:
  ```json
  "sensor_provenance": {
    "ph": "PHYSICAL_ADC",
    "turbidity_ntu": "PHYSICAL_ADC",
    "temperature_c": "UNAVAILABLE",
    "dissolved_oxygen_mg_l": "SYNTHETIC_MOCK",
    "salinity_ppt": "SYNTHETIC_MOCK",
    "gps": "SYNTHETIC_MOCK"
  }
  ```
- **Safety Rule:** Synthetic values must never be stored as ground truth in `event_store.db`.

### Human Decision D09
> Human authorization is required to decide between Option A (strict `null` / unavailable) and Option B (tagged synthetic data) for the final Capstone demo.

---

## 12. Production Driver Mode Contract

### 12.1 Forensic Reality of Current Firmware
- In `firmware/src/main.cpp:36`:
  ```cpp
  const DriverMode ACTIVE_MODE = DriverMode::MOCK;
  ```
- All sensors are allocated via `DriverFactory::create...()` using `ACTIVE_MODE`.
- In `firmware/src/DriverFactory.cpp`, when `mode == DriverMode::MOCK`, every sensor is a mock class (`MockPHSensor`, `MockTurbiditySensor`, etc.) that returns hardcoded constants (`ph = 7.4`, `turbidity = 4.2 NTU`, `temp = 24.5 C`).
- **Network Stack:** `main.cpp:84,92` directly instantiates `MockWiFiService mockWiFi;` and `MockMQTTService mockMQTT;`. No real Wi-Fi or real MQTT driver exists in `main.cpp`.

### 12.2 What Happens if `DriverMode::PHYSICAL` is Activated Today?
If `ACTIVE_MODE` were changed to `PHYSICAL` without prior code corrections:
1. `PHDriver` outputs $V_{P32}$ instead of $V_{module}$ $\rightarrow$ pH calculates to 2.80 $\rightarrow$ `CRITICAL` fault.
2. `TurbidityDriver` reads GPIO 33 (DS18B20 1-Wire pin) $\rightarrow$ reads constant 3.3V $\rightarrow$ NTU calculation invalid.
3. `DODriver` reads GPIO 34 (Turbidity sensor) $\rightarrow$ reads optical signal as dissolved oxygen.
4. `DS18B20Driver` initializes on GPIO 18 (unconnected pin) $\rightarrow$ returns -999.0 $\rightarrow$ `FAULT`.
5. `LEDDriver` and `BuzzerDriver` actuate GPIOs 19, 21, 22, 23 (unconnected pins) $\rightarrow$ bench LEDs/buzzer stay dark.
6. `RelayDriver` writes to GPIO 27 $\rightarrow$ corrupts Red Status LED.
7. `HAL::runSelfTest()` returns `false` $\rightarrow$ FSM transitions to `State::FAULT` $\rightarrow$ device enters permanent recovery bootloop.

### 12.3 Authoritative Future Contract: Hybrid Driver Architecture
To safely integrate physical hardware, `DriverFactory` must support a **Hybrid Driver Mode**:
- `PHDriver`: **PHYSICAL** (GPIO 32, with 2.5x divider reconstruction).
- `TurbidityDriver`: **PHYSICAL** (GPIO 34, raw voltage window mode).
- `LEDDriver`: **PHYSICAL** (Green=25, Yellow=26, Red=27).
- `BuzzerDriver`: **PHYSICAL** (GPIO 14).
- `DS18B20Driver`: **MOCK / DEFERRED** (until sensor defect resolved).
- `DODriver`, `SalinityDriver`, `GPSSensor`: **MOCK** (missing physical hardware).
- `RelayDriver`: **MOCK / UNASSIGNED** (missing physical pump).

---

## 13. FSM Health Contract

### 13.1 Confirmed Mismatch
The forensic audit confirmed an architectural disconnect between the Hardware Abstraction Layer and the Finite State Machine:

```
[CalibratedSensor Status]
   Returns: "OK" | "WARNING" | "CRITICAL" | "FAULT"
       │
       ▼
   (DISCONNECTED IN HAL)
       │
       ▼
[HAL::_sensorStatus]
   Set ONLY in initialize() & runSelfTest(): "OK" | "FAULT"
       │
       ▼
[TelemetryData::sensor_status]
   Populated with HAL::_sensorStatus: ALWAYS "OK" (or "FAULT" on boot fail)
       │
       ▼
[FSM::executeUpdateActions(State::MONITORING)]
   Evaluates: strcmp(data.sensor_status, "WARNING")  --> NEVER TRUE!
              strcmp(data.sensor_status, "CRITICAL") --> NEVER TRUE!
```

### 13.2 Evidence in Code
1. `firmware/lib/Calibration/CalibratedSensor.cpp:53-58`:
   ```cpp
   switch (_lastValidation) {
       case ValidationState::VALID:    return "OK";
       case ValidationState::WARNING:  return "WARNING";
       case ValidationState::CRITICAL: return "CRITICAL";
       case ValidationState::FAULT:    return "FAULT";
   }
   ```
2. `firmware/src/HAL.cpp:52, 121`:
   ```cpp
   _sensorStatus = success ? "OK" : "FAULT";
   _sensorStatus = healthy ? "OK" : "FAULT";
   ```
3. `firmware/src/HAL.cpp:70`:
   ```cpp
   data.sensor_status = _sensorStatus;
   ```
4. `firmware/lib/FSM/FSM.cpp:237-240`:
   ```cpp
   } else if (strcmp(data.sensor_status, "CRITICAL") == 0) {
       dispatch(Event::ALERT_DETECTED, "Critical thresholds exceeded");
   } else if (strcmp(data.sensor_status, "WARNING") == 0) {
       dispatch(Event::WARNING_DETECTED, "Warning thresholds exceeded");
   }
   ```

### 13.3 Authoritative Future Contract
`HAL::readAllSensors()` must compute an aggregate health state across all active calibrated sensors:
- If ANY sensor is `FAULT` $\rightarrow$ `data.sensor_status = "FAULT"`
- Else if ANY sensor is `CRITICAL` $\rightarrow$ `data.sensor_status = "CRITICAL"`
- Else if ANY sensor is `WARNING` $\rightarrow$ `data.sensor_status = "WARNING"`
- Else $\rightarrow$ `data.sensor_status = "OK"`

This restores the active dispatch of `Event::WARNING_DETECTED` and `Event::ALERT_DETECTED` to drive FSM transitions.

---

## 14. ESP32-CAM / GC2145 Contract

### 14.1 Hardware Silicon Identification
- Camera physical module: **GalaxyCore GC2145** (Silicon PID `0x2145`, DVP parallel interface).
- Microcontroller: ESP32-D0WD-V3 with **4 MB External PSRAM** active.
- **Silicon Limitation:** The GC2145 has **NO internal JPEG compression hardware engine** (unlike OmniVision OV2640).

### 14.2 Production Firmware Failure
In `firmware/esp32_cam/main_esp32_cam.cpp:101`:
```cpp
config.pixel_format = PIXFORMAT_JPEG;
esp_err_t err = esp_camera_init(&config);
```
When executed on the GC2145, the ESP-IDF camera driver returns error code `0x0106` (`ESP_ERR_NOT_SUPPORTED`) and crashes.

### 14.3 Verified Working Solution
In `firmware/bringup/07_ov2640_camera_verification/07_ov2640_camera_verification.ino`:
1. Initialize camera with `config.pixel_format = PIXFORMAT_RGB565` into PSRAM (`CAMERA_FB_IN_PSRAM`).
2. Capture uncompressed 16-bit RGB565 optical frame.
3. Call `frame2jpg(fb, 80, &jpgBuf, &jpgLen)` (`img_converters.h`) to compress RGB565 to standard JPEG in PSRAM.
4. Transmit JPEG over Base64 serial or MQTT.

### 14.4 Authoritative Production Camera Contract
The production camera firmware must replace the native OV2640 assumption with the verified GC2145 two-stage pipeline:
- Pixel Format: `PIXFORMAT_RGB565`
- Frame Size: `FRAMESIZE_224X224` (Native MobileNetV3 input shape)
- Framebuffer Location: `CAMERA_FB_IN_PSRAM` (Frame buffer count = 2)
- Compression: Software `frame2jpg()` in PSRAM with JPEG quality 80.
- Payload Contract: JSON envelope containing Base64 JPEG string, ISO8601 timestamp, and frame sequence ID published to `aquatic/AQUA_FRESH_001/camera/raw`.

---

## 15. MQTT Contract

### 15.1 Repository Broker Audit
A forensic audit across all configuration files revealed four completely disconnected broker targets:

| Component | Target File | Configured Broker Host | Port | Transport Protocol | Intended Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Main ESP32 Firmware** | `firmware/src/main.cpp:88` | `broker.hivemq.com` | 1883 | Plaintext TCP MQTT | Public Cloud MQTT Broker |
| **ESP32-CAM Firmware** | `firmware/esp32_cam/main_esp32_cam.cpp:45` | `192.168.1.100` | 1883 | Plaintext TCP MQTT | Local Subnet Gateway IP |
| **Python Device Config**| `config/device_config.json:12`| `localhost` | 1883 | Loopback TCP | Local Development Host |
| **IoT Central Gateway** | `src/iot/gateway.py:52` | `InMemoryMQTTBroker` | N/A | In-memory Python Object | Deterministic Testing |
| **Python MQTT Client** | `src/iot/mqtt_client.py:89` | `localhost` | 1883 | `paho-mqtt` Client | Live Broker Integration |

### 15.2 Authoritative Production Broker Contract
To enable real wireless telemetry between Main ESP32, ESP32-CAM, and the central Python backend, one unified broker must be authorized:
- **Topology:** Central Local MQTT Broker (e.g. Eclipse Mosquitto running on the development PC).
- **Target Host IP:** The static LAN IP of the host machine (e.g., `192.168.1.X` or local hotspot IP).
- **Topic Hierarchy:**
  - Telemetry: `aquatic/{device_id}/telemetry`
  - Camera Frames: `aquatic/{device_id}/camera/raw`
  - System Decisions: `aquatic/{device_id}/decision`
  - Actuator Commands: `aquatic/{device_id}/command`
  - Device Status: `aquatic/{device_id}/status`

### Human Decision D11
> Human authorization is required to select between a Local Mosquitto Broker on LAN IP vs an external Public Cloud Broker (`broker.hivemq.com`).

---

## 16. Model Feature Contracts

A forensic inspection of trained models (`models/model_registry.json`) and the decision pipeline (`src/fusion/decision_pipeline.py`) reveals exactly where physical sensor data enters the AI system:

| Model / Subsystem | Artifact Path | Consumed Features | Physical Sensor Dependency | Geospatial / Temporal Dependency | Role in System Architecture |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CAML Freshwater Model** | `models/deployment/caml_champion.joblib` | `lat`, `lon`, `distance_to_water_m`, `region`, `Season`, `Year`, `Month_sin`, `Month_cos`, `DayOfYear_sin`, `DayOfYear_cos` | **ZERO** (Does NOT consume pH, Turbidity, DO, Temp) | Requires GPS coordinates & Calendar Timestamps | Predicts geographical baseline bloom severity ($P_{bloom}$). |
| **HABSOS Marine Model** | `models/deployment/habsos_champion.joblib` | `LATITUDE`, `LONGITUDE`, `STATE_ID`, `SAMPLE_DEPTH`, `SALINITY`, `WATER_TEMP`, `Season`, `Year`, `Month`, `Month_sin`, `Month_cos`, `DayOfYear_sin`, `DayOfYear_cos` | Consumes `SALINITY` & `WATER_TEMP` | Requires GPS coordinates & Calendar Timestamps | Predicts marine dinoflagellate risk categories. |
| **AIS Anomaly Detector** | `models/ais/caml_ais_detector_v1.0.joblib` | Same feature schema as CAML / HABSOS | **ZERO** (Does NOT consume pH, Turbidity, DO) | Requires GIS coordinates & Calendar Timestamps | Detects spatial-temporal anomalies outside known baseline. |
| **Computer Vision (CV)** | `models/cv/mobilenetv3_aquatic_bloom.pt` | $224 \times 224 \times 3$ RGB optical image | Consumes optical frame from GC2145 camera | Synchronized timestamp | Classifies bloom presence, turbidity discoloration, or clear water. |
| **Sensor Quality Engine**| `src/iot/sensor_quality.py` | `temperature_c`, `ph`, `turbidity_ntu`, `salinity_ppt`, `dissolved_oxygen_mg_l` | **100% DEPENDENT ON PHYSICAL SENSORS** | Noise & rate of change | Evaluates sensor health, noise, drift $\rightarrow$ outputs $q_{sensor}$. |
| **Temporal Engine** | `src/fusion/temporal_intelligence.py` | `temperature_c`, `ph`, `turbidity_ntu`, `dissolved_oxygen_mg_l` | **100% DEPENDENT ON PHYSICAL SENSORS** | Multi-frame rolling window | Computes slopes per minute & trajectory $\rightarrow$ outputs $t_{temporal}$. |
| **Multimodal Fusion Engine**| `src/fusion/fusion_engine.py` | Composite threat vectors from ML, AIS, CV, and Sensors | Weighted by $q_{sensor}$ and $t_{temporal}$ | Time alignment window ($\Delta t \le 10\text{s}$) | Synthesizes all evidence into final 5-tier ecological state & actuator response. |

### Architectural Insight
Physical sensors (pH, turbidity, temperature) do **not** enter the tabular CAML Random Forest classifier. Instead, they drive **Sensor Quality**, **Temporal Trajectory**, and **Multimodal Evidence Fusion**, directly weighting whether ML predictions and visual bloom evidence are trustworthy.

---

## 17. Sensor Provenance Contract

### 17.1 Missing Telemetry Provenance
In the current repository, `payload["sensors"]` is a flat dictionary of numeric floats. When telemetry reaches `gateway.py`, the system cannot distinguish whether a reading originated from:
- A physical analog-to-digital conversion on GPIO 32/34.
- A virtual mock driver (`MockPHSensor`).
- A synthetic fallback for missing hardware (DO, Salinity).

### 17.2 Authoritative Provenance Standard
For production integration, the telemetry contract must incorporate explicit provenance metadata:
```json
{
  "schema_version": "2.0.0",
  "device_id": "AQUA_FRESH_001",
  "timestamp": "2026-09-29T10:15:30.000Z",
  "sensors": {
    "ph": 7.42,
    "turbidity_ntu": 4.80,
    "temperature_c": null,
    "dissolved_oxygen_mg_l": 8.50,
    "salinity_ppt": 0.10
  },
  "provenance": {
    "ph": "PHYSICAL_ADC",
    "turbidity_ntu": "PHYSICAL_ADC",
    "temperature_c": "UNAVAILABLE",
    "dissolved_oxygen_mg_l": "SYNTHETIC_MOCK",
 ## 18. Human Decisions Locked

The five pre-integration engineering decisions have been formally approved and locked by human authorization:

### Decision D02: Pump Relay Pin Finalization — LOCKED: GPIO 19
- **Issue:** Relay cannot occupy GPIO 27 (occupied by physical Red LED).
- **Authorized Decision:** **Approve `GPIO 19` as the dedicated pump relay control GPIO.**
- **Enforcement Rules:** `GPIO 27` remains exclusively assigned to the Red Status LED. Do NOT reuse `GPIO 27` for the relay under any circumstances.
- **Classification:** `HUMAN DECISION (LOCKED)`

### Decision D06: Turbidity Optical Staging — LOCKED: TURBIDITY_OPTICAL_DEFERRED
- **Issue:** Turbidity electrical ADC path is verified, but optical response is saturated at 0.258V.
- **Authorized Decision:** **Keep turbidity optical measurement classified as UNVERIFIED until physical trimpot is adjusted with a screwdriver.**
- **Enforcement Rules:** Do NOT claim valid NTU measurements from the current hardware state. Electrical ADC acquisition may be supported later, but telemetry must preserve the uncalibrated/unverified state.
- **Classification:** `HUMAN DECISION (LOCKED)`

### Decision D07: Driver Mode Architecture — LOCKED: HYBRID_DRIVER_MODE
- **Issue:** Hardcoded `DriverMode::PHYSICAL` crashes because missing sensors fail self-tests.
- **Authorized Decision:** **Approve `HybridDriverMode`.**
- **Enforcement Rules:**
  1. Verified physical hardware uses physical drivers (LEDs, Buzzer, pH, Turbidity raw ADC).
  2. Deferred/unavailable hardware does not prevent system startup.
  3. Unavailable/deferred sensors must retain explicit provenance/state.
  4. Do NOT silently fabricate physical measurements.
- **Classification:** `HUMAN DECISION (LOCKED)`

### Decision D09: Missing Hardware Policy — LOCKED: UNAVAILABLE_NULL
- **Issue:** Dissolved Oxygen, Salinity/TDS, GPS, and Water Pump/load are physically unavailable.
- **Authorized Decision:** **Use strict UNAVAILABLE / null semantics for physically absent sensors.**
- **Enforcement Rules:**
  1. Do NOT generate synthetic physical sensor values unless a future explicitly isolated simulation/test mode requests them.
  2. Any future synthetic value must be explicitly tagged `SIMULATED` / `SYNTHETIC`.
- **Classification:** `HUMAN DECISION (LOCKED)`

### Decision D11: Production MQTT Broker Endpoint — LOCKED: LOCAL_MOSQUITTO
- **Issue:** Microcontrollers and backend currently target disconnected brokers (`hivemq`, `192.168.1.100`, `localhost`, `InMemory`).
- **Authorized Decision:** **Use Local Mosquitto as the unified integration broker for the physical LAN integration phase.**
- **Enforcement Rules:** All devices (Main ESP32, ESP32-CAM, Gateway/Backend) will connect to the development host's local LAN IP over port 1883.
- **Classification:** `HUMAN DECISION (LOCKED)`

---

## 19. Resolved Items

The following architectural and physical contradictions have been definitively resolved with concrete evidence:

1. **Physical Board & Port Allocation:** Resolved. NodeMCU ESP-32S on `COM3` (CP210x); ESP32-CAM on `COM4` (CH340).
2. **Camera Sensor Silicon Identity:** Resolved. Sensor is **GalaxyCore GC2145** (PID `0x2145`). OV2640 hardware JPEG assumptions are invalidated.
3. **Discrete Indicator Pin Map:** Resolved. Green=`GPIO 25`, Yellow=`GPIO 26`, Red=`GPIO 27`, Buzzer=`GPIO 14`.
4. **Relay Pin Map:** Resolved & Locked. Relay=`GPIO 19`.
5. **Analog Voltage Divider Attenuation:** Resolved. Both pH and Turbidity use $33\text{ k}\Omega / 22\text{ k}\Omega$ dividers ($K = 0.400$). The $2.500\times$ software reconstruction requirement is proven.
6. **CAML ML Feature Schema:** Resolved. CAML model consumes geographical GIS and cyclic calendar coordinates; it does not take raw pH or turbidity directly.
7. **FSM Health Status Rollup Gap:** Resolved. Identified that `HAL::readAllSensors()` never rolls up `CalibratedSensor::status()`, causing static `"OK"` status.
8. **Missing Hardware Semantics:** Resolved & Locked. Strict `UNAVAILABLE` / `null` reporting.
9. **Driver Mode Policy:** Resolved & Locked. `HybridDriverMode`.
10. **Integration MQTT Broker:** Resolved & Locked. Local Mosquitto broker on development PC LAN.

---

## 20. Unresolved Items

The following items cannot be resolved by software reconciliation and require physical intervention or human input:

1. **DS18B20 Enumeration Failure:** Requires physical inspection of 1-Wire probe connections or replacement of probe.
2. **Turbidity Trimpot Adjustment:** Requires miniature screwdriver adjustment of the onboard 10k trimmer pot until clear water outputs $\sim 4.0\text{V}$ ($1.6\text{V}$ at ADC).
3. **Physical Water Pump:** Pump load circuit cannot be validated until an inductive DC pump is physically wired to relay terminal blocks.

---

## 21. Exact Preconditions for Production Integration

The transition to production software integration may only proceed after the following verification gates are satisfied:

- [x] **Gate 1: Human Approvals Signed Off:** Decisions D02, D06, D09, D07, and D11 formally locked.
- [ ] **Gate 2: PinConfig & JSON Map Synchronization:** `PinConfig.h` and `device_config.json` updated to match authoritative physical GPIO map (`pumpRelayPin = 19`, `redLedPin = 27`, etc.).
- [ ] **Gate 3: Driver Voltage Scaling Implementation:** `PHDriver.cpp` and `TurbidityDriver.cpp` updated with the verified $2.500\times$ multiplier.
- [ ] **Gate 4: HAL Status Rollup Implementation:** `HAL::readAllSensors()` updated to aggregate calibrated sensor health into `TelemetryData::sensor_status`.
- [ ] **Gate 5: ESP32-CAM Production Driver Overhaul:** `main_esp32_cam.cpp` updated with the verified GC2145 RGB565 + `frame2jpg()` PSRAM software compression pipeline.
- [ ] **Gate 6: Unified MQTT Broker Verification:** Local Mosquitto broker active and configured identically across Main ESP32, ESP32-CAM, and Python Gateway.

---

## 22. Proposed Integration Sequence

When integration is authorized, implementation must strictly follow this phased, step-by-step dependency sequence:

```
[Phase 1: Config Alignment]
  ├── Update PinConfig.h (25, 26, 27, 14, 32, 34, Relay=19, Temp=33)
  └── Update device_config.json & device_registry.json
            ↓
[Phase 2: Firmware Driver Voltage Scaling]
  ├── Update PHDriver.cpp (Add 2.5x reconstruction multiplier)
  └── Update TurbidityDriver.cpp (Add 2.5x multiplier & check limits)
            ↓
[Phase 3: Firmware HAL & FSM Alignment]
  ├── Implement HAL health rollup in HAL::readAllSensors()
  └── Implement HybridDriverMode in DriverFactory.cpp
            ↓
[Phase 4: ESP32-CAM GC2145 Pipeline]
  └── Port verified RGB565+frame2jpg PSRAM pipeline into main_esp32_cam.cpp
            ↓
[Phase 5: Unified Network & Gateway Ingestion]
  ├── Configure unified Local Mosquitto MQTT broker IP
  └── Set use_mock=False in gateway.py and verify live telemetry reception
            ↓
[Phase 6: End-to-End Multimodal Verification]
  └── Benchtop validation: Live sensor telemetry + live camera frames -> Multimodal Fusion
```

---

## Decision Table

| ID | Issue | Evidence | Authoritative Resolution | Classification / Status |
| :--- | :--- | :--- | :--- | :--- |
| **D01** | **Master GPIO Map** | Physical bring-up stages 02, 03, 05A, 08; `PinConfig.h:8-20` | Adopt physical map: Green=25, Yellow=26, Red=27, Buzzer=14, pH=32, Turb=34. Update `PinConfig.h`. | `RESOLVED` |
| **D02** | **Relay GPIO Collision** | Red LED occupies GPIO 27; Relay on 27 causes collision | Reassign Pump Relay to `GPIO 19`. GPIO 27 remains exclusively Red LED. | `LOCKED BY HUMAN DECISION` |
| **D03** | **DS18B20 Temp Probe** | Stage 04 OneWire scan found 0 devices; `DS18B20Driver.cpp:21` | Maintain probe as `DEFERRED / NOT VERIFIED`; return `-999.0f` / `null` without crashing self-test. | `RESOLVED` |
| **D04** | **pH Voltage Scaling** | Physical 33k/22k divider ($K=0.400$); `PHDriver.cpp:26`; `CalibrationProfiles.cpp:9` | Implement $2.500\times$ module voltage reconstruction in `PHDriver.cpp` before calibration. | `RESOLVED` |
| **D05** | **Turbidity Scaling** | Physical 33k/22k divider ($K=0.400$); `CalibrationMath.cpp:13` | Implement $2.500\times$ multiplier in `TurbidityDriver.cpp`; update `maxRawVolts = 5.0f`. | `RESOLVED` |
| **D06** | **Turbidity Optical State**| Stage 08 report; op-amp saturated at 0.258V; ADC valid | Optical verification DEFERRED until physical trimpot is adjusted. No valid NTU claims permitted. | `LOCKED BY HUMAN DECISION` |
| **D07** | **Driver Mode Policy** | `main.cpp:36` locked to `MOCK`; `PHYSICAL` crashes on missing sensors | Implement `HybridDriverMode` (Physical for verified, Mock/null for missing/deferred). | `LOCKED BY HUMAN DECISION` |
| **D08** | **FSM Health Semantics** | `HAL.cpp:70` sets static status; `FSM.cpp:237` needs `WARNING`/`CRITICAL` | Update `HAL::readAllSensors()` to roll up worst-case calibrated sensor validation state. | `RESOLVED` |
| **D09** | **Missing Hardware** | DO, Salinity, GPS, Pump physically absent | Strict `UNAVAILABLE` / `null` semantics. Zero silent fabrication of synthetic values. | `LOCKED BY HUMAN DECISION` |
| **D10** | **Camera Silicon Model** | PID `0x2145` detected; `main_esp32_cam.cpp:101` fails with `0x0106` | Overhaul `main_esp32_cam.cpp` with verified RGB565 + PSRAM `frame2jpg()` compression. | `RESOLVED` |
| **D11** | **MQTT Broker Target** | Disconnected hosts (`hivemq`, `192.168.1.100`, `localhost`, `InMemory`) | Adopt `Local Mosquitto` broker on development host LAN IP. | `LOCKED BY HUMAN DECISION` |
| **D12** | **Model Feature Contract**| `model_registry.json`; `gateway.py:436` | CAML consumes GIS/time features; physical sensors drive Quality, Trajectory, and Fusion. | `RESOLVED` |
| **D13** | **Sensor Provenance** | Flat sensor dictionary in telemetry schema lacks source metadata | Add explicit `sensor_provenance` metadata to telemetry payloads and schemas. | `FUTURE IMPLEMENTATION REQ` |

---

*(End of Contract. Human Engineering Decisions Locked. Read-only stop condition preserved. No code, firmware, or hardware modified.)*
