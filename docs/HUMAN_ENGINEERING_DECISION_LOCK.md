# AquaSentinel-AI — Human Engineering Decision Lock & Implementation Contract

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems (AquaSentinel-AI)  
**Milestone:** Pre-Integration Decision Freeze & Architecture Lock  
**Document Status:** AUTHORITATIVE HARDWARE & SOFTWARE INTEGRATION SPECIFICATION  
**Reference Document:** [`docs/PRE_INTEGRATION_CONFLICT_RESOLUTION.md`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/docs/PRE_INTEGRATION_CONFLICT_RESOLUTION.md)  
**Governing Standard:** Strict Forensic Traceability (`VERIFIED FACT`, `HUMAN DECISION`, `IMPLEMENTATION REQUIREMENT`, `FUTURE VALIDATION`)  

---

## A. Purpose

This document formally locks the five critical human engineering decisions authorized following the repository-wide forensic audit and architecture reconciliation. It serves as the unalterable integration contract governing the transition from physical bench bring-up to production software integration.

### Absolute Boundary Rules
1. **Scope Freeze:** All five architectural decisions detailed herein are frozen. No silent deviation, assumption-based reinterpretation, or undocumented pin reallocations are permitted during implementation.
2. **Read-Only Preservation:** This document concludes the pre-integration governance phase. Zero production code, firmware, or hardware configurations have been modified during this decision-lock session.
3. **Traceability:** Every technical requirement is directly bound to bench verification evidence, physical silicon constraints, or explicitly authorized human decisions.

---

## B. Decision D02 — Relay GPIO19

### 1. Context & Forensic Conflict
During the initial hardware design, `GPIO 27` was assigned to the aerator pump relay in `PinConfig.h` and `device_config.json`. However, during physical bench bring-up (Stage 02), `GPIO 27` was physically wired to the **Red Status LED** via a 330 Ω series resistor to common ground. Toggling `GPIO 27` as a relay would actuate the Red LED or cause an electrical overload across the LED network.

### 2. Forensic Classifications
- **VERIFIED FACT:** Physical `GPIO 27` is occupied by the Red Status LED. Physical bring-up demonstrated that `GPIO 19` is a standard digital IO pin with push-pull driving capability, no boot-strapping restrictions, and no Wi-Fi/ADC2 resource conflicts.
- **HUMAN DECISION:** **Approve `GPIO 19` as the dedicated pump relay control GPIO.** `GPIO 27` remains exclusively assigned to the Red Status LED.
- **IMPLEMENTATION REQUIREMENT:**
  1. `firmware/include/config/PinConfig.h` line 19 must be updated from `int pumpRelayPin = 27;` to `int pumpRelayPin = 19;`.
  2. `config/device_config.json` line 31 must be updated from `"pump_relay": 27` to `"pump_relay": 19`.
  3. Under NO circumstances shall `GPIO 27` be multiplexed, shared, or driven by the relay driver.
- **FUTURE VALIDATION:** Validate that driving `GPIO 19` HIGH engages the optocoupled relay channel without altering the state of the Red Status LED on `GPIO 27`.

---

## C. Decision D06 — Turbidity Optical Verification Deferred

### 1. Context & Forensic Conflict
The analog turbidity interface board is powered from 5V and connected to `GPIO 34` through a $33\text{ k}\Omega / 22\text{ k}\Omega$ voltage divider ($K = 0.400$). While the electrical ADC circuit is verified and safe, the onboard LM358 operational amplifier was discovered biased at its low saturation rail ($V_{OUT} \approx 0.258\text{ V}$, $V_{ADC} \approx 0.103\text{ V}$). The module cannot optically discriminate clean water from turbid water until its multi-turn trimpot is mechanically adjusted.

### 2. Forensic Classifications
- **VERIFIED FACT:** The electrical ADC signal path, voltage attenuation network, and ESP32 silicon safety limits on `GPIO 34` are verified. The optical liquid response is non-functional in its current trimmer potentiometer state.
- **HUMAN DECISION:** **Keep turbidity optical measurement classified as UNVERIFIED until physical trimpot is adjusted with a screwdriver. Do NOT claim valid NTU measurements from the current hardware state.**
- **IMPLEMENTATION REQUIREMENT:**
  1. Electrical ADC window sampling and raw voltage acquisition may be integrated into firmware.
  2. Telemetry must report turbidity raw voltage or flag `turbidity_status = "UNVERIFIED_UNCALIBRATED"`.
  3. Downstream AI models, temporal engines, and fusion pipelines must NOT ingest current turbidity readings as ground-truth NTU.
  4. The DFRobot quadratic conversion formula ($NTU = -1120.4 V^2 + 5742.3 V - 4352.9$) must not be treated as calibrated truth until mechanical trimmer adjustment is completed.
