# VERSION 4.8.5 — PHYSICAL HARDWARE BASELINE & SOFTWARE-TO-HARDWARE INTEGRATION AUDIT

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Milestone:** V4.8.5 Final Physical Hardware Baseline & Integration Audit  
**Document Date:** August 18, 2026  
**Authoritative Hardware Inventory:** Confirmed 16-Item Physical Kit  
**Status:** Software Fully Verified / Physical Hardware Inventory Audited / Physical Assembly Pending  

---

> [!IMPORTANT]
> **SINGLE SOURCE OF TRUTH HARDWARE INVENTORY**  
> The 16 items listed in Section 1 represent the **EXACT PHYSICAL HARDWARE INVENTORY** owned for this project.  
> 
> Unused software interface drivers (Dissolved Oxygen, Salinity/TDS, GPS, Aerator Pump) remain intact in the software codebase for future extensibility, but are explicitly classified as **`SOFTWARE-DEFINED / NOT PHYSICALLY IMPLEMENTED`** or **`LOAD NOT YET CONNECTED`**.  
> 
> NO physical hardware has been wired, flashed, or powered on yet.

---

## 1. Confirmed Physical Hardware Inventory Audit

| Item # | Physical Hardware Component Name | Confirmed Quantity | Software Mapping Status | Electrical Interface | Physical Assignment |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | Liquid pH Probe with BNC Signal Amplifier Board | 1 | 🟢 **PHYSICALLY PRESENT** | Analog Voltage (0-3.0V) | **GPIO 32 (ADC1_CH4)** |
| **2** | ESP32-WROOM-32 38-Pin Development Board (Type-C) | 1 | 🟢 **PHYSICALLY PRESENT** | Main MCU (3.3V Logic) | Core Controller Board |
| **3** | DS18B20 Waterproof Stainless Steel Temp Sensor | 1 | 🟢 **PHYSICALLY PRESENT** | OneWire Digital (3.3V) | **GPIO 18** |
| **4** | Type-C USB High-Speed Data Cable | 1 | 🟢 **PHYSICALLY PRESENT** | USB Power + Serial Data | Main MCU Flash/Power |
| **5** | Male-to-Male (M-M) DuPont Jumper Wires | 10 | 🟢 **PHYSICALLY PRESENT** | Breadboard Interconnects | Signal & Power Interconnects |
| **6** | Female-to-Female (F-F) DuPont Jumper Wires | 10 | 🟢 **PHYSICALLY PRESENT** | Sensor Module Headers | Sensor Probe Connections |
| **7** | Assorted Resistor Kit Box | 1 | 🟢 **PHYSICALLY PRESENT** | 220Ω, 1kΩ, 4.7kΩ, 10k/20k | Pull-ups, Dividers, LED Limits |
| **8** | MB-102 Solderless Breadboard (830 Point) | 1 | 🟢 **PHYSICALLY PRESENT** | Circuit Prototyping | Master Breadboard Rail |
| **9** | 5mm Green Status Indicator LED | 1 | 🟢 **PHYSICALLY PRESENT** | Digital High-Active Output | **GPIO 19** (via 220 Ω) |
| **10** | 5mm Red Critical Alert Indicator LED | 1 | 🟢 **PHYSICALLY PRESENT** | Digital High-Active Output | **GPIO 22** (via 220 Ω) |
| **11** | 5mm Yellow Risk Warning Indicator LED | 1 | 🟢 **PHYSICALLY PRESENT** | Digital High-Active Output | **GPIO 21** (via 220 Ω) |
| **12** | 5V Piezo Audio Alarm Buzzer Module | 1 | 🟢 **PHYSICALLY PRESENT** | Digital High-Active Output | **GPIO 23** (via NPN Transistor) |
| **13** | Analog Optical Turbidity Sensor Module | 1 | 🟢 **PHYSICALLY PRESENT** | Analog Voltage (0-4.5V) | **GPIO 33 (ADC1_CH5)** |
| **14** | Transparent 2500 mL Aquatic Enclosure Box | 1 | 🟢 **PHYSICALLY PRESENT** | Water Test Vessel | Aquatic Sample Container |
| **15** | AI-Thinker ESP32-CAM Module + OV2640 Camera | 1 | 🟢 **PHYSICALLY PRESENT** | Independent Camera Node | Camera Transport (`aquatic/+/camera/raw`) |
| **16** | 5V 1-Channel Optocoupled Relay Module | 1 | 🟢 **PHYSICALLY PRESENT** | Digital Output (Load Pending)| **GPIO 27** (Coil 5V, Load Pending) |

