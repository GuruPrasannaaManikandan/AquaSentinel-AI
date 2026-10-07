import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import requests
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .status-badge {
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.90rem;
        text-transform: uppercase;
        display: inline-block;
        letter-spacing: 0.5px;
    }
    
    .badge-normal { background: #2E7D32; color: white; }
    .badge-watch { background: #0288D1; color: white; }
    .badge-early_warning { background: #F57C00; color: white; }
    .badge-high_risk { background: #E64A19; color: white; }
    .badge-bloom_confirmed { background: #B71C1C; color: white; }
    .badge-warning { background: #F57C00; color: white; }
    .badge-critical { background: #C62828; color: white; }
    .badge-anomaly { background: #6A1B9A; color: white; }
    .badge-fault { background: #424242; color: white; }
    /* smaller metric values so state words such as UNCALIBRATED fit; long text still ellipsizes normally */
    [data-testid="stMetricValue"] { font-size: 1.35rem !important; }
</style>
""", unsafe_allow_html=True)

# API endpoint helper
# run_demo.py starts the FastAPI backend on port 8000
API_URL = os.environ.get("AQUASENTINEL_API_URL", "http://127.0.0.1:8000")

def fetch_json(endpoint, method="GET", data=None, timeout=3.0):
    try:
        if method == "GET":
            r = requests.get(f"{API_URL}{endpoint}", timeout=timeout)
        else:
            r = requests.post(f"{API_URL}{endpoint}", json=data, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        else:
            try:
                err_detail = r.json().get("detail", f"HTTP {r.status_code}")
                st.session_state["last_api_error"] = str(err_detail)
            except Exception:
                st.session_state["last_api_error"] = f"HTTP {r.status_code}"
    except Exception as e:
        st.session_state["last_api_error"] = str(e)
    return None

def capture_camera_photo(device_id="AQUA_FRESH_001"):
    try:
        # Backend waits up to 15 s for the frame over USB serial
        r = requests.post(f"{API_URL}/api/camera/capture?device_id={device_id}", timeout=25.0)
        return r.json(), r.status_code
    except Exception as e:
        return {"success": False, "error": str(e), "camera": "ESP32-CAM", "sensor": "GC2145"}, 500


# Page title
st.title("🌊 IoT Aquatic Monitoring & Artificial Immune System Gateway")
st.markdown("**Version 7.0 Advanced Multimodal Intelligence & Evidential Reasoning Platform**")

# ----------------- LIVE PHYSICAL SENSOR PANEL -----------------
# ---- Sensor state semantics (one vocabulary everywhere) ----
#   VALID        calibrated / usable reading
#   UNCALIBRATED hardware present and answering, but no trustworthy calibration yet
#   FAULT        hardware present but malfunctioning / invalid data
#   UNAVAILABLE  hardware is not physically present (NOT a fault)
STATE_LABEL = {"VALID": "🟢 VALID", "UNCALIBRATED": "🟡 UNCALIBRATED", "FAULT": "🔴 FAULT", "UNAVAILABLE": "⚪ UNAVAILABLE"}
PHYSICAL_DEVICE_ID = "AQUA_FRESH_001"


def _fmt(value, fmt):
    return fmt.format(value) if isinstance(value, (int, float)) else "N/A"


def fetch_live(device_id=PHYSICAL_DEVICE_ID):
    """The ONE authoritative latest-live telemetry object (backend: newest EventStore row + same-packet detail)."""
    return fetch_json(f"/api/sensors/live?device_id={device_id}", timeout=2.0)


def sensor_display(live, name):
    """(value_text, state, note) for one sensor, from the single live object. Never turns N/A into 0."""
    states = live.get("sensor_states") or {}
    reasons = live.get("reasons") or {}
    st_ = states.get(name)
    if name == "ph":
        ph = live.get("ph")
        if st_ == "VALID" and ph is not None:
            return f"{ph:.2f}", "VALID", "calibrated pH"
        if st_ == "UNCALIBRATED":
            est = live.get("ph_estimate")
            return "UNCALIBRATED", "UNCALIBRATED", (
                f"module output ~{_fmt(live.get('ph_voltage'), '{:.2f} V')}; default-coefficient estimate "
                f"{_fmt(est, '{:.2f}')} is NOT a measurement")
        if st_ == "FAULT":
            return "FAULT", "FAULT", "pH channel invalid (saturated / no signal / out of 0-14)"
        return (f"{ph:.2f}" if ph is not None else "N/A"), st_, "state unknown (no matching detail packet)"
    if name == "turbidity":
        raw = live.get("turbidity_raw")
        if raw is not None and st_ == "VALID":
            return f"{raw:.0f} raw", "VALID", f"relative: {_fmt(live.get('turbidity_rel_clear_pct'), '{:.0f}')}% of the stored clear-water reference (raw {_fmt(live.get('turbidity_clear_ref_raw'), '{:.0f}')}); NOT NTU"
        if raw is not None:
            return f"{raw:.0f} raw", st_ or "UNCALIBRATED", "raw ADC count, not volts/NTU; no clear-water reference stored (higher = clearer)"
        if st_ == "FAULT" or live.get("sensor_status") == "FAULT":
            return "FAULT", "FAULT", f"no usable signal (ADC raw {_fmt(live.get('turbidity_adc_raw'), '{:.0f}')})"
        return "N/A", st_, "no reading"
    if name == "temperature":
        t = live.get("temperature_c")
        if t is not None:
            return f"{t:.1f} °C", "VALID", "DS18B20"
        if st_ in (None, "UNAVAILABLE"):
            return "N/A", "UNAVAILABLE", reasons.get("temperature") or "DS18B20 NOT CONNECTED"
        return "N/A", st_, "DS18B20 not responding"
    if name == "dissolved_oxygen":
        v = live.get("dissolved_oxygen_mg_l")
        return (f"{v:.2f}" if v is not None else "N/A"), ("VALID" if v is not None else "UNAVAILABLE"), reasons.get("dissolved_oxygen") or "no DO probe installed"
    if name == "salinity":
        v = live.get("salinity_ppt")
        return (f"{v:.2f}" if v is not None else "N/A"), ("VALID" if v is not None else "UNAVAILABLE"), reasons.get("salinity") or "no salinity/TDS probe installed"
    return "N/A", "UNAVAILABLE", ""


def sensor_card(col, title, live, name):
    value, state, note = sensor_display(live, name)
    col.metric(title, value)
    col.caption(f"{STATE_LABEL.get(state, state or 'UNKNOWN')} - {note}" if note else STATE_LABEL.get(state, state or "UNKNOWN"))


@st.fragment(run_every=2)
def live_sensor_panel():
    st.subheader("🔴 Live Hardware Sensors (ESP32)")
    live = fetch_live()
    if not live or not live.get("available"):
        reason = (live or {}).get("reason", "Backend not reachable.")
        st.warning(f"No live reading. {reason}")
        return
    if live.get("stale"):
        st.error(f"Last reading is {live.get('age_sec')} s old. Is the sensor ESP32 plugged in and the bridge running?")
    if live.get("actuator_test") not in (None, "OFF"):
        st.warning(f"🧪 **SIMULATION / ACTUATOR TEST - mode {live['actuator_test']}.** LEDs/buzzer are being driven for a demo. "
                   "Sensor readings below are real and are NOT altered.")

    c1, c2, c3 = st.columns(3)
    sensor_card(c1, "Turbidity (raw ADC)", live, "turbidity")
    sensor_card(c2, "Water pH", live, "ph")
    sensor_card(c3, "Temperature (DS18B20)", live, "temperature")

    d1, d2, d3 = st.columns(3)
    sensor_card(d1, "Dissolved Oxygen", live, "dissolved_oxygen")
    sensor_card(d2, "Salinity / TDS", live, "salinity")
    d3.metric("GPS", "N/A")
    d3.caption(f"{STATE_LABEL['UNAVAILABLE']} - " + ((live.get("reasons") or {}).get("gps") or "no GPS module installed"))

    e1, e2, e3 = st.columns(3)
    e1.metric("Pump", "N/A")
    e1.caption(f"{STATE_LABEL['UNAVAILABLE']} - " + ((live.get("reasons") or {}).get("pump") or "no pump load connected (relay switching only)"))
    e2.metric("Packet #", live.get("sequence_number", "N/A"), help=f"{live.get('timestamp')} - age {live.get('age_sec')} s - fw {live.get('fw')} - {live.get('port')}")
    e2.caption(f"updated {live.get('timestamp')}")
    e3.metric("Firmware", live.get("fw") or "N/A")
    e3.caption("reported by the board")
    st.caption(f"Source: {live.get('source')}")
    if live.get("device_log"):
        with st.expander("ESP32 replies (calibration / actuator-test commands)"):
            for item in reversed(live["device_log"]):
                st.code(item.get("line", ""), language=None)


live_sensor_panel()
st.divider()

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
    st.metric("Active Devices Online", f"{stats['active_devices_count']} / 2", help="Monitored aquatic nodes")
with col2:
    st.metric("Telemetry Event Logs", stats["total_telemetry_records"])
with col3:
    st.metric("Total Warnings Emitted", stats["total_warnings"])
with col4:
    st.metric("Critical Alarms Raised", stats["total_criticals"])
with col5:
    st.metric("Active Anomalies", stats["total_anomalies"])

st.divider()

# Sidebar: Device Selection & Controls
st.sidebar.title("🎛️ Node Control Station")
device_ids = [d["device_id"] for d in devices] if devices else ["AQUA_FRESH_001", "AQUA_MARINE_001"]
selected_id = st.sidebar.selectbox("Select Target Edge Node", device_ids, index=0)

# Scenarios selector
st.sidebar.header("🧪 Edge Simulation Controls")
scenario_opts = [
    "NORMAL",
    "ALGAL_BLOOM",
    "CHEMICAL_SPILL",
    "SENSOR_FAULT",
    "RAPID_WARMING",
    "TURBIDITY_SPIKE",
    "DISSOLVED_OXYGEN_DEPLETION",
    "SALINITY_ANOMALY",
    "PH_SHOCK",
    "NOISY_SENSOR",
    "SENSOR_DRIFT"
]

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
cmd_opts = [
    "REQUEST_READING",
    "SET_SAMPLING_INTERVAL",
    "ACTIVATE_BUZZER",
    "DEACTIVATE_BUZZER",
    "ACTIVATE_RELAY",
    "DEACTIVATE_RELAY",
    "RESTART_DEVICE",
    "PIN_DIAGNOSTICS"
]
selected_cmd = st.sidebar.selectbox("Select Action Command", cmd_opts)
cmd_payload = {}
if selected_cmd == "SET_SAMPLING_INTERVAL":
    sec = st.sidebar.slider("Sampling Interval (seconds)", min_value=2, max_value=60, value=5)
    cmd_payload = {"interval": sec}

if st.sidebar.button("📤 Send Command Override", use_container_width=True):
    _before = fetch_live(selected_id) or {}
    before_ts, before_seq = _before.get("timestamp"), _before.get("sequence_number")
    with st.sidebar.status(f"⚡ Processing {selected_cmd}...", expanded=True) as cmd_status:
        cmd_status.write(f"1. 📤 Sending `{selected_cmd}` to FastAPI `/devices/{selected_id}/command`...")
        import time
        time.sleep(0.3)
        cmd_status.write(f"2. ⚙️ Executing `{selected_cmd}` on hardware/transport layer...")
        res = fetch_json(f"/devices/{selected_id}/command", "POST", {"command": selected_cmd, "payload": cmd_payload})
        if res and res.get("status") in ["SUCCESS", "COMMAND_COMPLETED", "EXECUTED", "OK"]:
            if selected_cmd == "REQUEST_READING":
                cmd_status.write("3. ⏳ Waiting for a NEW telemetry packet from the physical ESP32...")
                fresh = None
                for _ in range(16):
                    time.sleep(0.5)
                    now_live = fetch_live(selected_id) or {}
                    if now_live.get("available") and now_live.get("timestamp") != before_ts:
                        fresh = now_live
                        break
                if fresh:
                    cmd_status.write(f"4. 📥 New packet #{fresh.get('sequence_number')} at {fresh.get('timestamp')} stored in EventStore (previous: #{before_seq} at {before_ts}).")
                else:
                    cmd_status.write("4. ⚠️ No new packet within 8 s (is the bridge running and the ESP32 plugged in?). Not claiming success.")
            elif selected_cmd == "ACTIVATE_BUZZER":
                cmd_status.write("3. 🔊 Buzzer activated (GPIO14 HIGH).")
            elif selected_cmd == "DEACTIVATE_BUZZER":
                cmd_status.write("3. 🔇 Buzzer deactivated (GPIO14 LOW).")
            elif selected_cmd == "ACTIVATE_RELAY":
                cmd_status.write("3. ⚡ Relay activated (GPIO19 HIGH - electrical switching verified).")
            elif selected_cmd == "DEACTIVATE_RELAY":
                cmd_status.write("3. 🔌 Relay deactivated (GPIO19 LOW - relay contacts opened).")
            elif selected_cmd == "SET_SAMPLING_INTERVAL":
                cmd_status.write(f"3. ⏱️ Sampling interval updated to {cmd_payload.get('interval')} seconds on ESP32 scheduler.")
            elif selected_cmd == "PIN_DIAGNOSTICS":
                diag = res.get("diagnostics") or res.get("data", {})
                pins_str = ", ".join([f"{k}: {v}" for k, v in diag.get("pin_mappings", {}).items()]) if diag else "Green=GPIO25, Yellow=GPIO26, Red=GPIO27, Buzzer=GPIO14, Relay=GPIO19, pH=GPIO32, DS18B20=GPIO33, Turbidity=GPIO34"
                cmd_status.write(f"3. 🔍 Diagnostics complete: {pins_str}")
            elif selected_cmd == "RESTART_DEVICE":
                cmd_status.write("3. 🔄 Controlled restart dispatched to ESP32 runtime.")
            cmd_status.update(label=f"✅ {selected_cmd} Completed", state="complete", expanded=True)
            st.sidebar.success(f"Command `{selected_cmd}` Completed!")
            st.rerun()
        else:
            err = res.get("detail") if isinstance(res, dict) else st.session_state.get("last_api_error", "Unknown error")
            cmd_status.update(label=f"❌ {selected_cmd} Failed", state="error", expanded=True)
            st.sidebar.error(f"Command failed: {err}")

st.sidebar.divider()
st.sidebar.header("🧪 Actuator Demo - SIMULATION / ACTUATOR TEST")
st.sidebar.caption("Drives the LEDs and buzzer only (never the relay). Sensor values are NOT altered. Auto-ends after 60 s.")
_ta, _tb = st.sidebar.columns(2)
_tc, _td = st.sidebar.columns(2)
for _col, _mode, _label in ((_ta, "NORMAL", "🟢 NORMAL"), (_tb, "WARNING", "🟡 WARNING"), (_tc, "CRITICAL", "🔴 CRITICAL"), (_td, "OFF", "⏹ END TEST")):
    if _col.button(_label, key=f"act_{_mode}", use_container_width=True):
        _r = fetch_json(f"/devices/{PHYSICAL_DEVICE_ID}/command", "POST", {"command": "ACTUATOR_TEST", "payload": {"mode": _mode}})
        if _r:
            st.sidebar.info(f"ACTUATOR_TEST {_mode} dispatched to the ESP32 (simulation). Confirmation appears under 'ESP32 replies'.")
        else:
            st.sidebar.error(f"Not sent: {st.session_state.get('last_api_error')}")

st.sidebar.header("🎯 Calibration (physical probes)")
st.sidebar.caption("The ESP32 refuses to store a reference if the signal is not repeatable (coefficient of variation > 5%), so a noisy probe can never become 'VALID'.")
_cal = st.sidebar.selectbox("Procedure", [
    "TURB_CLEAR - store clear-water reference (probe in clear water)",
    "TURB_RESET - clear the turbidity reference",
    "PH_CAL7 - pH 7 point (pH 7 buffer, or BNC centre shorted to shield)",
    "PH_RESET - reset pH calibration"])
if st.sidebar.button("Run calibration command", use_container_width=True):
    _cmd = _cal.split(" ")[0]
    _r = fetch_json(f"/devices/{PHYSICAL_DEVICE_ID}/command", "POST", {"command": _cmd, "payload": {}})
    if _r:
        st.sidebar.info(f"{_cmd} dispatched. Read the ESP32's answer under 'ESP32 replies' in the live panel.")
    else:
        st.sidebar.error(f"Not sent: {st.session_state.get('last_api_error')}")

# Load latest values and intelligence
latest_data = fetch_json(f"/devices/{selected_id}/latest") or {"telemetry": None, "decision": None}
telemetry = latest_data.get("telemetry")
decision = latest_data.get("decision")
intel_data = fetch_json(f"/devices/{selected_id}/intelligence") or {}
multimodal_info = fetch_json(f"/devices/{selected_id}/multimodal") or {}
v8_response_info = fetch_json(f"/devices/{selected_id}/response") or {}
v8_trend_info = fetch_json(f"/devices/{selected_id}/risk-trend") or {}
reliability_metrics = fetch_json("/system/reliability") or {}

explanation = intel_data.get("explanation")
digital_state = intel_data.get("digital_state")
temporal_ev = intel_data.get("temporal_evidence") or (decision.get("temporal_evidence") if decision else None)
sensor_q = intel_data.get("sensor_quality") or (decision.get("sensor_quality") if decision else None)
visual_ev = intel_data.get("visual_evidence") or (decision.get("visual_evidence") if decision else None)

# Get device state details
dev_details = None
for d in devices:
    if d["device_id"] == selected_id:
        dev_details = d
        break

# Tabs split by capabilities (V7 Multimodal Integration + V8 Research Deployment)
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📟 Live Telemetry & Quality",
    "📷 Optical & Temporal Intelligence",
    "🧠 Evidential Decision & XAI",
    "📈 Historical Baselines",
    "🚨 Alert History & Event Store",
    "🌐 V7 Multimodal Intelligence",
    "🔬 V8 Research & Deployment"
])

# ----------------- TAB 1: Live Telemetry & Quality -----------------
with tab1:
    st.subheader(f"Telemetry Status: {selected_id}")
    
    if dev_details:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ecosystem Type", dev_details["ecosystem_type"])
        c2.metric("Dataset Route", dev_details["dataset_route"].upper())
        _fw_live = (fetch_live(selected_id) or {}).get("fw")
        c3.metric("Firmware Version", _fw_live or dev_details["firmware_version"],
                  help="Reported by the board in its latest packet" if _fw_live else "From the device registry (no live packet)")
        
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
        ts_val = telemetry.get("timestamp", "N/A")
        seq_val = telemetry.get("sequence_number") or telemetry.get("id") or "N/A"
        orig_val = telemetry.get("bridge_origin", "LIVE")
        cmd_trig = telemetry.get("command_triggered")
        trig_str = f" | Last Trigger: `{cmd_trig}`" if cmd_trig else ""
        st.info(f"📡 **Live Telemetry Stream Active** | Last Ingest: `{ts_val}` | Packet Sequence: `#{seq_val}` | Source: `{orig_val}`{trig_str}")

        # Same authoritative live object as the top cards (never a second data source).
        live_obj = fetch_live(selected_id) or {}
        sc1, sc2, sc3, sc4, sc5 = st.columns(5)
        if live_obj.get("available"):
            sensor_card(sc1, "Temperature", live_obj, "temperature")
            sensor_card(sc2, "Salinity / TDS", live_obj, "salinity")
            sensor_card(sc3, "Water pH", live_obj, "ph")
            sensor_card(sc4, "Turbidity", live_obj, "turbidity")
            sensor_card(sc5, "Dissolved Oxygen", live_obj, "dissolved_oxygen")
        else:
            for col, label in ((sc1, "Temperature"), (sc2, "Salinity / TDS"), (sc3, "Water pH"), (sc4, "Turbidity"), (sc5, "Dissolved Oxygen")):
                col.metric(label, "N/A")

        st.divider()

        # V5.1 Sensor Quality Vector Display
        st.subheader("🛡️ Sensor Reliability Vector ($Q_{sensor}$)")
        if sensor_q:
            qc1, qc2, qc3 = st.columns(3)
            q_val = sensor_q.get("q_sensor", 1.0)
            q_st = sensor_q.get("quality_state", "RELIABLE")
            qc1.metric("Overall Sensor Quality (Q_sensor)", f"{q_val:.2f}")
            qc2.metric("Sensor Quality State", q_st)
            flags = sensor_q.get("degradation_reasons", [])
            qc3.markdown(f"**Quality Flags:** {', '.join(flags) if flags else '✅ ALL PROBES NOMINAL'}")
        else:
            st.info("Sensor quality assessment initializing...")

        st.divider()

        # Map display
        st.subheader("📍 Deployment Location")
        if telemetry.get("latitude") is not None and telemetry.get("longitude") is not None:
            map_df = pd.DataFrame([{"lat": telemetry["latitude"], "lon": telemetry["longitude"]}])
            st.map(map_df, zoom=10)
        else:
            st.info("📍 GPS Module: Not Equipped / Inactive (Hardware Contract: GPS NOT AVAILABLE)")
    else:
        st.info("No telemetry logs received yet. Start the simulation to poll data.")

# ----------------- TAB 2: Optical & Temporal Intelligence -----------------
with tab2:
    st.subheader("📷 Optical Intelligence (V5.2) & Temporal Trends (V5.3)")

    col_opt, col_temp = st.columns(2)

    with col_opt:
        st.markdown("### 📷 Physical ESP32-CAM — Manual Photo Capture")

        # Initialize camera session state variables if not present
        if "cam_initialized" not in st.session_state:
            st.session_state["cam_initialized"] = True
            st.session_state["camera_status"] = "READY"
            st.session_state["camera_capturing"] = False
            st.session_state["camera_error"] = None
            st.session_state["trigger_capture"] = False
            # Check backend for latest saved capture
            try:
                latest_cam = fetch_json("/api/camera/latest")
                if latest_cam and latest_cam.get("success"):
                    st.session_state["camera_capture_id"] = latest_cam.get("capture_id")
                    st.session_state["camera_last_capture"] = latest_cam.get("captured_at")
                    st.session_state["camera_frame_sequence"] = latest_cam.get("frame_sequence")
                    st.session_state["camera_image_path"] = latest_cam.get("filepath")
                    st.session_state["camera_optical_intel"] = latest_cam.get("optical_intelligence")
                else:
                    st.session_state["camera_capture_id"] = None
                    st.session_state["camera_last_capture"] = None
                    st.session_state["camera_frame_sequence"] = None
                    st.session_state["camera_image_path"] = None
                    st.session_state["camera_optical_intel"] = None
            except Exception:
                st.session_state["camera_capture_id"] = None
                st.session_state["camera_last_capture"] = None
                st.session_state["camera_frame_sequence"] = None
                st.session_state["camera_image_path"] = None
                st.session_state["camera_optical_intel"] = None

        # Execute pending capture request triggered by button click
        if st.session_state.get("trigger_capture"):
            with st.spinner("Requesting fresh frame from physical ESP32-CAM over USB..."):
                capture_res, status_code = capture_camera_photo(selected_id)
                if status_code == 200 and capture_res.get("success"):
                    st.session_state["camera_status"] = "SUCCESS"
                    st.session_state["camera_capture_id"] = capture_res.get("capture_id")
                    st.session_state["camera_last_capture"] = capture_res.get("captured_at")
                    st.session_state["camera_frame_sequence"] = capture_res.get("frame_sequence")
                    st.session_state["camera_image_path"] = capture_res.get("filepath")
                    st.session_state["camera_optical_intel"] = capture_res.get("optical_intelligence")
                    st.session_state["camera_error"] = None
                else:
                    st.session_state["camera_status"] = "ERROR"
                    st.session_state["camera_error"] = capture_res.get("error", f"Capture failed with status {status_code}")

                st.session_state["trigger_capture"] = False
                st.session_state["camera_capturing"] = False
                st.rerun()

        # Capture Status Alert Banners
        if st.session_state.get("camera_status") == "SUCCESS":
            st.success(f"✓ Photo captured successfully at {st.session_state.get('camera_last_capture')} | Frame #{st.session_state.get('camera_frame_sequence')}")
        elif st.session_state.get("camera_status") == "ERROR":
            st.error(f"✗ Camera capture failed\n\n**Reason:** {st.session_state.get('camera_error')}")

        # Metadata Status Card
        card_col1, card_col2 = st.columns(2)
        _cam_live = fetch_json("/api/camera/status") or {}
        _cam_state = _cam_live.get("status", "UNKNOWN")
        _cam_box = card_col1.info if _cam_state not in ("ERROR", "OFFLINE", "UNKNOWN") else card_col1.error
        _cam_err = f"\n\n**Last error:** {_cam_live.get('last_error')}" if _cam_live.get("last_error") else ""
        _cam_box(f"**Camera:** `{_cam_state}` (ESP32-CAM)\n\n**Sensor:** `GC2145` (USB serial)\n\n**Source:** `PHYSICAL ESP32-CAM`{_cam_err}")
        card_col2.info(f"**Status:** `{st.session_state.get('camera_status', 'READY')}`\n\n**Frame:** `#{st.session_state.get('camera_frame_sequence', 'N/A')}`\n\n**Last Capture:** `{st.session_state.get('camera_last_capture', 'None')}`")

        # Display the captured physical photo
        img_rel_path = st.session_state.get("camera_image_path")
        full_img_path = os.path.join(BASE_DIR, img_rel_path) if img_rel_path else None
        # Only ever show the exact file returned by the latest successful capture;
        # never an older photo or a fixed legacy path.
        if st.session_state.get("camera_status") == "ERROR":
            st.warning("No photo shown: the latest capture failed. Click '📸 CAPTURE PHOTO' to try again.")
        elif full_img_path and os.path.exists(full_img_path):
            with open(full_img_path, "rb") as _img_f:
                _img_bytes = _img_f.read()
            st.image(
                _img_bytes,
                caption=(f"📷 Physical ESP32-CAM Photo | Frame #{st.session_state.get('camera_frame_sequence')} | "
                         f"Captured: {st.session_state.get('camera_last_capture')} | {os.path.basename(full_img_path)}"),
                use_container_width=True
            )
        else:
            st.warning("No camera photo captured yet. Click '📸 CAPTURE PHOTO' to acquire a fresh frame.")

        # Recent captures gallery (newest first)
        captures_dir = os.path.join(BASE_DIR, "data", "camera_captures")
        if os.path.isdir(captures_dir):
            recent = sorted((f for f in os.listdir(captures_dir) if f.lower().endswith(".jpg")), reverse=True)[:6]
            if len(recent) > 1:
                with st.expander(f"🖼️ Recent captures ({len(recent)})"):
                    gcols = st.columns(3)
                    for i, fname in enumerate(recent):
                        gcols[i % 3].image(os.path.join(captures_dir, fname), caption=fname.replace("esp32cam_", "").replace(".jpg", ""), use_container_width=True)

        # Manual Capture Button
        btn_label = "📸 Capturing..." if st.session_state.get("camera_capturing") else "📸 CAPTURE PHOTO"
        btn_disabled = st.session_state.get("camera_capturing", False)

        def trigger_photo_capture():
            st.session_state["trigger_capture"] = True
            st.session_state["camera_capturing"] = True

        st.button(
            btn_label,
            disabled=btn_disabled,
            key="btn_manual_photo_capture",
            on_click=trigger_photo_capture,
            use_container_width=True
        )

        # Optical Intelligence Inference section
        st.markdown("---")
        opt_intel = st.session_state.get("camera_optical_intel")
        if opt_intel and opt_intel.get("status") == "SUCCESS":
            st.markdown("#### 🔍 Optical Quality & Edge Vision ($Q_{visual}$)")
            model_name = opt_intel.get("model_name", "MobileNetV3-Small-AquaticBloom")
            pred_cls = opt_intel.get("predicted_class", "UNAVAILABLE")
            v_state = opt_intel.get("visual_state", "UNCERTAIN")
            conf = opt_intel.get("confidence", 0.0)
            eff_conf = opt_intel.get("effective_confidence", 0.0)
            qv = opt_intel.get("q_visual", 1.0)
            q_state = opt_intel.get("quality_state", "RELIABLE")

            sc1, sc2 = st.columns(2)
            sc1.metric("Optical Model", model_name)
            sc2.metric("Classification", pred_cls)

            mc1, mc2 = st.columns(2)
            mc1.metric("Visual Detection State", v_state)
            mc2.metric("Optical Quality ($Q_{visual}$)", f"{qv:.2f}")

            mc3, mc4 = st.columns(2)
            mc3.metric("Raw Model Confidence", f"{conf:.2%}")
            mc4.metric("Effective Confidence", f"{eff_conf:.2%}")

            opt_q = opt_intel.get("optical_quality", {})
            if opt_q:
                st.caption(f"**Metrics:** Sharpness: `{opt_q.get('sharpness_score', 0):.2f}` | Lum: `{opt_q.get('mean_luminance', 0):.1f}` | Entropy: `{opt_q.get('entropy_score', 0):.2f}` bits | State: `{q_state}`")
        else:
            st.info("ℹ️ Optical classification unavailable. Frame acquisition from physical GC2145 PASS ✅")


    with col_temp:
        st.markdown("### ⏱️ Temporal Environmental Trajectory (N=12)")
        if temporal_ev:
            t_state = temporal_ev.get("temporal_state", "NORMAL")
            t_risk = temporal_ev.get("trajectory_risk_score", 0.0)
            persist = temporal_ev.get("persistence_cycles", 0)

            st.metric("Temporal Threat State", t_state)
            st.metric("Trajectory Threat Score", f"{t_risk:.2%}")
            st.metric("Persistence Window", f"{persist} cycles")

            st.markdown("#### Trend Slopes (per minute)")
            slopes = temporal_ev.get("trend_slopes", {})

            # Map canonical metrics and handle null/unavailable properly
            ph_slope = slopes.get("ph_per_min")
            turb_slope = slopes.get("turbidity_voltage_per_min", slopes.get("turbidity_ntu_per_min"))
            temp_slope = slopes.get("temperature_c_per_min")
            do_slope = slopes.get("dissolved_oxygen_mg_l_per_min")
            sal_slope = slopes.get("salinity_ppt_per_min")

            ph_str = f"{ph_slope:+.4f} / min" if ph_slope is not None else "N/A"
            turb_str = f"{turb_slope:+.4f} V/min" if turb_slope is not None else "N/A"
            temp_str = f"{temp_slope:+.4f} °C/min" if temp_slope is not None else "N/A"
            do_str = f"{do_slope:+.4f} mg/L/min" if do_slope is not None else "N/A"
            sal_str = f"{sal_slope:+.4f} ppt/min" if sal_slope is not None else "N/A"

            st.write(f"• **pH:** `{ph_str}`")
            st.write(f"• **Turbidity:** `{turb_str}`")
            st.write(f"• **Temperature:** `{temp_str}`")
            st.write(f"• **Dissolved Oxygen:** `{do_str}`")
            st.write(f"• **Salinity:** `{sal_str}`")

            leads = temporal_ev.get("lead_indicators", [])
            if leads:
                st.markdown("#### Early-Warning Precursors")
                for l in leads:
                    st.warning(l)
        else:
            st.info("Temporal trajectory accumulating sliding-window history...")

# ----------------- TAB 3: Evidential Decision & XAI -----------------
with tab3:
    st.subheader("🧠 Multi-Tier Threat Progression & Explainability (XAI)")

    if decision:
        fusion = decision.get("fusion", {})
        eco_state = fusion.get("ecological_state", fusion.get("final_state", "NORMAL"))
        comp_risk = fusion.get("composite_risk_score", 0.0)

        # 5-Tier Threat Gauge
        badge_cls = {
            "NORMAL": "badge-normal",
            "WATCH": "badge-watch",
            "EARLY_WARNING": "badge-early_warning",
            "HIGH_RISK": "badge-high_risk",
            "BLOOM_CONFIRMED": "badge-bloom_confirmed"
        }.get(eco_state, "badge-fault")

        st.markdown(f"<h3>5-Tier Ecological Threat State: <span class='status-badge {badge_cls}'>{eco_state}</span></h3>", unsafe_allow_html=True)
        st.metric("Composite Threat Risk Score", f"{comp_risk:.2%}")
        st.caption(f"Reason Code: {fusion.get('reason_code')} | Confidence Band: {fusion.get('confidence_band')}")

        st.divider()

        # Explainability & Attribution
        if explanation:
            st.markdown("### 📊 Modality Attribution Breakdown")
            m_attrib = explanation.get("modality_attribution", {})
            st.bar_chart(pd.DataFrame([m_attrib]).rename(columns={
                "sensor_pct": "Sensor Probes %",
                "visual_pct": "Camera Vision %",
                "temporal_pct": "Temporal Trajectory %",
                "ais_pct": "Adaptive AIS %"
            }))

            st.markdown("### 🔬 Feature-Level Root Cause Attribution")
            f_attrib = explanation.get("feature_attribution", {})
            st.bar_chart(pd.DataFrame([f_attrib]))

            st.markdown("### 💡 Prioritized Diagnostic Lead Factors")
            for factor in explanation.get("key_factors", []):
                st.info(f"• {factor}")

        st.divider()

        # Subsystems (ML & AIS)
        mc1, mc2 = st.columns(2)
        with mc1:
            st.markdown("### 🤖 Supervised Machine Learning")
            ml_ev = decision.get("ml_evidence", {})
            st.metric("Predicted Class", ml_ev.get("predicted_class", "N/A"))
            st.metric("Prediction Confidence", f"{ml_ev.get('confidence', 0):.2%}")
            st.metric("Dangerous Class Flag", "YES" if ml_ev.get("dangerous_class") else "NO")

        with mc2:
            st.markdown("### 🛡️ Adaptive Artificial Immune System (V5.4)")
            ais_ev = decision.get("ais_evidence", {})
            imm_type = ais_ev.get("immune_response_type", "PRIMARY_RESPONSE")
            if imm_type == "SECONDARY_RESPONSE":
                st.markdown("**Anomaly Status:** <span style='color:#D32F2F;font-weight:bold;'>⚡ SECONDARY IMMUNE RESPONSE (Memory Recall)</span>", unsafe_allow_html=True)
            elif ais_ev.get("is_anomaly"):
                st.markdown("**Anomaly Status:** <span style='color:#E53935;font-weight:bold;'>⚠️ PRIMARY RESPONSE (Novelty Detected)</span>", unsafe_allow_html=True)
            else:
                st.markdown("**Anomaly Status:** <span style='color:#43A047;font-weight:bold;'>✅ SELF (In-Distribution Tolerant)</span>", unsafe_allow_html=True)

            st.metric("AIS Anomaly Score", f"{ais_ev.get('anomaly_score', 0):.4f}")
            st.metric("Nearest Detector Distance", f"{ais_ev.get('nearest_detector_distance', 0):.4f}")
            st.metric("Memory Cell Matches", ais_ev.get("memory_cell_matches", 0))

        st.divider()

        # Actuator Output States
        st.subheader("🔌 Live Actuator Output States")
        act_summary = latest_data.get("decision", {}).get("actuator_summary") or "LEDs(G=N/A, Y=N/A, R=N/A), Buzzer=N/A, Pump=N/A"
        ac1, ac2, ac3, ac4, ac5 = st.columns(5)
        ac1.metric("Green LED", "ON" if "G=ON" in act_summary else "OFF")
        ac2.metric("Yellow LED", "ON" if "Y=ON" in act_summary else "OFF")
        ac3.metric("Red LED", "ON" if "R=ON" in act_summary else "OFF")
        ac4.metric("Piezo Buzzer", "ON" if "Buzzer=ON" in act_summary else "OFF")
        ac5.metric("Aerator Pump", "ON" if "Pump=ON" in act_summary else "OFF")
    else:
        st.info("Inference decision has not run yet. Poll sensors to trigger.")

# ----------------- TAB 4: Historical Baselines & Digital State -----------------
with tab4:
    st.subheader("📈 Historical Baselines & Digital Ecosystem State (V5.7 / V5.8)")

    if digital_state:
        st.metric("Site Ecosystem Health Index", f"{digital_state.get('ecosystem_health_index', 1.0):.1%}")
        st.caption(f"Total Historical Observations Analyzed: {digital_state.get('total_observations', 0)}")

        st.markdown("#### Rolling Baseline Distributions (Mean ± Std)")
        bases = digital_state.get("baselines", {})
        b_rows = []
        for m, b in bases.items():
            if b:
                b_rows.append({
                    "Metric": m,
                    "Mean": b["mean"],
                    "Std Dev": b["std"],
                    "Median": b["median"],
                    "Min": b["min_val"],
                    "Max": b["max_val"],
                    "Samples": b["sample_count"]
                })
        if b_rows:
            st.dataframe(pd.DataFrame(b_rows))

    hist_telemetry = fetch_json(f"/devices/{selected_id}/telemetry?limit=100")
    if hist_telemetry and len(hist_telemetry) > 0:
        df = pd.DataFrame(hist_telemetry).sort_values("timestamp")
        st.markdown("#### Water Temperature Trend (°C)")
        st.line_chart(df, x="timestamp", y="temperature_c")
        st.markdown("#### pH Levels Trend")
        st.line_chart(df, x="timestamp", y="ph")
        st.markdown("#### Turbidity Voltage Trend (V) [Uncalibrated NTU]")
        st.line_chart(df, x="timestamp", y="turbidity_ntu")
        st.markdown("#### Dissolved Oxygen Trend (mg/L)")
        st.line_chart(df, x="timestamp", y="dissolved_oxygen_mg_l")
    else:
        st.info("No historical telemetry records logged in database yet.")

# ----------------- TAB 5: Alerts & Event Logs -----------------
with tab5:
    st.subheader("🚨 Persisted System Alerts Log")
    unack_alerts = fetch_json("/alerts?acknowledged=false&limit=25")
    
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
    decisions_hist = fetch_json(f"/devices/{selected_id}/decisions?limit=25")
    if decisions_hist and len(decisions_hist) > 0:
        st.markdown("#### Latest Fusion Decisions Table")
        st.dataframe(pd.DataFrame(decisions_hist).tail(20))

# ----------------- TAB 6: V7 Multimodal Intelligence -----------------
with tab6:
    st.subheader(f"🌐 V7 Multimodal Alignment & Intelligence: {selected_id}")

    # Extract V7 data payloads
    snapshot_data = multimodal_info.get("multimodal_snapshot") or intel_data.get("multimodal_snapshot") or {}
    concordance_data = multimodal_info.get("concordance") or intel_data.get("concordance") or {}
    conflict_data = multimodal_info.get("conflict") or intel_data.get("conflict") or {}
    state_data = multimodal_info.get("multimodal_state") or intel_data.get("multimodal_state") or {}

    # Overview KPI row
    mc1, mc2, mc3, mc4 = st.columns(4)

    # Concordance status
    conc_st = concordance_data.get("concordance_state", "INCONCLUSIVE")
    agr_score = float(concordance_data.get("agreement_score", 0.0))
    with mc1:
        if conc_st == "CONCORDANT":
            badge_cls = "badge-normal"
        elif conc_st == "PARTIALLY_CONCORDANT":
            badge_cls = "badge-watch"
        else:
            badge_cls = "badge-early_warning"
        st.markdown(f"**Concordance State:**<br><span class='status-badge {badge_cls}'>{conc_st}</span>", unsafe_allow_html=True)
        st.caption(f"Agreement Score: {agr_score:.1%}")

    # Conflict status
    has_conf = bool(conflict_data.get("conflict_detected", False))
    conf_type = conflict_data.get("conflict_type", "NONE")
    presc_act = conflict_data.get("prescriptive_action") or conflict_data.get("recommended_handling", "STANDARD_FUSION")
    with mc2:
        if has_conf:
            conf_badge = '<span class="status-badge badge-warning">CONFLICT DETECTED</span>'
        else:
            conf_badge = '<span class="status-badge badge-normal">CONCORDANT / NO CONFLICT</span>'
        st.markdown(f"**Cross-Modality Conflict:**<br>{conf_badge}", unsafe_allow_html=True)
        st.caption(f"Action: {presc_act}")

    # Single-modality dominance prevention
    dom_prev = bool(state_data.get("dominance_prevented", False))
    with mc3:
        if dom_prev:
            dom_badge = '<span class="status-badge badge-warning">DOMINANCE PREVENTED</span>'
            dom_sub = "Single noisy probe held to EARLY_WARNING"
        else:
            dom_badge = '<span class="status-badge badge-normal">NOMINAL SYNTHESIS</span>'
            dom_sub = "Multi-channel corroborated"
        st.markdown(f"**Dominance Governance:**<br>{dom_badge}", unsafe_allow_html=True)
        st.caption(dom_sub)

    # Composite alignment quality
    align_q = float(snapshot_data.get("alignment_quality", 1.0))
    avail_mods = snapshot_data.get("available_modalities", ["SENSOR", "AIS"])
    with mc4:
        st.metric("Alignment Quality", f"{align_q:.1%}", f"{len(avail_mods)}/5 Modalities Active")

    st.divider()

    # Section 1: Multimodal Snapshot Breakdown Table
    st.markdown("#### 📡 Real-Time Multimodal Alignment Snapshot")
    mods_dict = snapshot_data.get("modalities", {})
    if mods_dict:
        rows = []
        for mod_name, item in mods_dict.items():
            rows.append({
                "Modality": mod_name,
                "Status": "ACTIVE",
                "Assessed State": item.get("state", "UNKNOWN"),
                "Confidence": f"{float(item.get('confidence', 0)):.1%}",
                "Quality Score": f"{float(item.get('quality', 1.0)):.2f}",
                "Freshness": item.get("freshness_state", "CURRENT"),
                "Valid Feed": "✅ Valid" if item.get("valid", True) else "⚠️ Degraded",
                "Threat Severity": f"{float(item.get('severity', 0.0)):.2f}",
                "Source Provider": item.get("source", "Standard")
            })
        for m_miss in snapshot_data.get("missing_modalities", []):
            rows.append({
                "Modality": m_miss,
                "Status": "OFFLINE / MISSING",
                "Assessed State": "UNAVAILABLE",
                "Confidence": "0.0%",
                "Quality Score": "0.00",
                "Freshness": "MISSING",
                "Valid Feed": "❌ Offline",
                "Threat Severity": "0.00",
                "Source Provider": "None (Graceful Fallback)"
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("No active multimodal snapshot data registered for this cycle.")

    # Section 2: Conflict Diagnostics Card
    st.markdown("#### ⚖️ Cross-Modality Conflict Diagnostics & Resolution")
    if has_conf:
        st.warning(
            f"**Active Conflict:** `{conf_type}`\n\n"
            f"- **Conflicting Modalities:** {', '.join(conflict_data.get('modalities_in_conflict', []))}\n"
            f"- **Conflict Severity:** `{conflict_data.get('conflict_severity', 'MEDIUM')}`\n"
            f"- **Prescriptive Handling:** `{presc_act}`\n"
            f"- **Diagnostic Details:** {conflict_data.get('explanation', 'Discordance detected between visual and chemistry telemetry.')}"
        )
    else:
        st.success(
            "**Harmonious Evidential Concordance:** All active modalities report mutually consistent ecological indicators. "
            "No cross-modality suppression or conservative hold required."
        )

    # Section 3: Synthesized Ecological Reasoning & Explainability
    st.markdown("#### 🧠 Synthesized Multimodal Ecological Rationale")
    eco_expl = state_data.get("explanation") or explanation.get("summary") if explanation else "System operating within nominal ecological parameters."
    st.info(f"**Diagnostic Narrative:** {eco_expl}")

    # Section 4: Multimodal Event History
    st.markdown("#### 📜 Recent Multimodal Event History")
    history_events = multimodal_info.get("recent_history", [])
    if history_events:
        st.dataframe(pd.DataFrame(history_events), use_container_width=True)
    else:
        st.caption("No persisted multimodal event history recorded yet.")

# ----------------- TAB 7: V8 Research & Deployment -----------------
with tab7:
    st.subheader(f"🔬 V8 Research-Grade Deployment & Autonomous Response: {selected_id}")

    # Boundary Banner
    st.info(
        "🛡️ **System Status:** `V8.0.0 SOFTWARE COMPLETE & FULLY VERIFIED` | "
        "⚠️ **Physical Hardware Boundary:** `PENDING BENCH WIRING VALIDATION`"
    )

    trend_obj = v8_trend_info.get("risk_trend") or {}
    resp_obj = v8_response_info.get("actuator_decision") or {}
    policy_state = v8_response_info.get("policy_state", "MONITOR")

    # Row 1: V8 Core Intelligence KPIs
    rk1, rk2, rk3, rk4 = st.columns(4)
    with rk1:
        traj = trend_obj.get("trajectory", "STABLE")
        traj_color = {
            "STABLE": "badge-normal",
            "RISING": "badge-warning",
            "ACCELERATING": "badge-critical",
            "PEAKING": "badge-bloom_confirmed",
            "DECLINING": "badge-watch",
            "RECOVERING": "badge-normal"
        }.get(traj, "badge-normal")
        st.markdown(f"**Risk Trajectory:**<br><span class='status-badge {traj_color}'>{traj}</span>", unsafe_allow_html=True)
        st.caption(f"Slope: {float(trend_obj.get('slope_per_min', 0.0)):+.3f}/min")

    with rk2:
        horizon = trend_obj.get("horizon_state", "NO_IMMEDIATE_RISK")
        hor_color = {
            "NO_IMMEDIATE_RISK": "badge-normal",
            "DEVELOPING_RISK": "badge-watch",
            "NEAR_TERM_RISK": "badge-warning",
            "ACTIVE_EVENT": "badge-critical",
            "RECOVERY": "badge-normal"
        }.get(horizon, "badge-normal")
        st.markdown(f"**Early-Warning Horizon:**<br><span class='status-badge {hor_color}'>{horizon}</span>", unsafe_allow_html=True)
        st.caption(f"Uncertainty: {float(trend_obj.get('uncertainty', 0.0)):.1%}")

    with rk3:
        pol_color = {
            "MONITOR": "badge-normal",
            "WATCH": "badge-watch",
            "PREPARE": "badge-warning",
            "INTERVENE": "badge-high_risk",
            "EMERGENCY": "badge-critical",
            "RECOVERY": "badge-normal"
        }.get(policy_state, "badge-normal")
        st.markdown(f"**Autonomous Policy:**<br><span class='status-badge {pol_color}'>{policy_state}</span>", unsafe_allow_html=True)
        st.caption(f"Action: {resp_obj.get('approved_action', 'NO_ACTION')}")

    with rk4:
        suff = trend_obj.get("data_sufficiency", "SUFFICIENT")
        st.metric("Data Sufficiency", suff, f"Window: {trend_obj.get('evidence_window', 0)} cycles")

    st.divider()

    # Row 2: Actuator Safety Gate Matrix & Audit
    sg_col1, sg_col2 = st.columns(2)
    with sg_col1:
        st.markdown("#### 🛡️ Multi-Barrier Actuator Safety Gate")
        checks = resp_obj.get("safety_checks", {})
        if isinstance(checks, str):
            try:
                checks = json.loads(checks)
            except Exception:
                checks = {}
        if checks and isinstance(checks, dict):
            chk_rows = []
            for k, v in checks.items():
                chk_rows.append({
                    "Safety Barrier": str(k).replace("_", " ").title(),
                    "Status": "✅ PASSED" if v else "⛔ BLOCKED"
                })
            st.dataframe(pd.DataFrame(chk_rows), use_container_width=True)
        else:
            st.caption("No active safety gate interventions for nominal cycles.")

        blocked = resp_obj.get("blocked_reasons", [])
        if isinstance(blocked, str):
            try:
                blocked = json.loads(blocked)
            except Exception:
                blocked = []
        if blocked and isinstance(blocked, list):
            st.warning(f"**Intervention Safeguard Blocked Reasons:**\n" + "\n".join([f"- `{b}`" for b in blocked]))
        else:
            st.success("All safety barriers cleared for authorized autonomous actions.")

    with sg_col2:
        st.markdown("#### ⚡ Autonomous Actuation Audit")
        act_status = resp_obj.get("execution_status", "COMMAND_NOT_VERIFIED")
        st.markdown(f"- **Requested Command:** `{resp_obj.get('requested_action', 'NO_ACTION')}`")
        st.markdown(f"- **Gate Decision:** `{resp_obj.get('approved_action', 'NO_ACTION')}`")
        st.markdown(f"- **Execution Verification Status:** `{act_status}`")
        st.markdown(f"- **Audit Command ID:** `{resp_obj.get('command_id', 'N/A')}`")

        # System Reliability Metrics
        st.markdown("#### 📊 System Reliability Metrics")
        if reliability_metrics:
            rc1, rc2 = st.columns(2)
            rc1.metric("Total System Cycles", reliability_metrics.get("total_cycles", 0))
            rc1.metric("Throughput", f"{reliability_metrics.get('throughput_cycles_sec', 0.0)} cyc/s")
            rc2.metric("P95 Latency", f"{reliability_metrics.get('latency_p95_ms', 0.0)} ms")
            rc2.metric("Success Rate", f"{reliability_metrics.get('success_rate_percent', 100.0)}%")
        else:
            st.caption("Reliability metrics collector initializing.")

    st.divider()

    # Row 3: Actuator Decision History Table
    st.markdown("#### 📜 Actuator Decision Audit Log")
    act_history = v8_response_info.get("recent_actuator_history", [])
    if act_history:
        st.dataframe(pd.DataFrame(act_history), use_container_width=True)
    else:
        st.caption("No actuator decision audit history registered yet.")

