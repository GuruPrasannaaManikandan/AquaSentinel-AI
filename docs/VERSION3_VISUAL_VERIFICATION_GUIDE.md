# Visual Verification Guide: AquaSentinel-AI Version 3

This document serves as the forensic verification guide to demonstrate that the **AquaSentinel-AI Version 3** firmware, simulation, backend, and dashboard systems are fully functional.

---

## 1. Architectural Overview & Data Flow

The project is structured to run in two primary modes:
1. **Mock Mode (Recommended for Demos):** Runs fully in-memory using an internal `InMemoryMQTTBroker` singleton. It is 100% self-contained, requires no network ports for MQTT, and runs out-of-the-box.
2. **Real MQTT Mode (Physical/Integration Testing):** Connects to a physical MQTT broker (e.g., Eclipse Mosquitto) running on `localhost:1883` via `paho-mqtt` (Python) or `PubSubClient` (C++).

### Runtime Data Flow Trace
```
  [Virtual Environment]
           ↓ (Generates simulated Temperature, pH, Salinity, Turbidity, DO)
     [HAL Drivers]
           ↓ (Reads calibrated ADC values / applies offset & scale)
  [Cooperative Scheduler]
           ↓ (Triggers SensorTask callback on scheduler tick)
      [FSM Engine]
           ↓ (Transitions states: BOOT -> INITIALIZING -> CONNECTING -> ONLINE -> SENSING -> PUBLISHING)
  [Wi-Fi / MQTT Manager]
           ↓ (Publishes telemetry payload on topic: `aquatic/{device_id}/telemetry`)
 central [MQTT Broker] (InMemoryMQTTBroker OR Eclipse Mosquitto)
           ↓ (Gateway subscribes to `aquatic/+/telemetry`)
   [Backend Gateway]
           │ 1. Validates payload format & schema
           │ 2. Extracts features (spatial mapping: US Region, State ID)
           │ 3. Executes ML (XGBoost/RF) + AIS (Negative Selection) inference
           │ 4. Combines evidence via Dempster-Shafer rule of combination
           │ 5. Logs data in SQLite database (`models/fusion/aquatic_events.db`)
           │ 6. Publishes fused state decision to `aquatic/{device_id}/decision`
           ↓ (If state is CRITICAL, publishes `ACTIVATE_BUZZER` command)
  [Edge Device Actuators]
           ↓ (Receives decision/command, updates G/Y/R LEDs, buzzer, and pump relay via HAL)
  [Streamlit Dashboard]
             (Polls backend REST API & WebSockets to display KPIs, live feeds, alerts, and histories)
```

---

## 2. Prerequisites & Environment Setup

### 2.1 Python Dependencies
Ensure Python 3.10+ is installed. Install all required dependencies by running:
```powershell
pip install -r requirements.txt
```