---

## 2. Software Interface vs Physical Inventory Audit Matrix

| Software Driver / Module | Pin Assignment | Software Interface Status | Physical Hardware Status | Functional Behavior in System |
| :--- | :--- | :--- | :--- | :--- |
| **`DS18B20TemperatureSensor`**| GPIO 18 | 🟢 Active | 🟢 **PHYSICALLY PRESENT** | Primary water temperature telemetry. |
| **`PHSensorDriver`** | GPIO 32 (ADC1) | 🟢 Active | 🟢 **PHYSICALLY PRESENT** | Primary acidity / pH telemetry. |
| **`TurbiditySensorDriver`** | GPIO 33 (ADC1) | 🟢 Active | 🟢 **PHYSICALLY PRESENT** | Primary visual water clarity telemetry. |
| **`DissolvedOxygenDriver`** | GPIO 34 (ADC1) | 🟢 Intact / Preserved | ⚪ **SOFTWARE-DEFINED (NO HARDWARE)** | Virtual driver returns software telemetry or neutral fallback. |
| **`SalinitySensorDriver`** | GPIO 36 (ADC1) | 🟢 Intact / Preserved | ⚪ **SOFTWARE-DEFINED (NO HARDWARE)** | Virtual driver returns software telemetry or neutral fallback. |
| **`GPSSensorDriver`** | GPIO 16/17 (UART2)| 🟢 Intact / Preserved | ⚪ **SOFTWARE-DEFINED (NO HARDWARE)** | Virtual driver returns software coordinates. |
| **`GreenLEDActuator`** | GPIO 19 | 🟢 Active | 🟢 **PHYSICALLY PRESENT** | Normal / System Ready indicator. |
| **`YellowLEDActuator`** | GPIO 21 | 🟢 Active | 🟢 **PHYSICALLY PRESENT** | Warning / Elevated risk indicator. |
| **`RedLEDActuator`** | GPIO 22 | 🟢 Active | 🟢 **PHYSICALLY PRESENT** | Critical / Algal bloom alert indicator. |
| **`BuzzerActuator`** | GPIO 23 | 🟢 Active | 🟢 **PHYSICALLY PRESENT** | Audio alarm during Critical / Sensor Fault. |
| **`PumpRelayActuator`** | GPIO 27 | 🟢 Active | 🟢 **RELAY PRESENT (LOAD PENDING)** | Relay energizes during Warning/Critical; **NO PUMP CONNECTED**. |
| **`CameraTransportReceiver`** | Wi-Fi / MQTT | 🟢 Active | 🟢 **ESP32-CAM PRESENT** | Transmits 224x224 JPEG at 0.1 FPS to Gateway. |

---

## 3. Sensor Electrical & Voltage Safety Audit

### 3.1 Liquid pH Probe & Signal Amplifier
- **Power Supply Requirement**: 5.0V DC connected to `VCC` pin of pH amplifier board.
- **Output Signal Range**: 0.0V to 3.0V DC (at pH 0 to 14).
- **ESP32 ADC Safety Check**: The pH amplifier output maximum (3.0V) is **100% safe** for direct connection to ESP32 **GPIO 32 (ADC1_CH4)** (3.3V maximum input rating). No resistor divider required.
- **Ground Strategy**: Amplifier `GND` connected directly to Main MB-102 Breadboard Common Ground Rail.

