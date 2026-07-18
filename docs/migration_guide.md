# Migration Guide: Moving from Virtual Drivers to Physical ESP32 Hardware

This guide explains how to migrate the Capstone Project Version 2.0 software-only virtual embedded system to physical ESP32 microcontrollers. 

Because of the decoupled layered architecture, you only need to modify/replace the **Sensor and Actuator Drivers** layer. The scheduler, gateway telemetry validations, backend, machine learning models, database event stores, and dashboards will remain completely untouched.

---

## 1. Hardware Pin & GPIO Configuration

Physical pins are mapped inside `config/device_config.json`. To run on a physical board, ensure your GPIO mapping connects to the correct microcontrollers inputs.

Example configuration excerpt:
```json
"gpio": {
  "ph": 32,
  "turbidity": 33,
  "dissolved_oxygen": 34,
  "green_led": 12,
  "yellow_led": 13,
  "red_led": 14,
  "buzzer": 15,
  "pump_relay": 16
}
```

---

## 2. Implementing Physical Drivers in MicroPython

To migrate a driver, inherit from the abstract base class `BaseSensorDriver` or `BaseActuatorDriver` defined in `src/iot/drivers/base_driver.py` and replace simulation reads with low-level pin libraries (e.g., `machine.ADC` or `machine.Pin` in MicroPython).

### A. Example: Migrating `VirtualPHSensorDriver` to `ESP32PHSensorDriver`

The virtual driver reads from a simulation environment block. The physical driver will read an analog voltage from an ADC pin, apply a regression formula to convert voltage to pH, and apply local calibration scaling.

#### Physical Implementation Example:
```python
from machine import ADC, Pin
from src.iot.drivers.base_driver import BaseSensorDriver

class ESP32PHSensorDriver(BaseSensorDriver):
    def __init__(self, name: str, pin: int, config: dict = None):
        super().__init__(name, pin, config)
        self.adc = None

    def init(self) -> bool:
        try:
            # Configure ESP32 ADC on the specified GPIO pin
            self.adc = ADC(Pin(self.pin))
            self.adc.atten(ADC.ATTN_11DB)  # 11dB attenuation gives 0-3.6V range
            self.adc.width(ADC.WIDTH_12BIT) # 12-bit width (0-4095 range)
            self.status = "OK"
            return True
        except Exception:
            self.status = "FAULT"
            return False

    def read(self) -> float:
        if self.status == "FAULT" or not self.adc:
            return None
        
        try:
            # Read analog value (0-4095)
            raw_adc = self.adc.read()
            # Convert ADC to voltage (typically 3.3V reference)
            voltage = (raw_adc / 4095.0) * 3.3
            
            # Simple standard pH regression formula (e.g., pH = 3.5 * voltage + offset)
            # Adjust formulas based on your specific analog probe model
            ph_val = 3.5 * voltage
            
            # Apply configured calibration scale and offset
            offset = self.config.get("offset", 0.0)
            scale = self.config.get("scale", 1.0)
            return float((ph_val * scale) + offset)
        except Exception:
            self.status = "FAULT"
            return None
```

### B. Example: Migrating `VirtualLEDDriver` to `ESP32LEDDriver`

For actuators, replace the internal state logs with actual high/low voltage outputs using GPIO pin signals.

#### Physical Implementation Example:
```python
from machine import Pin
from src.iot.drivers.base_driver import BaseActuatorDriver

class ESP32LEDDriver(BaseActuatorDriver):
    def __init__(self, name: str, pin: int, config: dict = None):
        super().__init__(name, pin, config)
        self.io_pin = None

    def set_state(self, state: str) -> bool:
        if not super().set_state(state):
            return False
        
        if not self.io_pin:
            # Initialize pin on first write if not initialized
            try:
                self.io_pin = Pin(self.pin, Pin.OUT)
            except Exception:
                return False
                
        # Write high/low state based on command
        if state == "ON":
            self.io_pin.value(1)
        else:
            self.io_pin.value(0)
        return True
```

---

## 3. Swapping Drivers in the Hardware Abstraction Layer (HAL)

Once the physical drivers are written, swap their import calls inside the HAL class (`src/iot/hal.py`). The rest of the main loop remains unchanged.

```python
# MODIFY src/iot/hal.py imports:
# - from src.iot.drivers.sensors import VirtualPHSensorDriver
# + from src.iot.drivers.sensors_esp32 import ESP32PHSensorDriver

# Inside HAL._init_drivers():
# - self.sensors["ph"] = VirtualPHSensorDriver("PH_01", gpio.get("ph"), self.env, cal.get("ph", {}))
# + self.sensors["ph"] = ESP32PHSensorDriver("PH_01", gpio.get("ph"), cal.get("ph", {}))
```

Notice that we remove the reference to `self.env` because the physical sensor reads directly from the real water body, completing the transition.

---

## 4. Hardware Deployment Architecture Flow

```
+--------------------------------------------------------------+
|                    Main ESP32 Board (MCU)                    |
|                                                              |
|   +------------------------------------------------------+   |
|   |         Firmware Tasks Loop / OS Scheduler           |   |
|   +--------------------------+---------------------------+   |
|                              |                               |
|                              v                               |
|   +------------------------------------------------------+   |
|   |          Hardware Abstraction Layer (HAL)            |   |
|   +--------------------------+---------------------------+   |
|                              |                               |
|                              v                               |
|   +------------------------------------------------------+   |
|   |           Low Level Physical drivers                 |   |
|   +----+--------------------------+------------------+---+   |
|        |                          |                  |       |
+--------|--------------------------|------------------|-------+
         | (I2C/SPI)                | (ADC)            | (GPIO)
         v                          v                  v
    +---------+                +---------+        +---------+
    | GPS/RTC |                | Sensors |        | LED/Pump|
    +---------+                +---------+        +---------+
```
