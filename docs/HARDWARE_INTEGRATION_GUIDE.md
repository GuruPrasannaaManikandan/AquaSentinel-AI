# Hardware Integration Guide

This guide details the hardware integration, wiring schematics, and pinout configurations for deploying the AquaSentinel-AI firmware on a physical ESP32-WROOM-32E board.

## Pin Assignments

| Sensor / Actuator | ESP32 GPIO Pin | Interface Type | Description |
| --- | --- | --- | --- |
| **DS18B20 Temp** | `GPIO 4` | OneWire | Digital temperature sensor probe. |
| **Analog pH Probe**| `GPIO 32 (ADC1_CH4)`| Analog input | Analog voltage output representing pH levels. |
| **Salinity Probe** | `GPIO 33 (ADC1_CH5)`| Analog input | Analog conductivity probe output. |
| **Turbidity Probe** | `GPIO 34 (ADC1_CH6)`| Analog input | Analog turbidity photodiode voltage. |
| **DO Probe** | `GPIO 35 (ADC1_CH7)`| Analog input | Analog Dissolved Oxygen voltage. |
| **Green LED** | `GPIO 12` | GPIO Output | Normal operation indicator. |
| **Yellow LED** | `GPIO 13` | GPIO Output | Warning/Reconnecting status indicator. |
| **Red LED** | `GPIO 14` | GPIO Output | Active error status indicator. |
| **Buzzer** | `GPIO 15` | GPIO Output | Critical alarm warning buzzer. |
| **Pump Relay** | `GPIO 23` | GPIO Output | Water recirculation/flush pump activator. |

## Wiring Overview

```
                          ESP32 Pinout Map
                     +───────────────────────+
                     |                       |
   [ DS18B20 Temp ] ─| GPIO 4          3.3V  |─ [ 3.3V Power Line ]
   [ pH Probe ] ────| GPIO 32         5.0V  |─ [ 5.0V Power Line ]
   [ Salinity ] ────| GPIO 33         GND   |─ [ Ground Line ]
   [ Turbidity ] ───| GPIO 34         GPIO23|─ [ Pump Relay ]
   [ DO Probe ] ────| GPIO 35         GPIO15|─ [ Alarm Buzzer ]
   [ Green LED ] ───| GPIO 12         GPIO14|─ [ Red LED ]
   [ Yellow LED ] ──| GPIO 13               |
                     |                       |
                     +───────────────────────+
```

## Power Management

- **ESP32 MCU Board**: Powered via micro-USB (5V) or external power supply on the 5V/GND pins.
- **Analog Sensor Modules (pH, DO, TDS)**: Require a stable 5V input. Using 3.3V will cause scaling offsets and calibration drift.
- **Temperature Probe**: Can be powered via 3.3V. Requires a 4.7kΩ pull-up resistor between the OneWire data line (GPIO 4) and the 3.3V rail.
- **Relay and Buzzer Modules**: Require separate 5V lines. Directly driving relays from ESP32 pins will trigger overcurrent reset loops. Use optocouplers and flyback diodes.
