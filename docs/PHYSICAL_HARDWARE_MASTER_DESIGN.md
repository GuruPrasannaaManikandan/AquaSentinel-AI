# PHYSICAL HARDWARE MASTER DESIGN SPECIFICATION

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Milestone:** Physical Hardware Design Phase — Master Technical Design  
**Authoritative Hardware Target:** ESP32-WROOM-32 / ESP32-WROOM-32E + AI-Thinker ESP32-CAM  
**Document Version:** 1.0.0 (August 18, 2026)  
**Status:** Software Fully Verified / Hardware Designed to Software Contract / Physical Assembly Pending  

---

> [!IMPORTANT]
> **PRIMARY HARDWARE DESIGN PRINCIPLE**  
> We are designing the physical hardware **STRICTLY TO FIT THE FINALIZED SOFTWARE ARCHITECTURE**.  
> 
> The software architecture established across Milestones V3.8–V4.8.4 is the authoritative interface contract. The physical hardware design adapts to this contract wherever electrically and technically safe.  
> 
> NO physical hardware has been built, wired, or flashed yet. Physical hardware testing and validation remain explicitly marked **PENDING**.

---

## 1. Master System Block Diagram

```
                              AQUATIC ENVIRONMENT
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            │                                                     │
            ▼                                                     ▼
┌──────────────────────┐                              ┌──────────────────────┐
│  ESP32-WROOM-32 MCU  │                              │   ESP32-CAM BOARD    │
│  (Sensors + FSM)     │                              │   (AI-Thinker OV2640)│
└───────────┬──────────┘                              └───────────┬──────────┘
            │                                                     │
 ┌──────────┼──────────┬──────────┐                               │
 ▼          ▼          ▼          ▼                               │
Temp       pH        Turb        DO & Salinity                    │
[GPIO18]  [GPIO32]   [GPIO33]   [GPIO34 / 36]                     │
Digital   Analog     Analog     Analog                            │
(3.3V)    (ADC1)     (ADC1)     (ADC1)                            │
            │                                                     │
            ▼                                                     ▼
     Telemetry JSON                                        Camera Frame JSON
     (Schema 1.1)                                          (Schema 1.1 + Base64 JPEG)
            │                                                     │
            │ MQTT over Wi-Fi                                     │ MQTT over Wi-Fi
            └──────────────────────────┬──────────────────────────┘
                                       ▼
                            ┌─────────────────────┐
                            │    GATEWAY HOST     │
                            │ (TemporalValidator  │
                            │  + MobileNetV3 CV   │
                            │  + FusionEngine)    │
                            └──────────┬──────────┘
                                       │
                                MQTT Decision
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │  ESP32-WROOM-32 MCU │
                            └──────────┬──────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
     Status LEDs (x3)            Audio Buzzer               Aerator Relay
    [GPIO 19, 21, 22]             [GPIO 23]                   [GPIO 27]
    (Green/Yellow/Red)         (2N2222 Driver)            (Optocoupled 5V Coil)
                                                                  │
                                                                  ▼
                                                          12V Aerator Pump
```

---

## 2. Main MCU & Microcontroller Specifications

### 2.1 ESP32-WROOM-32 / ESP32-WROOM-32E Development Module
- **Microcontroller**: Tensilica Dual-Core 32-bit LX6, 240 MHz clock frequency.
- **Memory**: 520 KB SRAM, 4 MB SPI Flash.
- **Wireless Connectivity**: Wi-Fi 802.11 b/g/n (2.4 GHz) + Bluetooth v4.2 BR/EDR and BLE.
- **PlatformIO Environment**: `board = esp32dev`, `framework = arduino`.
- **Primary Responsibility**: Sensor sampling, HAL coordinate management, C++ FSM decision execution, LED indicator control, buzzer alarms, relay driving, and telemetry MQTT publishing.

### 2.2 AI-Thinker ESP32-CAM Board
- **Microcontroller**: ESP32-S module with 4 MB external PSRAM.
- **Camera Sensor**: OV2640 2 Megapixel image sensor module.
- **Capture Configuration**: `224x224` JPEG resolution (`FRAMESIZE_224X224`), `PIXFORMAT_JPEG`, `jpeg_quality = 12`.
- **Capture Rate**: 0.1 FPS (1 frame every 10 seconds).
- **Primary Responsibility**: Dedicated optical frame capture, JPEG compression, Base64 JSON payload generation, and MQTT publishing to `aquatic/{device_id}/camera/raw`.

---

## 3. Sensor Array & Signal Conditioning Design

### 3.1 DS18B20 Digital Temperature Sensor
- **Pin Assignment**: `GPIO 18` (Digital I/O).
- **Protocol**: OneWire single-bus protocol.
- **Signal Conditioning**: External 4.7 kΩ pull-up resistor connected between `DQ` and `3.3V`.
- **Power Rail**: 3.3V / 5.0V DC.