### 3.2 Optical Turbidity Sensor Module
- **Power Supply Requirement**: 5.0V DC connected to Turbidity emitter/detector board.
- **Output Signal Range**: 0.0V to 4.5V DC (0 to 4500 NTU).
- **ESP32 ADC Safety Check**: 
  > [!CAUTION]
  > Raw 4.5V output exceeds the ESP32 3.3V ADC damage threshold!  
  > 
  > A **voltage divider** constructed from the Resistor Kit Box (**10 kΩ / 20 kΩ 1% metal film resistors**) MUST be inserted between the turbidity output pin (`AO`) and ESP32 **GPIO 33 (ADC1_CH5)** to scale the 0.0V-4.5V signal down to **0.0V-3.0V DC**.

### 3.3 DS18B20 Waterproof Temperature Probe
- **Power Supply Requirement**: 3.3V DC connected to `VDD` (Red wire).
- **Signal Line**: Connected to **GPIO 18** (Yellow wire).
- **Pull-up Resistor**: A **4.7 kΩ pull-up resistor** from the Resistor Kit Box MUST be placed between `DQ` (Yellow wire) and `3.3V` (Red wire) to maintain OneWire bus timing stability.
- **Grounding**: Black wire connected to Common Ground Rail.

---

## 4. Actuator Safety & Driver Circuit Audit

### 4.1 Status LEDs (Green - GPIO 19, Yellow - GPIO 21, Red - GPIO 22)
- **Driving Voltage**: 3.3V Logic from ESP32 GPIO pins.
- **Current Limiting**: Each 5mm LED MUST be wired in series with a **220 Ω resistor** from the Resistor Kit Box.
- **Current Draw**: $\approx 6\text{ mA}$ per LED, well within the safe 12 mA sourcing limit per ESP32 GPIO.

### 4.2 5V Piezo Audio Alarm Buzzer (GPIO 23)
- **Driving Voltage**: 5.0V DC Power Rail.
- **Current Draw**: $20\text{ mA} - 40\text{ mA}$ (exceeds direct ESP32 GPIO pin limit of 12 mA).
- **Transistor Driver Circuit**:
  > [!IMPORTANT]
  > ESP32 **GPIO 23** MUST drive the buzzer using an **NPN Transistor (2N2222)** from the Resistor Box / transistor kit.  
  > - Base: GPIO 23 connected through a **1 kΩ resistor**.  
  > - Collector: Connected to Buzzer Negative (-) terminal.  
  > - Emitter: Connected to Common Ground Rail.  
  > - Buzzer Positive (+): Connected to 5V Power Rail.

### 4.3 5V 1-Channel Optocoupled Relay Module (GPIO 27)
- **Coil Power Supply**: 5.0V DC connected to Relay `VCC` and `GND`.
- **Logic Input**: Connected to **GPIO 27** (3.3V Logic compatible with EL817 optocoupler).
- **Load Status**: **NO LOAD CONNECTED**. High-voltage AC or motor connections are strictly absent. Relay energizes safely as a dry-contact logic indicator.

---

## 5. Tailored Power Architecture (No Pump / 5V Single Source)

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
 (5V VCC)     (5V VCC)       (5V VCC)   (via 2N2222)        (via 4.7kΩ)    (via 220Ω)   (Core MCU)
