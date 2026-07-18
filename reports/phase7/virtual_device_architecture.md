# Virtual IoT Device Architecture Report

This report describes the hardware and software architecture of the virtual aquatic monitoring node based on the ESP32 microcontroller.

## 1. Simulated Hardware Components

The virtual node simulates the following physical components:
1.  **ESP32 Microcontroller:** The core computation unit running an event-driven state machine.
2.  **GPS Module:** Provides spatial telemetry (`latitude`, `longitude`).
3.  **RTC (Real-Time Clock) Module:** Provides millisecond-accurate timestamps used to calculate seasonal cyclic encodings.
4.  **Water Temperature Sensor:** Measures temperature in °C.
5.  **Salinity/TDS (Total Dissolved Solids) Sensor:** Measures salinity in parts per thousand (ppt).
6.  **pH Sensor:** Measures acidity/alkalinity in the range [0.0, 14.0].
7.  **Turbidity Sensor:** Measures water clarity in Nephelometric Turbidity Units (NTU).
8.  **Dissolved Oxygen (DO) Sensor:** Measures DO in mg/L.
9.  **LED Indicators:**
    *   **Green LED:** Indicates NORMAL operation.
    *   **Yellow LED:** Indicates WARNING conditions (or OOD telemetry).
    *   **Red LED:** Indicates CRITICAL threat state.
10. **Piezo Buzzer:** Sound emitter for CRITICAL alarms.
11. **Relay-Controlled Aerator/Water Pump:** Virtual actuator triggered during warnings/critical events.

---

## 2. Sensor Classification: Inference vs. Extensibility

To prevent model ingestion errors, we separate the sensors into two groups:

### 2.1 Model Inference Sensors (Direct Input)
*   **GPS Coordinates:** Ingested directly by both CAML (`lat`, `lon`) and HABSOS (`LATITUDE`, `LONGITUDE`).
*   **RTC Timestamp:** Used to calculate cyclic date features (`Month_sin`, `Month_cos`, etc.) for both models.
*   **Water Temperature:** Ingested directly by HABSOS (`WATER_TEMP`). Excluded from CAML.
*   **Salinity:** Ingested directly by HABSOS (`SALINITY`). Excluded from CAML.

### 2.2 Edge-Only & Extensibility Sensors (Monitored via Local Rules)
*   **pH, Turbidity, and Dissolved Oxygen:** These variables were **not** part of the training feature space for CAML or HABSOS baseline models. 
*   **Gateway Policy:** The IoT gateway will validate these values and persist them in the event store but **must never** feed them into the ML/AIS model input structures.
*   **Edge Safety Rules:** These are used by the ESP32 node locally to raise immediate warning flags if values exceed predefined physical limits (e.g. pH < 6.0 or pH > 9.0).
