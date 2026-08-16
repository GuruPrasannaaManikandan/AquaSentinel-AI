import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import requests
import json

# Setup page layout
st.set_page_config(
    page_title="Aquatic Ecosystem IoT & AIS Gateway Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (CSS Injection for Sleek Design)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .status-badge {
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        text-transform: uppercase;
        display: inline-block;
    }
    
    .badge-normal { background: #2E7D32; color: white; }
    .badge-warning { background: #F57C00; color: white; }
    .badge-critical { background: #C62828; color: white; }
    .badge-anomaly { background: #6A1B9A; color: white; }
    .badge-fault { background: #424242; color: white; }
</style>
""", unsafe_allow_html=True)

# API endpoint helper
API_URL = "http://localhost:8000"

def fetch_json(endpoint, method="GET", data=None):
    try:
        if method == "GET":
            r = requests.get(f"{API_URL}{endpoint}", timeout=2.0)
        else:
            r = requests.post(f"{API_URL}{endpoint}", json=data, timeout=2.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

# Page title
st.title("🌊 IoT Aquatic Monitoring & Artificial Immune System Gateway")
st.markdown("Real-time telemetry, negative selection anomaly filtration, and rule-based evidence-fusion decision logs.")

# Fetch system status and active devices
health = fetch_json("/health")
devices = fetch_json("/devices") or []
stats = fetch_json("/system/status") or {
    "active_devices_count": 0, "total_telemetry_records": 0, "total_warnings": 0, "total_criticals": 0, "total_anomalies": 0, "unacknowledged_alerts_count": 0
}

# 1. System Overview Metrics
st.subheader("📊 System Overview KPIs")
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Active Devices Online", f"{stats['active_devices_count']} / 2", help="Simulated ESP32 microcontroller nodes")
with col2:
    st.metric("Telemetry Event Logs", stats["total_telemetry_records"])
with col3:
    st.metric("Total Warnings Emit", stats["total_warnings"])
with col4:
    st.metric("Critical Alarms Raised", stats["total_criticals"])
with col5:
    st.metric("Unacknowledged Alerts", stats["unacknowledged_alerts_count"])

st.divider()

# Sidebar: Simulation and manual control channels
st.sidebar.header("🛠️ Simulation Controls")

# Simulation runner status toggle
sim_run = st.sidebar.button("🟢 Start Background Simulation")
sim_stop = st.sidebar.button("🔴 Stop Background Simulation")

if sim_run:
    fetch_json("/simulation/start", "POST")
    st.rerun()
if sim_stop:
    fetch_json("/simulation/stop", "POST")
    st.rerun()

st.sidebar.divider()

# Selected Device context
device_ids = [d["device_id"] for d in devices] if devices else ["AQUA_FRESH_001", "AQUA_MARINE_001"]
selected_id = st.sidebar.selectbox("Device Selection", device_ids)

# Trigger Single Step
if st.sidebar.button("⚡ Trigger Single-Step Cycle"):
    res = fetch_json("/simulation/cycle", "POST")
    if res:
        st.rerun()
    else:
        st.sidebar.error("Step execution failed.")

# Active scenario configurations
scenario_opts = ["NORMAL", "KNOWN_BLOOM_RISK", "UNUSUAL_ENVIRONMENTAL_CONDITION", "SENSOR_FAULT", "GRADUAL_ENVIRONMENTAL_DEGRADATION", "SUDDEN_EVENT"]

# Query active scenarios from the backend to initialize default selectbox index
active_scenarios = fetch_json("/simulation/scenarios") or {"AQUA_FRESH_001": "NORMAL", "AQUA_MARINE_001": "NORMAL"}
current_scen = active_scenarios.get(selected_id, "NORMAL")

try:
    default_idx = scenario_opts.index(current_scen)
except ValueError:
    default_idx = 0

active_scen = st.sidebar.selectbox("Set Environmental Scenario", scenario_opts, index=default_idx)

if st.sidebar.button("💾 Apply Scenario Selection"):
    fetch_json("/simulation/scenario", "POST", {"device_id": selected_id, "scenario": active_scen})
    st.rerun()

st.sidebar.divider()

# Command dispatch override controls
st.sidebar.header("🕹️ Actuator Commands Override")
cmd_opts = ["REQUEST_READING", "SET_SAMPLING_INTERVAL", "ACTIVATE_BUZZER", "DEACTIVATE_BUZZER", "ACTIVATE_RELAY", "DEACTIVATE_RELAY", "RESTART_DEVICE", "RUN_DIAGNOSTICS"]
selected_cmd = st.sidebar.selectbox("Select Action Command", cmd_opts)
cmd_payload = {}
if selected_cmd == "SET_SAMPLING_INTERVAL":
    sec = st.sidebar.slider("Sampling Interval (seconds)", 5, 60, 10)
    cmd_payload = {"interval": sec}

if st.sidebar.button("📤 Send Command Override"):
    res = fetch_json(f"/devices/{selected_id}/command", "POST", {"command": selected_cmd, "payload": cmd_payload})
    if res:
        st.rerun()
    else:
        st.sidebar.error("Failed to send command.")

# Main page layouts split by tabs
tab1, tab2, tab3, tab4 = st.tabs(["📟 Live Telemetry", "🧠 Intelligence & Fusion Panel", "📈 Historical Trends", "🚨 Alert History & Event Store"])

# Load latest values
latest_data = fetch_json(f"/devices/{selected_id}/latest") or {"telemetry": None, "decision": None}
telemetry = latest_data.get("telemetry")
decision = latest_data.get("decision")

# Get device state details
dev_details = None
for d in devices:
    if d["device_id"] == selected_id:
        dev_details = d
        break

with tab1:
    st.subheader(f"Telemetry Status: {selected_id}")
    
    if dev_details:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ecosystem Type", dev_details["ecosystem_type"])
        c2.metric("Dataset Route", dev_details["dataset_route"].upper())
        c3.metric("Firmware Version", dev_details["firmware_version"])
        
        # State machine color formatting
        fsm_st = dev_details["status"]
        if fsm_st in ["BOOT", "INITIALIZING", "CONNECTING", "RECOVERING"]:
            badge_html = f'<span class="status-badge badge-warning">{fsm_st}</span>'
        elif fsm_st == "ERROR":
            badge_html = f'<span class="status-badge badge-critical">{fsm_st}</span>'
        else:
            badge_html = f'<span class="status-badge badge-normal">{fsm_st}</span>'
        c4.markdown(f"**ESP32 FSM State:**<br>{badge_html}", unsafe_allow_html=True)
    
    st.divider()
    
    if telemetry:
        # Display Sensor dials
        sc1, sc2, sc3, sc4, sc5 = st.columns(5)
        
        with sc1:
            val = telemetry.get("temperature_c")
            st.metric("Temperature (°C)", f"{val:.2f}" if val is not None else "N/A")
        with sc2:
            val = telemetry.get("salinity_ppt")
            st.metric("Salinity / TDS (ppt)", f"{val:.2f}" if val is not None else "N/A")
        with sc3:
            val = telemetry.get("ph")
            st.metric("Water pH", f"{val:.2f}" if val is not None else "N/A")
        with sc4:
            val = telemetry.get("turbidity_ntu")
            st.metric("Turbidity (NTU)", f"{val:.2f}" if val is not None else "N/A")
        with sc5:
            val = telemetry.get("dissolved_oxygen_mg_l")
            st.metric("Dissolved Oxygen (mg/L)", f"{val:.2f}" if val is not None else "N/A")

        # Map display
        st.subheader("📍 Deployment Location")
        map_df = pd.DataFrame([{
            "lat": telemetry["latitude"],
            "lon": telemetry["longitude"]
        }])
        st.map(map_df, zoom=10)
    else:
        st.info("No telemetry logs received yet. Start the simulation to poll data.")

with tab2:
    st.subheader("🧠 Subsystem Intelligence Metrics")
    
    if decision:
        mc1, mc2 = st.columns(2)
        
        with mc1:
            st.markdown("### 🤖 Supervised Machine Learning")
            if str(decision["ml_predicted_class"]).upper() in ["BYPASSED", "SKIPPED", "UNAVAILABLE", "NOT_RUN"]:
                st.metric("Predicted Class ID", "UNAVAILABLE")
                st.metric("Prediction Confidence", "N/A")
                st.metric("Dangerous Class Target?", "N/A")
            else:
                st.metric("Predicted Class ID", decision["ml_predicted_class"])
                st.metric("Prediction Confidence", f"{decision['ml_confidence']:.2%}")
                st.metric("Dangerous Class Target?", "YES" if decision["ml_dangerous_class"] == 1 else "NO")
            st.caption(f"Model ID: {decision['ml_model_id']}")

        with mc2:
            st.markdown("### 🛡️ Artificial Immune System (NSA)")
            if str(decision["ais_model_id"]).upper() in ["BYPASSED", "SKIPPED", "UNAVAILABLE", "NOT_RUN"]:
                st.markdown("**Anomaly Status:** <span style='color:#757575;font-weight:bold;'>⚪ UNAVAILABLE (Sensor Fault)</span>", unsafe_allow_html=True)
                st.metric("Anomaly Score", "N/A")
                st.metric("Nearest Detector Distance", "N/A")
                st.metric("Matched Detectors Count", "N/A")
            else:
                anom_flag = decision["ais_is_anomaly"]
                if anom_flag == 1:
                    st.markdown("**Anomaly Status:** <span style='color:#E53935;font-weight:bold;'>⚠️ NON-SELF (Anomaly Flagged)</span>", unsafe_allow_html=True)
                else:
                    st.markdown("**Anomaly Status:** <span style='color:#43A047;font-weight:bold;'>✅ SELF (In-Distribution)</span>", unsafe_allow_html=True)
                
                st.metric("Anomaly Score", f"{decision['ais_anomaly_score']:.4f}")
                st.metric("Nearest Detector Distance", f"{decision['ais_nearest_distance']:.4f}")
                st.metric("Matched Detectors Count", decision["ais_matched_detectors"])
            st.caption(f"AIS Version: {decision['ais_model_id']}")

        st.divider()

        st.subheader("🔀 Evidence Fusion Logic Outcome")
        f_state = decision["final_state"]
        
        # Format colors
        if f_state == "NORMAL":
            state_color = "badge-normal"
        elif f_state == "WARNING":
            state_color = "badge-warning"
        elif f_state == "CRITICAL":
            state_color = "badge-critical"
        elif f_state == "UNKNOWN_ANOMALY":
            state_color = "badge-anomaly"
        else:
            state_color = "badge-fault"

        st.markdown(f"<h4>Final Emitted State: <span class='status-badge {state_color}'>{f_state}</span></h4>", unsafe_allow_html=True)
        st.markdown(f"**Reason Code:** `{decision['reason_code']}`")
        st.markdown(f"**Reasoning Explanation:** {decision['reasoning']}")
        st.markdown(f"**Confidence Band:** `{decision['confidence_band']}`")
        st.caption(f"Fusion Version: {decision['fusion_version']}")

        st.divider()

        # Actuator State indicators
        st.subheader("🔌 Actuator Output States")
        act_summary = latest_data.get("decision", {}).get("actuator_summary") or "LEDs(G=N/A, Y=N/A, R=N/A), Buzzer=N/A, Pump=N/A"
        
        ac1, ac2, ac3, ac4, ac5 = st.columns(5)
        # Parse states
        g_led = "ON" if "G=ON" in act_summary else ("OFF" if "G=OFF" in act_summary else "N/A")
        y_led = "ON" if "Y=ON" in act_summary else ("OFF" if "Y=OFF" in act_summary else "N/A")
        r_led = "ON" if "R=ON" in act_summary else ("OFF" if "R=OFF" in act_summary else "N/A")
        buzzer = "ON" if "Buzzer=ON" in act_summary else ("OFF" if "Buzzer=OFF" in act_summary else "N/A")
        pump = "ON" if "Pump=ON" in act_summary else ("OFF" if "Pump=OFF" in act_summary else "N/A")

        ac1.metric("Green LED Indicator", g_led)
        ac2.metric("Yellow LED Indicator", y_led)
        ac3.metric("Red LED Indicator", r_led)
        ac4.metric("Piezo Buzzer Status", buzzer)
        ac5.metric("Aerator Pump Relay", pump)
    else:
        st.info("Inference decision has not run yet. Poll sensors to trigger.")

with tab3:
    st.subheader("📈 Environmental Sensor Historical Charts")
    hist_telemetry = fetch_json(f"/devices/{selected_id}/telemetry")
    
    if hist_telemetry and len(hist_telemetry) > 0:
        df = pd.DataFrame(hist_telemetry)
        # Sort by timestamp
        df = df.sort_values("timestamp")
        
        # Time-series charts
        st.markdown("#### Water Temperature trend")
        st.line_chart(df, x="timestamp", y="temperature_c")
        
        st.markdown("#### Salinity trend")
        st.line_chart(df, x="timestamp", y="salinity_ppt")

        st.markdown("#### pH Levels trend")
        st.line_chart(df, x="timestamp", y="ph")

        st.markdown("#### Turbidity (NTU) trend")
        st.line_chart(df, x="timestamp", y="turbidity_ntu")

        st.markdown("#### Dissolved Oxygen (mg/L) trend")
        st.line_chart(df, x="timestamp", y="dissolved_oxygen_mg_l")
    else:
        st.info("No historical telemetry records logged in database yet.")

with tab4:
    st.subheader("🚨 Persisted System Alerts Log")
    unack_alerts = fetch_json("/alerts?acknowledged=false")
    
    if unack_alerts and len(unack_alerts) > 0:
        for alert in unack_alerts:
            alert_id = alert["id"]
            sev = alert["severity"]
            with st.container():
                st.markdown(f"**Alert ID {alert_id} | Severity: {sev} | Device: {alert['device_id']}**")
                if sev == "HIGH":
                    st.error(alert["message"])
                else:
                    st.warning(alert["message"])
                st.caption(f"Reason Code: {alert['reason_code']} | Timestamp: {alert['timestamp']}")
                if st.button(f"Acknowledge Alert {alert_id}", key=f"ack_{alert_id}"):
                    fetch_json(f"/alerts/{alert_id}/acknowledge", "POST")
                    st.rerun()
                st.divider()
    else:
        st.success("All clear! No unacknowledged alerts logged.")

    st.divider()

    st.subheader("📂 Full Database Event Logs")
    # Show Raw decisions logs
    decisions_hist = fetch_json(f"/devices/{selected_id}/decisions")
    if decisions_hist and len(decisions_hist) > 0:
        st.markdown("#### Latest Fusion decisions Table")
        st.dataframe(pd.DataFrame(decisions_hist).tail(20))
    else:
        st.caption("No decisions logged in database.")