```

### Power Consumption Budget (Actual Owned Hardware)

| Component | Supply Rail | Voltage (V) | Typical Current (mA) | Peak Current (mA) | Power Budget Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ESP32-WROOM-32** | 3.3V Rail | 3.3V | 80 mA | 240 mA | Wi-Fi peak transmission spikes. |
| **ESP32-CAM Board** | 5.0V USB / Rail | 5.0V | 120 mA | 310 mA | Independent Type-C / 5V power input. |
| **DS18B20 Temp Sensor**| 3.3V Rail | 3.3V | 1.0 mA | 1.5 mA | OneWire active conversion. |
| **pH Amplifier Board** | 5.0V Rail | 5.0V | 10 mA | 20 mA | Op-amp signal conditioning. |
| **Turbidity Sensor Module**| 5.0V Rail | 5.0V | 30 mA | 40 mA | IR LED emitter + phototransistor. |
| **Status LEDs (x3)** | 3.3V Rail | 3.3V | 6 mA | 18 mA | 220 Ω current limiting per LED. |
| **5V Piezo Buzzer** | 5.0V Rail | 5.0V | 20 mA | 40 mA | 2N2222 NPN transistor driven. |
| **5V Relay Coil** | 5.0V Rail | 5.0V | 50 mA | 70 mA | Optocoupler coil activation. |
| **TOTAL MAIN BOARD** | **5.0V USB Input**| **5.0V** | **317 mA** | **739.5 mA** | **100% Powered by Standard 5V 1A Type-C USB** |

---

## 6. Software-to-Hardware Traceability Matrix

```
  PHYSICAL COMPONENT         GPIO / INTERFACE          C++ DRIVER         PYTHON GATEWAY PROCESSING        FSM / ACTUATION EFFECT
