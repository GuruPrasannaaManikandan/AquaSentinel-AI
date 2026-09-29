import json
import time
import numpy as np
import paho.mqtt.client as mqtt

BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "aquatic/AQUA_FRESH_001/telemetry"

samples = []
max_samples = 30

def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected to {BROKER}:{PORT} (rc={rc})")
    client.subscribe(TOPIC)
    print(f"[MQTT] Subscribed to {TOPIC}, capturing {max_samples} live wet packets...")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        sensors = data.get("sensors", {})
        seq = data.get("sequence_number", 0)
        ts = data.get("timestamp", "")
        
        ph_val = sensors.get("ph")
        turb_val = sensors.get("turbidity_ntu")
        temp_val = sensors.get("temperature_c")
        sal_val = sensors.get("salinity_ppt")
        do_val = sensors.get("dissolved_oxygen_mg_l")
        
        health = data.get("device_health", {})
        status = health.get("sensor_status", "OK")

        sample = {
            "seq": seq,
            "ts": ts,
            "ph": ph_val,
            "turbidity_v": turb_val,
            "temperature_c": temp_val,
            "salinity_ppt": sal_val,
            "dissolved_oxygen_mg_l": do_val,
            "sensor_status": status,
            "battery": sensors.get("battery"),
            "rssi": sensors.get("rssi")
        }
        samples.append(sample)
        ph_str = f"{ph_val:6.2f}" if ph_val is not None else "None"
        turb_str = f"{turb_val:6.3f} V" if turb_val is not None else "None"
        print(f"[{len(samples):02d}/{max_samples}] Seq #{seq:03d} (TS: {ts}) | pH: {ph_str} | Turbidity: {turb_str} | Temp: {temp_val} | Status: {status}")
    except Exception as e:
        print(f"Error parsing packet: {e}")

client = mqtt.Client(client_id=f"wet_collector_{int(time.time())}")
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_start()

timeout = 180  # 30 samples * 5s = 150s + 30s margin
start_time = time.time()
while len(samples) < max_samples and (time.time() - start_time) < timeout:
    time.sleep(1)

client.loop_stop()
client.disconnect()

print("\n" + "=" * 70)
print("PHASE 3, 5, 8: NUMERICAL ANALYSIS OF WET SENSOR TELEMETRY (30 SAMPLES)")
print("=" * 70)

ph_vals = [s["ph"] for s in samples if s["ph"] is not None]
turb_vals = [s["turbidity_v"] for s in samples if s["turbidity_v"] is not None]

# Save raw samples to json
with open("docs/wet_sensor_evidence.json", "w") as f:
    json.dump(samples, f, indent=2)
print("Raw sample data saved to docs/wet_sensor_evidence.json\n")

if ph_vals:
    ph_mean = float(np.mean(ph_vals))
    ph_min = float(np.min(ph_vals))
    ph_max = float(np.max(ph_vals))
    ph_std = float(np.std(ph_vals))
    ph_range = float(ph_max - ph_min)
    print(f"pH SENSOR (WET IN WATER):")
    print(f"  Count:              {len(ph_vals)}")
    print(f"  Mean:               {ph_mean:.4f}")
    print(f"  Minimum:            {ph_min:.4f}")
    print(f"  Maximum:            {ph_max:.4f}")
    print(f"  Std Deviation:      {ph_std:.4f}")
    print(f"  Range:              {ph_range:.4f}")
    in_range = all(0.0 <= p <= 14.0 for p in ph_vals)
    print(f"  Strictly in [0,14]: {in_range}")
    if not in_range:
        print(f"  [INVESTIGATION] Observed values range from {ph_min:.2f} to {ph_max:.2f}.")

if turb_vals:
    turb_mean = float(np.mean(turb_vals))
    turb_min = float(np.min(turb_vals))
    turb_max = float(np.max(turb_vals))
    turb_std = float(np.std(turb_vals))
    turb_range = float(turb_max - turb_min)
    print(f"\nTURBIDITY SENSOR (WET IN WATER):")
    print(f"  Count:              {len(turb_vals)}")
    print(f"  Mean:               {turb_mean:.4f} V")
    print(f"  Minimum:            {turb_min:.4f} V")
    print(f"  Maximum:            {turb_max:.4f} V")
    print(f"  Std Deviation:      {turb_std:.4f} V")
    print(f"  Range:              {turb_range:.4f} V")
    print(f"  Status Semantics:   UNVERIFIED_UNCALIBRATED")

print("=" * 70)