- **FUTURE VALIDATION:** Following physical screwdriver adjustment of the 10k trimmer pot, perform bench verification comparing clear water ($V_{OUT} \approx 4.0\text{V} - 4.2\text{V}$, $V_{ADC} \approx 1.6\text{V} - 1.7\text{V}$) against a known turbid milk suspension.

---

## D. Decision D07 — HybridDriverMode

### 1. Context & Forensic Conflict
Production firmware (`firmware/src/main.cpp:36`) hardcodes `ACTIVE_MODE = DriverMode::MOCK`. Enabling `DriverMode::PHYSICAL` across the entire device causes immediate boot failures:
- Missing hardware probes (DO, Salinity, GPS, Temp) fail self-tests.
- `HAL::runSelfTest()` returns `false`, setting `_sensorStatus = "FAULT"`.
- The Finite State Machine transitions to `State::FAULT` and enters a permanent recovery bootloop.

### 2. Forensic Classifications
- **VERIFIED FACT:** Certain subsystems exist physically and are verified (LEDs, Buzzer, pH, Turbidity ADC, ESP32-CAM), while others are deferred (DS18B20 Temp) or physically missing (DO, Salinity, GPS, Water Pump).
- **HUMAN DECISION:** **Approve `HybridDriverMode`. Verified physical hardware shall use physical drivers. Deferred or unavailable hardware shall not prevent system startup and must retain explicit provenance.**
- **IMPLEMENTATION REQUIREMENT:**
  1. Refactor `firmware/src/DriverFactory.cpp` to support `DriverMode::HYBRID`.
  2. Physical Drivers instantiated:
     - `PHDriver` (GPIO 32, with 2.5x reconstruction)
     - `TurbidityDriver` (GPIO 34, raw ADC mode)
     - `LEDDriver` (Green=25, Yellow=26, Red=27)
     - `BuzzerDriver` (GPIO 14)
  3. Mock / Passive Drivers instantiated:
     - `DS18B20Driver` / `MockTemperatureSensor` (deferred, reports `-999.0f`)
     - `DODriver` / `MockDOSensor` (missing hardware, reports `-999.0f` / `null`)
     - `SalinityDriver` / `MockSalinitySensor` (missing hardware, reports `-999.0f` / `null`)
     - `GPSSensor` / `MockGPSSensor` (missing hardware, reports default coordinates)
     - `RelayDriver` / `MockRelay` (missing pump load)
  4. System self-test must evaluate physical components strictly, allowing operational startup without failing on deferred/mock components.
- **FUTURE VALIDATION:** Boot the Main ESP32 in `HYBRID` mode on `COM3`. Confirm LED cycling, buzzer chirps, live ADC polling on GPIO 32/34, and stable transition to `State::MONITORING`.

---

## E. Decision D09 — UNAVAILABLE / null Missing Hardware Policy

### 1. Context & Forensic Conflict
Dissolved Oxygen (DO), Salinity/TDS, GPS, and the physical Aerator Pump are completely absent from the bench. Previously, simulated components fabricated synthetic numbers (e.g. `salinity = 0.5 ppt`, `DO = 8.5 mg/L`), creating the false impression that real physical sensors were providing data.

### 2. Forensic Classifications
- **VERIFIED FACT:** No physical transducers exist for DO, Salinity, GPS, or Pump.
- **HUMAN DECISION:** **Use strict UNAVAILABLE / null semantics for physically absent sensors. Do NOT generate synthetic physical sensor values unless a future explicitly isolated simulation/test mode requests them. Any future synthetic value must be explicitly tagged `SIMULATED` / `SYNTHETIC`.**
- **IMPLEMENTATION REQUIREMENT:**
  1. Firmware `TelemetryData` representation: Missing float values must be populated with standard `-999.0f` sentinels or omitted from JSON output.
  2. Gateway & Backend JSON Schema: Missing sensors must deserialize as `null`:
     ```json
     {
       "sensors": {
         "ph": 7.42,
         "turbidity_ntu": null,
         "temperature_c": null,
         "dissolved_oxygen_mg_l": null,
         "salinity_ppt": null
       }
     }
     ```
  3. `src/iot/sensor_quality.py`: Update `SensorQualityEvaluator` to dynamically ignore `null` metrics when calculating overall sensor quality $q_{sensor}$.
  4. `src/fusion/multimodal_alignment.py`: Mark missing sensor modalities as `ModalityState.MISSING` rather than `ModalityState.DEGRADED`.
  5. Never record synthetic values into SQLite `event_store.db` as ground truth.