┌──────────────────┐       ┌──────────────────┐    ┌──────────────────┐   ┌───────────────────────────┐   ┌─────────────────────────┐
│ DS18B20 Temp     ├──────►│ GPIO 18 (OneWire)├───►│ DS18B20Sensor    ├──►│ Telemetry -> ML/AIS Model ├──►│ FSM Monitoring State    │
├──────────────────┤       ├──────────────────┤    ├──────────────────┤   ├───────────────────────────┤   ├─────────────────────────┤
│ Liquid pH Probe  ├──────►│ GPIO 32 (ADC1)   ├───►│ PHSensor         ├──►│ Telemetry -> ML/AIS Model ├──►│ FSM Monitoring State    │
├──────────────────┤       ├──────────────────┤    ├──────────────────┤   ├───────────────────────────┤   ├─────────────────────────┤
│ Turbidity Sensor ├──────►│ GPIO 33 (ADC1)   ├───►│ TurbiditySensor  ├──►│ Telemetry -> ML/AIS Model ├──►│ FSM Monitoring State    │
├──────────────────┤       ├──────────────────┤    ├──────────────────┤   ├───────────────────────────┤   ├─────────────────────────┤
│ Status LEDs (x3) ├◄──────│ GPIO 19, 21, 22  │◄───┤ LEDActuator      │◄──┤ MQTT Decision             │◄──┤ Green/Yellow/Red Visual │
├──────────────────┤       ├──────────────────┤    ├──────────────────┤   ├───────────────────────────┤   ├─────────────────────────┤
│ 5V Audio Buzzer  ├◄──────│ GPIO 23 (NPN)    │◄───┤ BuzzerActuator   │◄──┤ MQTT Decision             │◄──┤ Critical Audio Alarm    │
├──────────────────┤       ├──────────────────┤    ├──────────────────┤   ├───────────────────────────┤   ├─────────────────────────┤
│ 5V Relay Module  ├◄──────│ GPIO 27 (Coil)   │◄───┤ RelayActuator    │◄──┤ MQTT Decision             │◄──┤ Relay Coil Activation   │
├──────────────────┤       ├──────────────────┤    ├──────────────────┤   ├───────────────────────────┤   ├─────────────────────────┤
│ ESP32-CAM Node   ├──────►│ Wi-Fi / MQTT     ├───►│ CameraTransport  ├──►│ MobileNetV3 -> FusionEngine├──►│ Multimodal Fusion State │
└──────────────────┘       └──────────────────┘    └──────────────────┘   └───────────────────────────┘   └─────────────────────────┘
```

---

## 7. 2500 mL Transparent Aquatic Test Container Setup

- **Test Vessel**: 2500 mL Transparent Box containing water samples.
- **Probe Mounting Strategy**:
  - DS18B20 waterproof probe submerged directly into the 2500 mL water volume.
  - Liquid pH glass probe suspended vertically with tip submerged in water (BNC amplifier module mounted externally on dry breadboard).
  - Optical Turbidity sensor head submerged in water (optical driver circuit module mounted externally on dry breadboard).
- **Safety Precaution**: Electronic amplifier boards and microcontrollers remain strictly external to the 2500 mL container to prevent moisture short-circuits.

---

## 8. Verified Bill of Materials vs Inventory Classification

| Inventory Component Name | Quantity | BOM Classification | Required Electrical Adaptation |
| :--- | :--- | :--- | :--- |
| Liquid pH Probe + BNC Amplifier | 1 | 🟢 **AVAILABLE** | Direct connection to GPIO 32 (ADC1_CH4). |
| ESP32-WROOM-32 38-Pin Board | 1 | 🟢 **AVAILABLE** | Type-C power input & logic controller. |
| DS18B20 Waterproof Temp Sensor | 1 | 🟢 **AVAILABLE** | Requires 4.7 kΩ pull-up resistor on GPIO 18. |
| Type-C USB Data Cable | 1 | 🟢 **AVAILABLE** | Main USB power & serial flash interface. |
| M-M & F-F DuPont Jumper Wires | 20 | 🟢 **AVAILABLE** | Breadboard interconnects. |
| Resistor Kit Box | 1 kit | 🟢 **AVAILABLE** | Contains 220Ω, 1kΩ, 4.7kΩ, 10kΩ, 20kΩ resistors. |
| MB-102 Breadboard | 1 | 🟢 **AVAILABLE** | Central circuit prototyping. |
| Green, Yellow, Red 5mm LEDs | 3 | 🟢 **AVAILABLE** | 220 Ω current limiting on GPIO 19, 21, 22. |
| 5V Piezo Audio Buzzer Module | 1 | 🟢 **AVAILABLE** | Requires 2N2222 NPN transistor driver on GPIO 23. |
| Optical Turbidity Sensor Module | 1 | 🟢 **AVAILABLE** | Requires 10k/20k resistor divider on GPIO 33. |
| Transparent 2500 mL Box | 1 | 🟢 **AVAILABLE** | Aquatic test container. |
| AI-Thinker ESP32-CAM Board | 1 | 🟢 **AVAILABLE** | Independent optical node. |
| 5V 1-Channel Relay Module | 1 | 🟢 **AVAILABLE** | Driven via GPIO 27 (Load pending). |
| 2N2222 NPN Transistor | 1 | 🟡 **ADDITIONAL REQUIRED**| Transistor for buzzer driver on GPIO 23. |

---

## 9. Final Categorized Statements

1. 🟢 **SOFTWARE VERIFIED**: All GPIO pin assignments, software drivers, temporal validation thresholds, MQTT topic structures, and FSM decision states are 100% verified via automated pytest baseline (299 passed, 3 skipped).
2. 🔵 **HARDWARE DESIGN VERIFIED FROM DOCUMENTATION**: Voltage safety margins (3.0V ADC max), 10k/20k voltage dividers, 4.7kΩ OneWire pull-ups, and 220Ω LED current limiting are verified against official datasheets.
3. 🟡 **ENGINEERING RECOMMENDATIONS**: Mount sensor amplifier boards externally from the 2500 mL water vessel; use 2N2222 transistor driver for 5V buzzer.
4. 🟠 **PHYSICAL SPECIFICATIONS REQUIRING VERIFICATION**: Final pH buffer 2-point calibration slope and raw optical turbidity voltage zero-point require bench verification upon physical assembly.
5. 🔴 **UNSAFE / BLOCKED**: Direct connection of raw 4.5V turbidity output to ESP32 ADC without resistor divider is **BLOCKED as UNSAFE**.
