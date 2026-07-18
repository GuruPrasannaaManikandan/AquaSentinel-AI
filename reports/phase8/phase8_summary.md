# Phase 8 Implementation Summary

## 1. Backend Architecture & REST API Endpoints
We implemented a lightweight and robust backend service layer using **FastAPI** that wraps the virtual device simulator runtime, central gateway, and EventStore.

The REST API exposes the following endpoints:
*   `GET /health`: Diagnostic health check for database connections and pipeline model loaders.
*   `GET /devices`: Lists all active devices registered.
*   `GET /devices/{device_id}`: Details on coordinate bounds and enabled sensors.
*   `GET /devices/{device_id}/latest`: Combined object of the latest polled telemetry and model decisions.
*   `GET /devices/{device_id}/telemetry`: Historical time-series telemetry with time-window filtering.
*   `GET /devices/{device_id}/decisions`: Historical model predictions and fusion decisions.
*   `GET /devices/{device_id}/actuators`: Traceable histories of LEDs, buzzer, and pump relay states.
*   `GET /alerts`: Persistent warning, critical, and anomaly alert notifications.
*   `POST /alerts/{alert_id}/acknowledge`: Acknowledges and dismisses an active alert.
*   `GET /system/status`: Aggregated system status KPIs (active warnings, OOD count, device online count).
*   `POST /devices/{device_id}/command`: Sends manual override commands to simulated ESP32 microcontrollers.
*   `POST /simulation/start`: Starts background simulation polling loop.
*   `POST /simulation/stop`: Stops background simulation loop.
*   `POST /simulation/scenario`: Updates the simulated scenario (e.g., `SENSOR_FAULT`).
*   `POST /simulation/cycle`: Executes exactly one single poll-validation-inference step synchronously.

---

## 2. Real-Time WebSocket Streaming
*   Exposes a reactive endpoint `/ws/live` to broadcast real-time telemetry frames and fused decisions to connected browser sockets.
*   Uses a threadsafe `ConnectionManager` to push JSON updates instantly without polling the database.

---

## 3. Streamlit Monitoring Dashboard
We designed and implemented a professional dashboard under [dashboard/app.py](file:///p:/5th%20semester/Embedded%20Systems%20Capstone%20Project/dashboard/app.py) featuring:
1.  **System KPIs:** Real-time metrics counters for alerts, warnings, and unacknowledged items.
2.  **Live Telemetry Panel:** Gauges and metrics showing water metrics, FSM states, and maps.
3.  **Model Diagnostics:** Detailed separate cards tracking ML prediction confidences and AIS negative selection distances.
4.  **Simulation Controls:** Interactive inputs to update scenarios (e.g. Red Tide bloom) and send hardware commands.
5.  **Historical Trends:** Plotted time-series trends of salinity, temp, pH, and DO.
6.  **Interactive Alert Log:** UI table displaying database rows and quick buttons to acknowledge warnings.

---

## 4. Visual Color Policy Compliance
We mapped the FSM and fusion states to distinct colors and icons:
*   `NORMAL` $ightarrow$ Green Badge (✅)
*   `WARNING` $ightarrow$ Orange Badge (⚠️)
*   `CRITICAL` $ightarrow$ Red Badge (🚨)
*   `UNKNOWN_ANOMALY` $ightarrow$ Purple Badge (👾)
*   `SENSOR FAULT` $ightarrow$ Gray Badge (⚙️)

---

## 5. MQTT Transport Mode
*   **Mode:** `IN_MEMORY_MQTT`
*   **Discussion:** The system defaults to the custom, highly robust in-memory mock broker transport layer. This ensures that the entire sensor-to-actuator simulation runs deterministically in a single process thread without external dependencies, while keeping the client subscriber interface identical to standard MQTT.

---

## 6. Phase 9 Finalization Recommendations
For Phase 9 (Final Review and Wrap-up):
- Prepare final project documentation.
- Lock all folder configurations and databases.
- Consolidate final balanced accuracy results across baseline champions.
