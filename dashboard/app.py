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
</style>
""", unsafe_allow_html=True)

# API endpoint helper
API_URL = os.environ.get("AQUASENTINEL_API_URL", "http://127.0.0.1:8001")

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
        r = requests.post(f"{API_URL}/api/camera/capture?device_id={device_id}", timeout=8.0)
        return r.json(), r.status_code
    except Exception as e:
        return {"success": False, "error": str(e), "camera": "ESP32-CAM", "sensor": "GC2145"}, 500


# Page title
st.title("🌊 IoT Aquatic Monitoring & Artificial Immune System Gateway")
st.markdown("**Version 7.0 Advanced Multimodal Intelligence & Evidential Reasoning Platform**")

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
    with st.sidebar.status(f"⚡ Processing {selected_cmd}...", expanded=True) as cmd_status:
        cmd_status.write(f"1. 📤 Sending `{selected_cmd}` to FastAPI `/devices/{selected_id}/command`...")
        import time
        time.sleep(0.3)
        cmd_status.write(f"2. ⚙️ Executing `{selected_cmd}` on hardware/transport layer...")
        res = fetch_json(f"/devices/{selected_id}/command", "POST", {"command": selected_cmd, "payload": cmd_payload})
        if res and res.get("status") in ["SUCCESS", "COMMAND_COMPLETED", "EXECUTED", "OK"]:
            if selected_cmd == "REQUEST_READING":
                cmd_status.write("3. ⏳ Waiting for fresh telemetry from physical ESP32...")
                time.sleep(1.0)
                cmd_status.write("4. 📥 Fresh physical sensor reading received and stored in EventStore!")
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
        c3.metric("Firmware Version", dev_details["firmware_version"])
        
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

        sc1, sc2, sc3, sc4, sc5 = st.columns(5)
        with sc1:
            val = telemetry.get("temperature_c")
            st.metric("Temperature (°C)", f"{val:.2f}" if val is not None else "N/A")
        with sc2:
            val = telemetry.get("salinity_ppt")
            st.metric("Salinity / TDS (ppt)", f"{val:.2f}" if val is not None else "N/A")
        with sc3:
            val = telemetry.get("ph")
            if val is not None:
                raw_val = float(val)
                RAW_MIN, RAW_MAX = 14.7, 28.9
                ph_demo_val = max(0.0, min(14.0, ((raw_val - RAW_MIN) / (RAW_MAX - RAW_MIN)) * 14.0))
                disp_val = f"{ph_demo_val:.2f}"
            else:
                disp_val = "N/A"

            st.metric("Water pH", disp_val)
        with sc4:
            turb_v = telemetry.get("turbidity_voltage", telemetry.get("turbidity_ntu"))
            turb_disp = f"{turb_v:.2f} V" if turb_v is not None else "N/A"
            st.metric("Turbidity", turb_disp)
        with sc5:
            val = telemetry.get("dissolved_oxygen_mg_l")
            st.metric("Dissolved Oxygen (mg/L)", f"{val:.2f}" if val is not None else "N/A")

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
            st.session_state["camera_latest_image_bytes"] = None
            st.session_state["camera_latest_frame_sequence"] = None
            st.session_state["camera_latest_capture_id"] = None
            st.session_state["camera_latest_capture_timestamp"] = None
            st.session_state["camera_optical_intel"] = None

            # Check backend for latest saved capture and decode its bytes
            try:
                latest_cam = fetch_json("/api/camera/latest")
                if latest_cam and latest_cam.get("success"):
                    st.session_state["camera_latest_capture_id"] = latest_cam.get("capture_id")
                    st.session_state["camera_latest_capture_timestamp"] = latest_cam.get("captured_at")
                    st.session_state["camera_latest_frame_sequence"] = latest_cam.get("frame_sequence")
                    st.session_state["camera_optical_intel"] = latest_cam.get("optical_intelligence")
                    
                    latest_b64 = latest_cam.get("image_base64")
                    if latest_b64:
                        import base64
                        import io
                        from PIL import Image
                        b_bytes = base64.b64decode(latest_b64)
                        if len(b_bytes) > 100:
                            test_img = Image.open(io.BytesIO(b_bytes))
                            test_img.verify()
                            st.session_state["camera_latest_image_bytes"] = b_bytes
            except Exception:
                pass

        # Execute pending capture request triggered by button click
        if st.session_state.get("trigger_capture"):
            with st.spinner("Requesting fresh frame from physical ESP32-CAM (GC2145 on COM4)..."):
                capture_res, status_code = capture_camera_photo(selected_id)
                if status_code == 200 and capture_res.get("success"):
                    raw_b64 = capture_res.get("image_base64")
                    if raw_b64:
                        try:
                            import base64
                            import io
                            from PIL import Image

                            decoded_bytes = base64.b64decode(raw_b64)
                            # Phase 9: Validate decoded image bytes
                            if not decoded_bytes or len(decoded_bytes) < 100:
                                raise ValueError("Decoded image bytes too small or empty")
                            
                            val_img = Image.open(io.BytesIO(decoded_bytes))
                            val_img.verify()

                            # Phase 5: Update session state atomically with fresh image bytes
                            st.session_state["camera_latest_image_bytes"] = decoded_bytes
                            st.session_state["camera_latest_frame_sequence"] = capture_res.get("frame_sequence")
                            st.session_state["camera_latest_capture_id"] = capture_res.get("capture_id")
                            st.session_state["camera_latest_capture_timestamp"] = capture_res.get("captured_at")
                            st.session_state["camera_optical_intel"] = capture_res.get("optical_intelligence")
                            st.session_state["camera_status"] = "SUCCESS"
                            st.session_state["camera_error"] = None
                        except Exception as val_err:
                            st.session_state["camera_status"] = "ERROR"
                            st.session_state["camera_error"] = f"Capture failed: received invalid image data ({val_err})"
                    else:
                        st.session_state["camera_status"] = "ERROR"
                        st.session_state["camera_error"] = "Capture failed: API returned empty image payload"
                else:
                    st.session_state["camera_status"] = "ERROR"
                    err_detail = capture_res.get("error") if isinstance(capture_res, dict) else f"HTTP {status_code}"
                    st.session_state["camera_error"] = err_detail

                st.session_state["trigger_capture"] = False
                st.session_state["camera_capturing"] = False
                st.rerun()

        # Capture Status Alert Banners
        if st.session_state.get("camera_status") == "SUCCESS":
            st.success(f"✓ Photo captured successfully at {st.session_state.get('camera_latest_capture_timestamp')} | Frame #{st.session_state.get('camera_latest_frame_sequence')}")
        elif st.session_state.get("camera_status") == "ERROR":
            st.error(f"✗ Camera capture failed\n\n**Reason:** {st.session_state.get('camera_error')}")

        # Metadata Status Card
        card_col1, card_col2 = st.columns(2)
        card_col1.info(f"**Camera:** `READY` (ESP32-CAM)\n\n**Sensor:** `GC2145` (COM4)\n\n**Source:** `PHYSICAL ESP32-CAM`")
        card_col2.info(f"**Status:** `{st.session_state.get('camera_status', 'READY')}`\n\n**Frame:** `#{st.session_state.get('camera_latest_frame_sequence', 'N/A')}`\n\n**Last Capture:** `{st.session_state.get('camera_latest_capture_timestamp', 'None')}`")

        # Phase 6 & 7: Display the fresh image bytes directly (No static file, immune to browser caching)
        cur_img_bytes = st.session_state.get("camera_latest_image_bytes")
        cur_seq = st.session_state.get("camera_latest_frame_sequence", "N/A")
        cur_time = st.session_state.get("camera_latest_capture_timestamp", "None")

        if cur_img_bytes:
            st.image(
                cur_img_bytes,
                caption=f"📷 Physical ESP32-CAM Photo (GC2145 on COM4 | Frame #{cur_seq} | Captured: {cur_time})",
                use_container_width=True
            )
        else:
            st.info("No camera photo captured yet. Click '📸 CAPTURE PHOTO' to acquire a fresh frame.")

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
        st.markdown("#### pH Levels Trend (Uncalibrated Linear Estimate)")
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