### 2.2 Optional: Eclipse Mosquitto Broker Setup
If you wish to test with a physical MQTT broker rather than the in-memory simulator:
1. **Download:** Get the installer from [Mosquitto Downloads](https://mosquitto.org/download/).
2. **Install:** Run the installer and complete setup. Default directory: `C:\Program Files\mosquitto`.
3. **Environment Variables:** Add `C:\Program Files\mosquitto` to your system `PATH` so `mosquitto` can be executed from any PowerShell terminal.
4. **Execution:** Start the broker:
   ```powershell
   mosquitto -v
   ```
5. **Verify:** Check if the broker is listening on port 1883:
   ```powershell
   netstat -ano | findstr 1883
   ```

---

## 3. Visual Demonstration Procedures

### Option A: Fully Simulated In-Memory Demonstration (Recommended)
This mode runs the entire stack (FastAPI Backend, Streamlit UI, two virtual ESP32 devices, and the Central Gateway) in a single workflow.

#### 1. Startup Command
Open a single Windows PowerShell terminal at the project root (`p:\5th semester\Embedded Systems\Capstone Project`) and execute:
```powershell
python run_demo.py
```

#### 2. Expected Console Output
Upon launch, the terminal will print:
```text
==============================================================
🌊 STARTING AQUATIC ECOSYSTEM IoT & AIS MONITORING DEMO 🌊
==============================================================
[1/2] Launching FastAPI Backend Server via Uvicorn...
[2/2] Launching Streamlit Visualization Dashboard...

🎉 DEMO RUNNING SUCCESSFULLY!
👉 Access the API Documentation: http://127.0.0.1:8000/docs
👉 Access the Monitoring Dashboard: http://127.0.0.1:8501

Press Ctrl+C to terminate both servers and stop simulation.
```

#### 3. Expected Browser Views
- **Dashboard:** Navigate to `http://127.0.0.1:8501`.
- **API Docs:** Navigate to `http://127.0.0.1:8000/docs` to see the interactive FastAPI Swagger UI.

---

### Option B: Standalone Virtual Device (Real MQTT Integration)
This validates the isolated virtual microcontroller firmware stack interacting with a physical broker.

#### 1. Startup Sequence
1. Start your local Mosquitto Broker:
   ```powershell
   mosquitto -v
   ```
2. In a second PowerShell window, launch the standalone virtual device:
   ```powershell
   python embedded_device/main.py --device-id AQUA_FRESH_001 --ecosystem Freshwater --route caml --host localhost --port 1883
   ```
   *(To run the standalone device in mock mode, add the `--use-mock` flag)*

#### 2. Expected Device Console Output
```text
==================================================
Starting Virtual Embedded Device: AQUA_FRESH_001
Ecosystem: Freshwater | Route: caml
MQTT Broker: localhost:1883 (Mock Mode: False)
Scenario: NORMAL
==================================================
[FIRMWARE] Booting virtual microcontroller...
[FIRMWARE] Initializing sensor drivers via HAL...
[FIRMWARE] Connecting to network (SSID: AquaNet_Freshwater_AP)...
[FIRMWARE] Running scheduler task loops. Sampling interval: 10s.
Press Ctrl+C to terminate.

[TICK 1] Triggering scheduler tick cycle...
  Published Telemetry payload: {'temperature_c': 24.2, 'salinity_ppt': 0.15, 'ph': 7.35, ...}
  Device Health: {'wifi_connected': True, 'mqtt_connected': True, 'sensor_status': 'OK'}
  FSM State: WAITING
```

---

### Option C: C++ Embedded Firmware Verification (Self-Tests)
This compiles and validates the production ESP32 C++ firmware codebase.

#### 1. Compilation & Upload Commands
Open a PowerShell terminal in the `firmware/` subdirectory:
```powershell
cd firmware
# Clean previous builds
pio run --target clean

# Compile the firmware
pio run

# Upload to a connected ESP32 board (via USB)
pio run --target upload
```

#### 2. Serial Port Monitoring
Open the serial console to capture bootup diagnostics:
```powershell
pio device monitor
```

#### 3. Expected Serial Output (Boot Verification)
```text
--------------------------------
AquaSentinel-AI Firmware
Firmware Version: 3.8.1
Hardware Mode: MOCK SIMULATOR
--------------------------------

[SYSTEM] Initializing Hardware Abstraction Layer...
[SYSTEM] HAL Initialized Successfully (Status: OK)
[SYSTEM] Executing sensor diagnostics self-test...
[SYSTEM] Diagnostics PASSED. All sensors functional.

==========================================================
         AQUASENTINEL-AI E2E VERIFICATION SUITE           
==========================================================
[SELF-TEST] Starting hardware self-tests...
[SELF-TEST] [PASS] HAL interface verified.
[SELF-TEST] [PASS] ADC Temperature sensor verified.
[SELF-TEST] [PASS] ADC pH sensor verified.
[SELF-TEST] [PASS] ADC Turbidity sensor verified.
[SELF-TEST] [PASS] GPIO Actuators and Indicators verified.
[SELF-TEST] [PASS] WiFiManager interface verified.
[SELF-TEST] [PASS] Heap memory verified. Free: 224856 bytes.
[SELF-TEST] [PASS] Cooperative Scheduler verified.
[SELF-TEST] [PASS] FSM engine verified.
[SELF-TEST] RESULT: PASS
----------------------------------------------------------
[TEST-RUNNER] Starting automated system verification...
[TEST-RUNNER] Scenario 1: Normal Operation Check
[TEST-RUNNER] [PASS] Normal Telemetry processing executed.
[TEST-RUNNER] Scenario 2: Wi-Fi Disconnection and Telemetry Buffering
[TEST-RUNNER] [PASS] Gateway transitioned to RECOVERING.
[TEST-RUNNER] [PASS] Telemetry enqueued in Offline Buffer successfully.
[TEST-RUNNER] Scenario 3: MQTT Disconnection Check
[TEST-RUNNER] [PASS] MQTT Outage handling verified.
[TEST-RUNNER] Scenario 4: Connection Recovery and Buffer Flushing
[TEST-RUNNER] [PASS] Buffer flushed on recovery.
[TEST-RUNNER] RESULT: ALL INTEGRATION SCENARIOS PASS
==========================================================
                  VERIFICATION SUMMARY                    
==========================================================
Hardware Self-Tests:        PASS
System Integration Tests:   PASS
----------------------------------------------------------
OVERALL STATUS: SUCCESS / PASS
==========================================================
Starting Cooperative Task Scheduler...
```

---

## 4. Visual Verification Checklist

To prove the Version 3 subsystems operate correctly, execute the following steps in the Streamlit Dashboard (`http://127.0.0.1:8501`) and check the indicators:

| Step # | User Action | Expected Dashboard Behavior | Actuator LED States | Subsystem Verified |
| :---: | :--- | :--- | :--- | :--- |
| **1** | Select device **AQUA_FRESH_001** and set scenario to `NORMAL`. Click **Start Background Simulation**. | UI updates every 2s. Charts draw flat lines. Status badges show `NORMAL` (Green, ✅). | **Green LED: ON**<br>Yellow LED: OFF<br>Red LED: OFF<br>Buzzer: OFF<br>Pump: OFF | Normal scheduler loop, Wi-Fi link, and MQTT publishing. |
| **2** | Change scenario to `KNOWN_BLOOM_RISK`. Click **Apply Scenario Selection**. | Data values spike. ML predicts bloom risk. Fusion state escalates to `CRITICAL` (Red, 🚨). | Green LED: OFF<br>Yellow LED: OFF<br>**Red LED: ON**<br>**Buzzer: ON**<br>**Pump: ON** | FSM transition to ERROR/CRITICAL and Command Dispatcher (`ACTIVATE_BUZZER`). |
| **3** | Change scenario to `SENSOR_FAULT`. Click **Apply Scenario Selection**. | Temperature reads `NaN`. Payload rejected. Fusion state displays `SENSOR_FAULT` (Gray, ⚙️). | Green LED: OFF<br>**Yellow LED: ON**<br>Red LED: OFF<br>Buzzer: OFF<br>Pump: OFF | Edge Validator bounds rejection & Gateway inference bypass rules. |
| **4** | Go to the **Alert History & Event Store** tab. | A table of warnings and sensor fault alerts is visible with timestamps. | N/A | SQLite event logging & persistence layer. |
| **5** | Select `ACTIVATE_BUZZER` from command overrides, click **Send Command Override**. | Status log notes manual override command executed. Buzzer indicator switches to `ON`. | **Buzzer: ON** | Downstream MQTT command reception and HAL execution. |

---

## 5. Troubleshooting Guide

### 5.1 Port Address Already in Use
* **Symptom:** Terminal outputs `OSError: [Errno 98] Address already in use` or Streamlit fails to load.
* **Reason:** A previous run of Uvicorn (port 8000) or Streamlit (port 8501) was not cleanly killed.
* **Resolution (Windows PowerShell):**
  ```powershell
  # Find process IDs holding the ports
  netstat -ano | findstr :8000
  netstat -ano | findstr :8501
  
  # Terminate processes (replace PID with the actual process ID found)
  taskkill /F /PID <PID>
  ```

### 5.2 ModuleNotFoundError: No module named 'src'
* **Symptom:** Python scripts fail on import.
* **Reason:** Python is looking for modules in the current subdirectory rather than the project root.
* **Resolution:** Run python commands with the `-m` prefix from the project root directory, or explicitly set the environment variable:
  ```powershell
  $env:PYTHONPATH="."
  ```

### 5.3 SQLite Database Locked
* **Symptom:** API outputs `sqlite3.OperationalError: database is locked`.
* **Reason:** Multi-threaded simulation writes block database readers during fast cycles.
* **Resolution:** The project has built-in connection overrides extending timeout thresholds to 10 seconds. If locks persist, restart the demo backend to release active handles.