- **FUTURE VALIDATION:** Transmit a live MQTT packet from the Main ESP32. Confirm Gateway validates the packet without crashing and logs `null` for missing channels.

---

## F. Decision D11 — Local Mosquitto

### 1. Context & Forensic Conflict
Four different broker endpoints were discovered in code: `broker.hivemq.com` (Main ESP32), `192.168.1.100` (ESP32-CAM), `localhost` (`device_config.json`), and `InMemoryMQTTBroker` (`gateway.py`). Hardware cannot communicate wirelessly without agreeing on a single network target.

### 2. Forensic Classifications
- **VERIFIED FACT:** Both microcontrollers (NodeMCU ESP-32S and ESP32-CAM) possess 802.11 b/g/n Wi-Fi radios. The development host can host an Eclipse Mosquitto broker on standard port 1883.
- **HUMAN DECISION:** **Use Local Mosquitto as the unified integration broker for the physical LAN integration phase.**
- **IMPLEMENTATION REQUIREMENT:**
  1. All physical hardware nodes and backend services must target the development machine's static LAN IP (or local Wi-Fi hotspot IP) on port `1883`.
  2. Public cloud brokers (e.g. HiveMQ) are strictly disallowed during physical integration to prevent internet latency, external downtime, and public topic snooping.
  3. `src/iot/gateway.py` must be configured with `use_mock=False` to bind to the live Mosquitto instance via `paho-mqtt`.
- **FUTURE VALIDATION:** Start Mosquitto on the PC. Connect Main ESP32 (`COM3`) and ESP32-CAM (`COM4`) to the same Wi-Fi SSID. Verify bi-directional MQTT subscribe and publish telemetry.

---

## G. Authoritative Physical Hardware Baseline

The physical hardware baseline is frozen as follows:

| Component | Physical Identity | Port / Bus | Power Rail | Electrical Protection | Verified Operational Baseline |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Main MCU** | NodeMCU ESP-32S (ESP32-D0WD-V3) | `COM3` (CP210x) | USB 5V | On-board 3.3V LDO | Dual Xtensa cores @ 240MHz, FreeRTOS active |
| **Optical Node** | AI-Thinker ESP32-CAM + MB | `COM4` (CH340) | USB 5V | 4MB External PSRAM | ESP32-D0WD-V3 @ 240MHz, PSRAM verified |
| **Camera Sensor** | GalaxyCore GC2145 (PID `0x2145`)| DVP Ribbon | 3.3V/1.8V LDO | Software JPEG via PSRAM| Frame capture verified (RGB565+JPEG) |
| **Green LED** | 5mm Green Diode | `GPIO 25` | 3.3V Logic | 330 Ω series resistor | Verified Active (Stage 02) |
| **Yellow LED** | 5mm Yellow Diode | `GPIO 26` | 3.3V Logic | 330 Ω series resistor | Verified Active (Stage 02) |
| **Red LED** | 5mm Red Diode | `GPIO 27` | 3.3V Logic | 330 Ω series resistor | Verified Active (Stage 02) |
| **Buzzer** | MB12A05 2-Pin Buzzer | `GPIO 14` | 3.3V Logic | Negative to Common GND | Verified Active (Stage 03) |
| **pH Module** | PH-4502C + Glass Electrode | `GPIO 32` | ESP32 5V (VIN) | 33kΩ / 22kΩ divider | Electrically Verified (Stage 05A) |
| **Turbidity** | Optical Board | `GPIO 34` (GPI) | ESP32 5V (VIN) | 33kΩ / 22kΩ divider | ADC Verified; Optical Pending (Stage 08) |
| **Temp Sensor** | DS18B20 Waterproof Probe | `GPIO 33` | 3.3V Rail | 4.7 kΩ pull-up to 3.3V | 0 ROM Devices (Stage 04, Deferred) |
| **Relay** | SRD-05VDC-SL-C 5V Relay | `GPIO 19` (Frozen)| 5V Rail | Optocoupled Isolation | Hardware Exists; Load Unvalidated |
| **Missing HW** | DO, Salinity, GPS, Water Pump | N/A | N/A | N/A | PHYSICALLY ABSENT (Strict null semantics)|

