# PHYSICAL WIRING PLAN & PIN-TO-WIRE SCHEMATIC

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Milestone:** Physical Hardware Design Phase — Wiring Specification  
**Authoritative Hardware Target:** ESP32-WROOM-32 / ESP32-WROOM-32E + AI-Thinker ESP32-CAM  
**Document Version:** 1.0.0 (August 18, 2026)  
**Status:** Software Verified / Datasheet Verified / Physical Assembly Pending  

---

## 1. Master GPIO Pin Assignment Table (ESP32-WROOM-32)

| Peripheral Component | Signal Name | ESP32 GPIO | Channel / Type | Signal Voltage | Level Shifting / Protection | Power Rail | Ground | Boot Pin / Safety Note |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DS18B20 Temp Sensor** | `DQ_DATA` | **GPIO 18** | Digital I/O | 3.3V / 5.0V | 4.7 kΩ Pull-up to 3.3V | 3.3V / 5V | Common GND | Standard IO. Clean OneWire timing. |
| **pH Sensor Module** | `PH_PO` | **GPIO 32** | Analog (ADC1_CH4)| 0.0V - 3.0V | Voltage Divider / Unity Buffer | 5.0V | Common GND | ADC1 Pin. Safe with 3.3V ADC. |
| **Turbidity Sensor** | `TURB_AO` | **GPIO 33** | Analog (ADC1_CH5)| 0.0V - 4.5V | 10kΩ/20kΩ Divider (5V -> 3.3V) | 5.0V | Common GND | ADC1 Pin. Must NOT exceed 3.3V into ESP32. |
| **Dissolved Oxygen (DO)**| `DO_AO` | **GPIO 34** | Analog (ADC1_CH6)| 0.0V - 3.0V | Buffer / RC Filter | 5.0V | Common GND | ADC1 Input-Only Pin. Cannot pull output. |
| **Salinity / TDS Sensor**| `TDS_AO` | **GPIO 36** | Analog (ADC1_CH0)| 0.0V - 2.3V | Low-pass RC Filter | 3.3V / 5V | Common GND | ADC1 Input-Only Pin (VP). Safe ADC range. |
| **GPS Module (UART2)** | `GPS_TXD` | **GPIO 16** | UART2_RX | 3.3V Serial | Direct Connection (3.3V TX) | 3.3V / 5V | Common GND | Serial RX. Ensure common ground. |
| **GPS Module (UART2)** | `GPS_RXD` | **GPIO 17** | UART2_TX | 3.3V Serial | Direct Connection (3.3V RX) | 3.3V / 5V | Common GND | Serial TX. High impedance during boot. |
| **Green Status LED** | `LED_GREEN` | **GPIO 19** | Digital Output| 3.3V Logic | 220 Ω Current Limiting Resistor| 3.3V Rail | Common GND | High-active (Normal / Ready indicator). |
| **Yellow Warning LED** | `LED_YELLOW`| **GPIO 21** | Digital Output| 3.3V Logic | 220 Ω Current Limiting Resistor| 3.3V Rail | Common GND | High-active (Warning / Elevated Risk). |
| **Red Critical LED** | `LED_RED` | **GPIO 22** | Digital Output| 3.3V Logic | 220 Ω Current Limiting Resistor| 3.3V Rail | Common GND | High-active (Critical / Bloom Alert). |
| **Audio Alarm Buzzer** | `BUZZER_CTRL`| **GPIO 23** | Digital Output| 3.3V Logic | NPN Transistor (2N2222) + 1kΩ | 5.0V Rail | Common GND | High-active. Flyback diode across buzzer coil. |
| **Aerator Pump Relay** | `RELAY_IN1` | **GPIO 27** | Digital Output| 3.3V Logic | Optocoupled 5V Relay Module | 5.0V Rail | Isolated GND| High/Low Active Module. 1N4007 flyback across pump. |

---

## 2. ESP32-CAM (AI-Thinker OV2640) Interface Wiring

| Pin / Connection | Function | Voltage / Signal | Connection Target | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **VCC (5V)** | Power Supply Input | 5.0V DC (Peak 310 mA) | Dedicated 5V 2A Power Rail | High peak current during Wi-Fi transmission & flash. |
| **GND** | Ground Reference | 0V | Common Ground Rail | System ground reference. |
| **U0TXD (GPIO 1)** | Serial Transmit | 3.3V Serial | FTDI Programmer RXD | Firmware flashing & serial debugging. |
| **U0RXD (GPIO 3)** | Serial Receive | 3.3V Serial | FTDI Programmer TXD | Firmware flashing & serial debugging. |
| **GPIO 0** | Boot Mode Selection | 3.3V / GND | Ground (Program) / Floating (Run)| Jumper to GND during flashing; disconnect to boot normally. |
| **RESET / EN** | Hard Reset | Pushbutton / RC | Reset Pushbutton to GND | System reboot trigger. |

---

## 3. Critical Electrical Constraints & Safeguards

> [!CAUTION]
> **5V OVERVOLTAGE PROTECTION WARNING**  
> ESP32 GPIO pins are **NOT 5V tolerant**. Exceeding 3.6V on any GPIO pin will permanently destroy the ESP32 silicon.  
> 
> Any analog sensor module operating from a 5V supply that outputs >3.3V (such as raw 0-5V Turbidity or pH modules) **MUST** use a precision voltage divider (e.g. 10 kΩ / 20 kΩ 1% tolerance resistors) to scale the maximum output to $\le 3.0\text{ V}$.

> [!IMPORTANT]
> **ADC1 vs ADC2 HARDWARE CONSTRAINT**  
> All 4 analog sensor probes (pH, Turbidity, DO, Salinity) are strictly assigned to **ADC1** pins (GPIOs 32, 33, 34, 36).  
> **ADC2** (GPIOs 0, 2, 4, 12, 13, 14, 15, 25, 26, 27) cannot be sampled by the ESP32 hardware while the Wi-Fi stack is active. Assigning analog sensors to ADC2 would crash sensor telemetry during MQTT transmission.

---

## 4. Bootstrapping Pin Audit & Precautions

- **GPIO 0**: ESP32 Boot Mode selection pin. Must be HIGH during normal boot. (Reserved on main MCU; used as Flash jumper on ESP32-CAM).
- **GPIO 2**: Must be left floating or pulled LOW during boot.
- **GPIO 12 (MTDI)**: Must be LOW during boot for 3.3V flash voltage. (Avoided in main MCU design).
- **GPIO 15 (MTDO)**: Must be HIGH during boot for silent log output. (Avoided in main MCU design).