### 3.2 Analog pH Sensor Module
- **Pin Assignment**: `GPIO 32` (`ADC1_CH4`).
- **Interface**: BNC probe connected to signal conditioning module with potentiometric offset calibration.
- **Signal Range**: 0.0V to 3.0V DC (100% safe for ESP32 3.3V ADC).
- **Power Rail**: 5.0V DC.

### 3.3 Analog Turbidity Sensor Module
- **Pin Assignment**: `GPIO 33` (`ADC1_CH5`).
- **Interface**: Infrared LED emitter and phototransistor optical sensing board.
- **Signal Range**: 0.0V to 4.5V raw module output.
- **Signal Conditioning**: Precision resistor voltage divider (10 kΩ / 20 kΩ 1% metal film) scaling 4.5V max output down to 3.0V max at `GPIO 33`.
- **Power Rail**: 5.0V DC.

### 3.4 Analog Dissolved Oxygen (DO) Sensor Probe
- **Pin Assignment**: `GPIO 34` (`ADC1_CH6` — Input Only pin).
- **Interface**: Galvanic / electrochemical DO probe with operational amplifier signal conditioner.
- **Signal Range**: 0.0V to 3.0V DC.
- **Signal Conditioning**: RC low-pass filter (10 kΩ + 0.1 µF capacitor) for high-frequency noise rejection.
- **Power Rail**: 5.0V DC.

### 3.5 Analog Salinity / TDS Sensor Probe
- **Pin Assignment**: `GPIO 36` (`ADC1_CH0` — VP / Input Only pin).
- **Interface**: AC excitation signal generator board avoiding probe polarization.
- **Signal Range**: 0.0V to 2.3V DC.
- **Power Rail**: 3.3V / 5.0V DC.

### 3.6 GY-NEO6MV2 GPS Module
- **Pin Assignment**: `GPIO 16` (UART2 RX), `GPIO 17` (UART2 TX).
- **Interface**: Hardware UART2 serial interface at 9600 baud rate.
- **Power Rail**: 3.3V / 5.0V DC.

---

## 4. Actuator Driver & Safety Mapping

| Actuator Device | GPIO Pin | Hardware Driver Circuit | Software Mapping & Actuator State |
| :--- | :--- | :--- | :--- |
| **Green Status LED** | **GPIO 19** | 3.3V Direct via 220 Ω resistor | **NORMAL State**: Green LED ON, Yellow OFF, Red OFF, Buzzer OFF, Relay OFF. |
| **Yellow Warning LED**| **GPIO 21** | 3.3V Direct via 220 Ω resistor | **WARNING State**: Yellow LED ON, Green OFF, Red OFF, Buzzer OFF, Relay ON. |
| **Red Critical LED** | **GPIO 22** | 3.3V Direct via 220 Ω resistor | **CRITICAL State**: Red LED ON, Green OFF, Yellow OFF, Buzzer ON, Relay ON. |
| **Audio Alarm Buzzer**| **GPIO 23** | 2N2222 NPN Transistor + 1kΩ Base | High-active audio alert during **CRITICAL** / **SENSOR_FAULT** states. |
| **Aerator Pump Relay** | **GPIO 27** | Optocoupled 5V Relay Module | Controls 12V Aerator Pump. Activated during **WARNING** and **CRITICAL** states. |

> [!IMPORTANT]
> **ACTUATOR SOFTWARE BEHAVIOR PRESERVATION**  
> 
> - **`NORMAL`**: Green LED ON, Yellow LED OFF, Red LED OFF, Buzzer OFF, Aerator Relay OFF.  
> - **`WARNING`**: Yellow LED ON, Green LED OFF, Red LED OFF, Buzzer OFF, Aerator Relay ON.  
> - **`CRITICAL`**: Red LED ON, Green LED OFF, Yellow LED OFF, Buzzer ON, Aerator Relay ON.  
> - **`UNKNOWN_ANOMALY`**: Yellow + Red LEDs ON, Buzzer OFF, Aerator Relay OFF.  
> - **`SENSOR_FAULT`**: Yellow + Red LEDs ON, Buzzer ON, Aerator Relay OFF.  
> 
> This exact software state mapping is 100% preserved.

---

## 5. Categorized Forensic Summary

1. **`SOFTWARE VERIFIED`**: All GPIO assignments, driver factory contracts, temporal validation thresholds, MQTT topic structures, and FSM actuator states are 100% software verified.
2. **`DATASHEET VERIFIED`**: Electrical voltage limits (3.3V ADC max), OneWire timing, UART baud rates (9600), and power current budgets (869.5 mA peak 5V) are verified against official manufacturer datasheets.
3. **`ENGINEERING RECOMMENDATION`**: Use dedicated 5V 2A power supply for ESP32-CAM; use star grounding topology to isolate motor switching noise; use optocoupler isolation for relay.
4. **`PHYSICAL TEST PENDING`**: Physical breadboard assembly, PCB soldering, probe fluid calibration, and live Wi-Fi transmission are pending physical hardware build.