---

## H. Authoritative GPIO Map

The authoritative ESP32 pin assignments are locked as follows:

```
========================================================================================
PIN      SILICON DOMAIN      DIRECTION     PERIPHERAL ASSIGNMENT    STATUS
========================================================================================
GPIO 14  Digital IO (ADC2)   Output        Acoustic Alarm Buzzer    CONFIRMED & VERIFIED
GPIO 19  Digital IO (VSPI)   Output        Aerator Pump Relay       CONFIRMED (LOCKED D02)
GPIO 25  Digital IO (ADC2)   Output        Green Status LED         CONFIRMED & VERIFIED
GPIO 26  Digital IO (ADC2)   Output        Yellow Status LED        CONFIRMED & VERIFIED
GPIO 27  Digital IO (ADC2)   Output        Red Status LED           CONFIRMED & VERIFIED
GPIO 32  Analog (ADC1_CH4)   Input         Analog pH Module (Po)    CONFIRMED & VERIFIED
GPIO 33  Digital (ADC1_CH5)  In/Out        DS18B20 1-Wire Temp      RESERVED (DEFERRED D03)
GPIO 34  GPI Only (ADC1_CH6) Input         Turbidity Board (OUT)    CONFIRMED (LOCKED D06)
========================================================================================
```

---

## I. Sensor Verification States

Every sensor is governed by an explicit state contract:

```
  pH Sensor          ──► [ELECTRICALLY_VERIFIED] ──► Calibrated Accuracy Pending
  Turbidity Sensor   ──► [ADC_VERIFIED]          ──► Optical Transmittance UNVERIFIED (D06)
  DS18B20 Temp Probe ──► [DEFERRED_UNVERIFIED]   ──► Reports -999.0f / null
  Dissolved Oxygen   ──► [PHYSICALLY_ABSENT]     ──► Strict null / UNAVAILABLE (D09)
  Salinity / TDS     ──► [PHYSICALLY_ABSENT]     ──► Strict null / UNAVAILABLE (D09)
  GPS Module         ──► [PHYSICALLY_ABSENT]     ──► Strict null / UNAVAILABLE (D09)
  Aerator Pump       ──► [LOAD_UNVALIDATED]      ──► Actuation Logic Only
```

---

## J. Camera GC2145 Contract

### 1. Hardware Silicon Identity
The camera module is conclusively identified as **GalaxyCore GC2145** (PID `0x2145`), DVP interface. It possesses **no internal hardware JPEG compression engine**.

### 2. Firmware Pipeline Contract
```
[GC2145 Silicon] ──► 16-bit RGB565 (224x224) ──► PSRAM Framebuffer ──► frame2jpg() in PSRAM ──► Standard JPEG ──► Base64 MQTT
```
- **Driver Configuration:** `config.pixel_format = PIXFORMAT_RGB565`
- **Resolution:** `FRAMESIZE_224X224` (Native MobileNetV3 tensor shape)
- **Buffer Storage:** `CAMERA_FB_IN_PSRAM` (Frame buffer count = 2)
- **JPEG Encoding:** Call `frame2jpg()` (`img_converters.h`) in PSRAM with JPEG quality 80.
- **Publish Topic:** `aquatic/AQUA_FRESH_001/camera/raw`

---

## K. Voltage-Divider Contract

### 1. Circuit Topology
Both pH (GPIO 32) and Turbidity (GPIO 34) utilize an identical precision voltage divider:
- Upper Resistor ($R_{top}$): $33\text{ k}\Omega$ (1% metal film)
- Lower Resistor ($R_{bottom}$): $22\text{ k}\Omega$ (1% metal film)
- Voltage Division Ratio:
  $$K = \frac{22\text{ k}\Omega}{33\text{ k}\Omega + 22\text{ k}\Omega} = \frac{22}{55} = 0.400$$

### 2. Software Reconstruction Contract
Because the ADC measures the attenuated voltage ($V_{ADC} = 0.400 \times V_{module}$), the physical driver layer must apply the inverse multiplier:
$$\text{Reconstruction Factor} = \frac{1}{K} = \frac{1}{0.400} = \mathbf{2.500}$$
- **`PHDriver.cpp` Contract:**
  $$V_{module} = \left(\text{rawAdc} \times \frac{3.3}{4095.0}\right) \times 2.500$$
