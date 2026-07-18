# Future Hardware Migration Plan

This document outlines the migration path from our software simulation to a physical hardware deployment.

---

## 1. Hardware Bill of Materials (BOM)

| Component | Selected Hardware Model | Interface Protocol |
|:---|:---|:---|
| **Microcontroller** | ESP32-WROOM-32E Dev Module | GPIO, I2C, UART, ADC |
| **Water Temperature** | DS18B20 (Waterproof probe) | One-Wire (Digital) |
| **Salinity / TDS** | Analog TDS Sensor Meter (Gravity) | ADC (Analog GPIO) |
| **Water pH** | Analog pH Sensor Kit v2 (DFRobot) | ADC (Analog GPIO) |
| **Turbidity** | Gravity: Analog Turbidity Sensor | ADC (Analog GPIO) |
| **Dissolved Oxygen** | Gravity: Analog Dissolved Oxygen Sensor | ADC (Analog GPIO) |
| **GPS Module** | Neo-6M GPS Module | UART (RX/TX) |
| **Actuator Relays** | 5V Optocoupler Relay Board | GPIO (Digital Out) |

---

## 2. Software Changes & Driver Replacements

### 2.1 Replaced Modules
*   **Sensor Simulator:** `sensor_simulator.py` is fully replaced by a C++ (ESP-IDF / Arduino) or MicroPython layer on the physical ESP32 that reads hardware pins:
    *   *DS18B20:* Reads via OneWire library.
    *   *pH/TDS/Turbidity:* Reads raw ADC voltage and maps it to physical values:
        $$\text{pH\_Value} = V_{\text{read}} \times m + c$$
    *   *GPS:* Parses NMEA sentences using TinyGPS++.
*   **Actuators Simulator:** `actuators.py` is replaced by physical GPIO outputs triggering status LEDs, active piezoceramic buzzers, and relay boards for aerator pumps.
*   **MQTT client Wrapper:** `mqtt_client.py` is replaced by `PubSubClient` (C++) or `umqtt.simple` (MicroPython) to connect to a real MQTT broker.

### 2.2 Unchanged Modules (Core Intelligence Layer)
The core Python modules remain unchanged and run on a gateway node (e.g., Raspberry Pi, local edge server, or cloud gateway):
*   Supervised ML loader and classifiers (`deployment_loader.py`).
*   Unsupervised AIS preprocessor and detectors (`ais_loader.py`).
*   Evidence-Fusion Engine (`decision_pipeline.py`).
*   SQLite Event Store database logger (`event_store.py`).
*   FastAPI backend server and Streamlit dashboard.

---

## 3. Communication & Transport Changes
*   **Broker Migration:** Switch from `InMemoryMQTTBroker` to a real broker, such as **Eclipse Mosquitto** hosted on a local Raspberry Pi or **HiveMQ/AWS IoT Core** in the cloud.
*   **Wireless Protocol:** The ESP32 utilizes its built-in WiFi chip to connect to local routers, or a cellular/LoRaWAN shield for remote field deployments.

---

## 4. Calibration & Deployment Challenges

*   **Sensor Calibration:** Analog probes (pH and TDS) drift over time. Regular calibration using standard buffer solutions (pH 4.01, 7.00, and 10.01) is required.
*   **ADC Noise:** The ESP32 ADC exhibits non-linearities and thermal noise. Hardware low-pass RC filters and software averaging (sliding mean of 10 samples) are recommended.
*   **Power Management:** Field deployments require solar panels, lithium-ion battery packs, and ESP32 deep-sleep cycles to optimize power usage.
