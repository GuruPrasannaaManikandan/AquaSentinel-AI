# Final Capstone Demonstration Guide

This guide outlines the 8–12 minute sequence for presenting the integrated system to the capstone evaluators.

---

## 1. Demo Checklist & Setup (1 Minute)
1.  Verify Python and dependencies are installed.
2.  Open a terminal window and launch the demo:
    ```bash
    python run_demo.py
    ```
3.  Open your browser to:
    *   **Dashboard:** `http://127.0.0.1:8501`
    *   **API Docs:** `http://127.0.0.1:8000/docs`

---

## 2. Walkthrough Sequence

### 2.1 Problem & Architecture Introduction (2 Minutes)
*   Explain the problem: Supervised ML models can predict known bloom classes but fail to detect unknown anomalies.
*   Introduce the solution: A parallel ML + AIS (Negative Selection Algorithm) gateway with a rules-based Evidence-Fusion Engine.
*   Highlight the software-based virtual IoT model (simulated ESP32 FSM, edge validation, and mock MQTT broker).

### 2.2 Freshwater Node & Normal Flow (2 Minutes)
*   In the dashboard, select **AQUA_FRESH_001** and set the scenario to `NORMAL`.
*   Click **Start Background Simulation**.
*   Point out:
    1.  Live telemetry updating every 2 seconds.
    2.  ML output: class `1` (Normal) with high confidence.
    3.  AIS output: `SELF` (no anomaly).
    4.  Fusion state: `NORMAL` (Green indicator, ✅).
    5.  Actuator states: Green LED is `ON`.

### 2.3 Bloom-Risk State Escalation (2 Minutes)
*   Change the scenario to `KNOWN_BLOOM_RISK` and click **Apply Scenario Selection**.
*   Observe the changes:
    1.  Turbidity and pH rise.
    2.  ML output shifts to class `4` (Bloom risk).
    3.  Fusion state escalates to `CRITICAL` (Red indicator, 🚨).
    4.  Actuators: Red LED, buzzer, and pump relay turn `ON`.
    5.  Show the warning generated in the **Alert History** tab.

### 2.4 Edge Validation & Sensor Fault Handling (2 Minutes)
*   Change the scenario to `SENSOR_FAULT`.
*   Observe:
    1.  Temperature changes to `NaN`.
    2.  Edge validator rejects the telemetry payload.
    3.  ML/AIS inference is bypassed to prevent model contamination.
    4.  Fusion state sets to `SENSOR_FAULT` (Gray indicator, ⚙️).
    5.  Actuators: Yellow LED turns `ON`.

### 2.5 Manual Overrides & History (1 Minute)
*   In the sidebar, select `ACTIVATE_BUZZER` and click **Send Command Override**. Show the buzzer activating in the actuator status indicator.
*   Navigate to the **Alert History & Event Store** tab to show logged SQLite tables and database metrics.

---

## 3. Fallback Instructions
If the Streamlit browser connection fails or port conflicts occur:
1.  Close the terminals, free ports `8000` and `8501`, and run `python run_demo.py` again.
2.  Alternatively, run a single simulation step in Python to show raw stdout:
    ```bash
    python run_phase7.py
    ```
    This prints a chronological event timeline verifying edge validations, gateway decisions, and database logging.