- **`TurbidityDriver.cpp` Contract:**
  $$V_{OUT} = \left(\text{rawAdc} \times \frac{3.3}{4095.0}\right) \times 2.500$$
- **Calibration Engine Contract:** `CalibrationProfiles.cpp` and `CalibrationMath.cpp` evaluate equations against the reconstructed 5V domain ($V_{module}$ and $V_{OUT}$), preserving semantic validity across all layers.

---

## L. Explicitly Forbidden Assumptions

The following assumptions are strictly prohibited during implementation:

1. **NO OV2640 Assumptions:** Never assume native hardware JPEG encoding on the ESP32-CAM.
2. **NO Direct 5V ADC Connections:** Never connect un-attenuated 5V analog module outputs to ESP32 GPIOs.
3. **NO Fabricated Sensor Data:** Never invent plausible floating-point values for missing hardware (DO, Salinity, GPS, Temp).
4. **NO Silent Pin Reuse:** Never drive `GPIO 27` for relay operations.
5. **NO Public Cloud Telemetry:** Never broadcast unencrypted bench telemetry to public cloud brokers during bring-up.
6. **NO Uncalibrated NTU Claims:** Never describe current turbidity readings as valid physical NTU.

---

## M. Preconditions for Implementation

Implementation may begin ONLY after satisfying the following checklist:

- [x] Pre-integration conflict resolution audit complete.
- [x] Five human engineering decisions formally locked.
- [ ] Dedicated physical branch created (`git checkout -b feature/hardware-integration`).
- [ ] Local Mosquitto broker installed and running on host machine port 1883.
- [ ] Multimeter / tool check confirmed for 3.3V rail stability under Wi-Fi load.

---

## N. Implementation Gates

Implementation must proceed strictly sequentially through six authorization gates:

```
[GATE 1: CONFIGURATION SYNCHRONIZATION]
  ├── Synchronize PinConfig.h (Relay=19, Red=27, Green=25, Yellow=26, Buzzer=14, pH=32, Turb=34)
  └── Synchronize device_config.json and device_registry.json
            ↓
[GATE 2: FIRMWARE DRIVER VOLTAGE SCALING]
  ├── Implement 2.500x multiplier in PHDriver.cpp
  └── Implement 2.500x multiplier in TurbidityDriver.cpp (raw ADC mode)
            ↓
[GATE 3: HAL HEALTH ROLLUP & HYBRID MODE]
  ├── Update HAL::readAllSensors() to aggregate calibrated sensor status
  └── Implement HybridDriverMode in DriverFactory.cpp
            ↓
[GATE 4: ESP32-CAM PRODUCTION OVERHAUL]
  └── Port verified GC2145 RGB565 + frame2jpg() PSRAM pipeline into main_esp32_cam.cpp
            ↓
[GATE 5: LOCAL NETWORK & GATEWAY INGESTION]
  ├── Configure local LAN IP for Mosquitto across both MCUs
  └── Set use_mock=False in gateway.py; verify live MQTT telemetry
            ↓
[GATE 6: BENCHTOP MULTIMODAL VALIDATION]
  └── End-to-end test: Live pH/turbidity ADC + live GC2145 frames -> Multimodal Fusion Engine
```

---

## O. Change-Control Rules

1. Any proposed modification to GPIO pin assignments requires a formal revision of this document.
2. If the physical DS18B20 probe is repaired or replaced, a dedicated isolated bring-up verification must be executed before transitioning its status to `VERIFIED`.
3. If the turbidity trimmer potentiometer is mechanically adjusted, Stage 08 verification must be re-run and documented before enabling NTU conversion in production firmware.

---

## Machine-Readable Decision Lock Table

```text
========================================================================================
DECISION ID   LOCKED VALUE                   SEMANTIC DESCRIPTION
========================================================================================
D02           GPIO19                         Dedicated Aerator Pump Relay GPIO
D06           TURBIDITY_OPTICAL_DEFERRED     Optical NTU unverified pending trimpot adjustment
D07           HYBRID_DRIVER_MODE             Physical drivers for verified HW; mock for rest
D09           UNAVAILABLE_NULL               Strict null semantics for absent hardware
D11           LOCAL_MOSQUITTO                Unified Local Mosquitto Broker on LAN IP
========================================================================================
```

---

*(End of Decision Lock Document. All decisions frozen. Read-only audit preserved.)*
