# PHYSICAL POWER ARCHITECTURE & ELECTRICAL ISOLATION PLAN

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Milestone:** Physical Hardware Design Phase — Power System & Isolation Architecture  
**Document Version:** 1.0.0 (August 18, 2026)  
**Status:** Software Verified / Datasheet Verified / Physical Assembly Pending  

---

## 1. System Power Tree Schematic

```
                          12V DC Mains Adapter / Battery (12V 3A)
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    │                                             │
                    ▼                                             ▼
       12V Aerator Pump Power Rail                   LM2596 / MP1584 Buck Converter
       (Isolated Motor Power Circuit)                (12V Step-Down to 5.0V @ 3A)
                    │                                             │
                    │                                             ▼
                    │                                      5.0V Main Power Rail
                    │                                             │
         ┌──────────┴──────────┐               ┌──────────────────┼──────────────────┐
         │                     │               │                  │                  │
         ▼                     ▼               ▼                  ▼                  ▼
    Pump Motor (12V)    Relay NO Contact   ESP32-CAM (5V Input)  Relay Coil (5V)   AMS1117 3.3V LDO
                                              (310mA Peak)        (70mA Peak)        (ESP32 Onboard)
                                                                                     │
                                                                                     ▼
                                                                             3.3V System Rail
                                                                                     │
                                                                       ┌─────────────┼─────────────┐
                                                                       ▼             ▼             ▼
                                                                  ESP32-WROOM    Sensors       Status LEDs
                                                                  (160mA Peak) (Temp/pH/DO)   (Green/Yel/Red)
```

---

## 2. Power Consumption Budget Analysis (Datasheet Estimates)

> [!NOTE]
> All current values in the table below represent **datasheet specifications** and maximum operational peak ratings. They are engineering estimates to size the power supply and are **NOT** claimed as measured physical hardware laboratory data.

| Subsystem Component | Supply Rail | Min Voltage (V) | Typical Current (mA) | Peak Current (mA) | Power Budget Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ESP32-WROOM-32 MCU** | 3.3V (via LDO) | 3.0V | 80 mA | 240 mA | Peak during Wi-Fi transmission bursts. |
| **ESP32-CAM + OV2640** | 5.0V Input | 4.75V | 120 mA | 310 mA | Peak during JPEG encode + Wi-Fi publish + LED flash. |
| **DS18B20 Temp Sensor**| 3.3V Rail | 3.0V | 1 mA | 1.5 mA | Active conversion draw. |
| **pH Sensor Module** | 5.0V Rail | 4.75V | 10 mA | 20 mA | Analog signal conditioning board draw. |
| **Turbidity Module** | 5.0V Rail | 4.75V | 30 mA | 40 mA | Infrared LED emitter + phototransistor. |
| **DO Sensor Module** | 5.0V Rail | 4.75V | 15 mA | 25 mA | Galvanic / electrochemical amplifier. |
| **Salinity / TDS Module**| 3.3V / 5.0V | 3.0V | 6 mA | 10 mA | AC excitation signal generator draw. |
| **GPS Module (NEO-6M)** | 3.3V / 5.0V | 3.0V | 35 mA | 67 mA | Peak draw during satellite acquisition. |
| **Status LEDs (x3)** | 3.3V Rail | 3.0V | 15 mA | 45 mA | 3.3V driven through 220 Ω resistors (15mA each). |
| **Buzzer (2N2222 Driver)**| 5.0V Rail | 4.5V | 20 mA | 40 mA | Driven via NPN transistor. |
| **Relay Coil (5V)** | 5.0V Rail | 4.5V | 50 mA | 70 mA | Optocoupled coil activation current. |
| **Aerator Pump Motor** | 12V Dedicated | 11.0V | 800 mA | 2000 mA | High inrush inductive motor startup current. |
| **TOTAL 5V/3.3V SYSTEM**| **5.0V Main** | **4.75V** | **382 mA** | **869.5 mA** | **Sized for 5V 3A Buck Converter (300% Margin)** |
| **TOTAL 12V MOTOR** | **12V Main** | **11.0V** | **800 mA** | **2000 mA** | **Sized for 12V 3A DC Adapter (150% Margin)** |

---

## 3. Grounding Strategy & Noise Isolation

### 3.1 Single-Point Star Grounding Topology
To prevent heavy inductive switching noise from the 12V aerator pump motor from corrupting sensitive analog sensor ADC readings (pH, Turbidity, DO, Salinity), the power layout enforces a **Star Grounding Topology**:

```
      [ 12V Motor Ground ] ─────────────────┐
                                            │
      [ 5V Buck Regulator Ground ] ─────────┼──► [ Main Star Ground Point (GND) ]
                                            │
      [ Analog Sensors & ESP32 GND ] ───────┘
```

1. **Analog Ground Plane**: Low-noise ground trace dedicated exclusively to analog sensors and ESP32 ADC reference pins.
2. **Power Ground Plane**: High-current ground trace for the 5V buck regulator, relay coil, and buzzer transistor.
3. **Inductive Motor Ground Plane**: Completely isolated 12V ground return path connected to the main power entry point.

---

## 4. Electrical Protection & Decoupling Circuitry

1. **Relay Optocoupler Isolation**: The 5V relay module utilizes an **EL817 optocoupler** to isolate the 3.3V ESP32 GPIO 27 control pin from the 5V relay coil circuit.
2. **Motor Flyback Diode**: A **1N4007 rectifier diode** is connected in reverse parallel across the 12V aerator pump terminals to absorb inductive voltage spikes when the relay turns OFF.
3. **Buzzer Flyback Diode**: A **1N4148 signal diode** is connected across the buzzer terminals driven by the 2N2222 transistor on GPIO 23.
4. **Power Rail Decoupling Capacitors**:
   - **Main 5V Rail**: 470 µF 16V Electrolytic + 0.1 µF Ceramic capacitor placed near the ESP32-CAM power terminals.
   - **Main 3.3V Rail**: 100 µF 10V Electrolytic + 0.1 µF Ceramic capacitor placed near the ESP32-WROOM power input.
