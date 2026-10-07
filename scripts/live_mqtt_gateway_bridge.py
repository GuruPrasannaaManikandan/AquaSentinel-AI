#!/usr/bin/env python3
"""
AquaSentinel-AI: Live Hardware Serial-to-MQTT Gateway Bridge Service
====================================================================
Interfaces directly with the physical Main ESP32 @ 115200 baud without
resetting the board (DTR=False, RTS=False). The COM port is auto-detected
(src/utils/serial_ports.py); override with --port COM7 or AQUA_MAIN_PORT=COM7.
Parses the firmware's "[TELEMETRY-JSON] {...}" line (pH, pH status, turbidity
voltage + NTU estimate), writes the latest reading to data/live_sensor.json for
the dashboard, and publishes live packets to MQTT (AQUA_MQTT_HOST, default
test.mosquitto.org:1883, topic aquatic/AQUA_FRESH_001/telemetry; --no-mqtt to skip),
subscribes to commands (aquatic/+/command) to handle operational overrides:
  - REQUEST_READING: immediate physical sensor acquisition
  - SET_SAMPLING_INTERVAL: reconfigures scheduler telemetry rate
  - ACTIVATE_BUZZER / DEACTIVATE_BUZZER: toggles GPIO14 sound alarm
  - ACTIVATE_RELAY / DEACTIVATE_RELAY: toggles GPIO19 relay contact (electrical switching only)
  - PIN_DIAGNOSTICS: reports configured physical GPIO mapping
  - RESTART_DEVICE: controlled safe restart sequence
and routes all events through Gateway.on_message_received into EventStore (SQLite).
"""

import sys
import os
import json
import time
import datetime
import threading
import paho.mqtt.client as mqtt

# Add workspace directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.iot.gateway import Gateway
from src.iot.event_store import EventStore
from src.utils import serial_ports

BROKER = os.environ.get("AQUA_MQTT_HOST", "test.mosquitto.org")
PORT = int(os.environ.get("AQUA_MQTT_PORT", "1883"))
LIVE_SENSOR_PATH = os.path.join(BASE_DIR, "data", "live_sensor.json")
TOPICS = [
    "aquatic/+/telemetry",
    "aquatic/+/status",
    "aquatic/+/diagnostics",
    "aquatic/+/command"
]

class LiveGatewayBridge:
    def __init__(self):
        self.gateway = Gateway(workspace_dir=BASE_DIR, use_mock=True)
        self.event_store = EventStore()
        self.gateway.event_store = self.event_store
        self.packet_count = 0
        self.seq_num = 0
        self.last_packet = None
        self.running = True
        self.mqtt_client = None
        self.mqtt_connected = False
        self.sampling_interval = 5.0  # seconds between periodic telemetry packets
        
        # Physical sensor state (from the main ESP32). None until the board reports.
        self.last_ph = None
        self.last_turb = None
        self.last_status = "NO_DATA"
        self.last_reading = None  # full parsed [TELEMETRY-JSON] dict
        self.serial_port = None
        self.ser = None
        self.lock = threading.Lock()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.mqtt_connected = True
            print(f"[LIVE-GATEWAY] Connected to MQTT broker: {BROKER}:{PORT}", flush=True)
            for t in TOPICS:
                client.subscribe(t)
                print(f"[LIVE-GATEWAY] Subscribed to topic: {t}", flush=True)
        else:
            print(f"[LIVE-GATEWAY] Failed to connect, rc={rc}", flush=True)

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload_str = msg.payload.decode('utf-8', errors='replace')
        try:
            payload = json.loads(payload_str)
        except Exception:
            return

        if topic.endswith("/command"):
            cmd = payload.get("command")
            dev_id = payload.get("device_id") or topic.split("/")[1]
            self.handle_command(cmd, dev_id, payload, origin="MQTT_COMMAND")
            return

        if topic.endswith("/telemetry"):
            # Avoid re-processing echo from bridge
            if payload.get("bridge_origin") == "COM3_SERIAL_BRIDGE":
                return
            self.process_payload(topic, payload)

    def handle_command(self, cmd, dev_id="AQUA_FRESH_001", payload=None, origin="MQTT"):
        payload = payload or {}
        ts_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print(f"\n[LIVE-GATEWAY] 🕹️ Executing Command: {cmd} for {dev_id} (origin={origin})", flush=True)

        if cmd == "REQUEST_READING":
            self.trigger_immediate_reading(dev_id, command_origin=origin)

        elif cmd == "SET_SAMPLING_INTERVAL":
            raw_interval = None
            if isinstance(payload.get("payload"), dict):
                raw_interval = payload["payload"].get("interval")
            if raw_interval is None:
                raw_interval = payload.get("interval")
            if raw_interval is not None:
                try:
                    val = float(raw_interval)
                    if 2.0 <= val <= 300.0:
                        self.sampling_interval = val
                        print(f"[LIVE-GATEWAY] ⏱️ Sampling interval updated to {self.sampling_interval} seconds", flush=True)
                        if self.ser and self.ser.is_open:
                            try:
                                self.ser.write(f"SET_INTERVAL {int(val)}\n".encode())
                            except Exception:
                                pass
                        self.event_store.log_command(ts_iso, dev_id, cmd, {"interval": val}, "COMPLETED")
                except ValueError:
                    pass

        elif cmd in ["ACTIVATE_BUZZER", "DEACTIVATE_BUZZER"]:
            state = "ON" if cmd == "ACTIVATE_BUZZER" else "OFF"
            print(f"[LIVE-GATEWAY] 🔊 Buzzer set to {state} (GPIO14)", flush=True)
            if self.ser and self.ser.is_open:
                try:
                    self.ser.write(f"{cmd}\n".encode())
                except Exception:
                    pass
            self.event_store.log_actuators(ts_iso, dev_id, f"LEDs(G=ON, Y=OFF, R=OFF), Buzzer={state}, Pump=OFF", f"Manual override: {cmd}")
            self.event_store.log_command(ts_iso, dev_id, cmd, payload, "COMPLETED")

        elif cmd in ["ACTIVATE_RELAY", "DEACTIVATE_RELAY"]:
            state = "ON" if cmd == "ACTIVATE_RELAY" else "OFF"
            print(f"[LIVE-GATEWAY] ⚡ Relay set to {state} (GPIO19, electrical switching only)", flush=True)
            if self.ser and self.ser.is_open:
                try:
                    self.ser.write(f"{cmd}\n".encode())
                except Exception:
                    pass
            self.event_store.log_actuators(ts_iso, dev_id, f"LEDs(G=ON, Y=OFF, R=OFF), Buzzer=OFF, Pump={state}", f"Manual override: {cmd}")
            self.event_store.log_command(ts_iso, dev_id, cmd, payload, "COMPLETED")

        elif cmd in ["PIN_DIAGNOSTICS", "RUN_DIAGNOSTICS"]:
            diag = {
                "green_led": "GPIO25",
                "yellow_led": "GPIO26",
                "red_led": "GPIO27",
                "buzzer": "GPIO14",
                "relay": "GPIO19",
                "ph": "GPIO32 (Physical, uncalibrated)",
                "turbidity": "GPIO34 (Physical voltage, uncalibrated)",
                "ds18b20": "GPIO33 (DS18B20 configured, PHYSICALLY DISCONNECTED)",
                "dissolved_oxygen": "NOT AVAILABLE",
                "salinity": "NOT AVAILABLE"
            }
            print(f"[LIVE-GATEWAY] 🩺 Hardware PIN Diagnostics: {json.dumps(diag)}", flush=True)
            if self.mqtt_client and self.mqtt_connected:
                try:
                    self.mqtt_client.publish(f"aquatic/{dev_id}/diagnostics", json.dumps(diag), qos=0)
                except Exception:
                    pass
            self.event_store.log_command(ts_iso, dev_id, cmd, diag, "COMPLETED")

        elif cmd == "RESTART_DEVICE":
            print(f"[LIVE-GATEWAY] 🔄 Device restart command received. Safe controlled restart sequence executed.", flush=True)
            if self.ser and self.ser.is_open:
                try:
                    self.ser.write(b"RESTART\n")
                except Exception:
                    pass
            self.event_store.log_command(ts_iso, dev_id, cmd, payload, "COMPLETED")

    def _build_telemetry_payload(self, seq, ts_iso, ph_val, turb_val, status_val, device_id="AQUA_FRESH_001", cmd_origin=None):
        payload = {
            "schema_version": "1.0",
            "device_id": device_id,
            "timestamp": ts_iso,
            "sequence_number": seq,
            "dataset_route": "caml",
            "bridge_origin": "COM3_SERIAL_BRIDGE",
            "location": {
                "latitude": None,
                "longitude": None
            },
            "sensors": {
                "ph": round(ph_val, 2) if ph_val is not None else None,
                "turbidity_ntu": round(turb_val, 3) if turb_val is not None else None,
                "turbidity_voltage": round(turb_val, 3) if turb_val is not None else None,
                "temperature_c": None,
                "salinity_ppt": None,
                "dissolved_oxygen_mg_l": None,
                "battery": 98.5,
                "rssi": -60,
                "distance_to_water_m": 120.0,
                "sample_depth": 0.0
            },
            "device_health": {
                "wifi_connected": False,
                "mqtt_connected": bool(self.mqtt_connected),
                "sensor_status": status_val
            }
        }
        reading = self.last_reading or {}
        payload["sensor_detail"] = {
            "ph_status": reading.get("ph_status"),
            "ph_voltage": reading.get("ph_voltage"),
            "turbidity_status": reading.get("turbidity_status"),
            "turbidity_ntu_est": reading.get("turbidity_ntu_est"),
        }
        if cmd_origin:
            payload["command_triggered"] = cmd_origin
        return payload

    def trigger_immediate_reading(self, device_id="AQUA_FRESH_001", command_origin="REQUEST_READING"):
        """Asks the physical ESP32 for a reading now; its reply arrives as a normal [TELEMETRY-JSON] line."""
        print(f"\n[LIVE-GATEWAY] ⚡ IMMEDIATE SENSOR ACQUISITION requested for {device_id} ({command_origin})", flush=True)
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(b"REQUEST_READING\n")
                print(f"[LIVE-GATEWAY] Dispatched REQUEST_READING to physical ESP32 on {self.serial_port}", flush=True)
            except Exception as e:
                print(f"[LIVE-GATEWAY] Serial dispatch error: {e}", flush=True)
        else:
            print("[LIVE-GATEWAY] Sensor ESP32 not connected; no reading taken.", flush=True)

    def process_payload(self, topic, payload):
        self.packet_count += 1
        self.last_packet = payload
        dev_id = payload.get("device_id", "UNKNOWN")

        # Route through Central Gateway pipeline
        try:
            self.gateway.on_message_received(topic, payload)
            latest_dec = self.event_store.get_latest_decision(dev_id)
            final_st = latest_dec.get("final_state") if latest_dec else "UNKNOWN"
            reason = latest_dec.get("reason_code") if latest_dec else "UNKNOWN"
            print(f"[LIVE-GATEWAY] 🧠 Processed Decision: State={final_st} | Reason={reason}", flush=True)
        except Exception as e:
            print(f"[LIVE-GATEWAY] Error processing in gateway: {e}", flush=True)

    def write_live_sensor_file(self, reading):
        """Atomically writes the latest physical reading for the backend /api/sensors/live."""
        try:
            os.makedirs(os.path.dirname(LIVE_SENSOR_PATH), exist_ok=True)
            tmp = LIVE_SENSOR_PATH + ".tmp"
            with open(tmp, "w") as f:
                json.dump(reading, f)
            os.replace(tmp, LIVE_SENSOR_PATH)
        except Exception as e:
            print(f"[SERIAL-BRIDGE] Could not write {LIVE_SENSOR_PATH}: {e}", flush=True)

    def handle_reading(self, reading):
        """Stores one parsed [TELEMETRY-JSON] reading, publishes it and routes it to the gateway."""
        ts_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        reading["received_at"] = ts_iso
        reading["port"] = self.serial_port
        with self.lock:
            self.last_reading = reading
            self.last_ph = reading.get("ph")
            self.last_turb = reading.get("turbidity_voltage")
            self.last_status = reading.get("status", "OK")
            self.seq_num += 1
            cur_seq = self.seq_num
        reading["sequence_number"] = cur_seq
        self.write_live_sensor_file(reading)

        print(f"[SERIAL-BRIDGE] pH={reading.get('ph')} ({reading.get('ph_status')}) | "
              f"turbidity={reading.get('turbidity_voltage')} V, ~{reading.get('turbidity_ntu_est')} NTU "
              f"({reading.get('turbidity_status')})", flush=True)

        trigger = reading.get("trigger")
        payload = self._build_telemetry_payload(cur_seq, ts_iso, self.last_ph, self.last_turb, self.last_status,
                                                cmd_origin=trigger if trigger and trigger != "PERIODIC" else None)
        if self.mqtt_client and self.mqtt_connected:
            try:
                self.mqtt_client.publish("aquatic/AQUA_FRESH_001/telemetry", json.dumps(payload), qos=0)
            except Exception as e:
                print(f"[SERIAL-BRIDGE] MQTT publish error: {e}", flush=True)
        self.process_payload("aquatic/AQUA_FRESH_001/telemetry", payload)

    def start_serial_bridge(self, port=None, baud=115200):
        """Reads the main ESP32 without toggling DTR/RTS (preserves board state)."""
        json_marker = "[TELEMETRY-JSON]"

        def reader():
            ser = None
            while self.running:
                try:
                    if ser is None or not ser.is_open:
                        use_port = port or serial_ports.find_port(serial_ports.MAIN, use_cache=False)
                        if not use_port:
                            print("[SERIAL-BRIDGE] Sensor ESP32 not found. Is it plugged in? "
                                  "Close any serial monitor, or pass --port COMx. Retrying in 3 s...", flush=True)
                            time.sleep(3.0)
                            continue
                        print(f"[SERIAL-BRIDGE] Opening {use_port} at {baud} baud (DTR=False, RTS=False)...", flush=True)
                        ser = serial_ports.open_port(use_port, baud, timeout=1.0)
                        self.ser = ser
                        self.serial_port = use_port
                        print(f"[SERIAL-BRIDGE] Connected to sensor ESP32 on {use_port}", flush=True)

                    line_bytes = ser.readline()
                    if not line_bytes:
                        continue
                    line = line_bytes.decode("utf-8", errors="replace").strip()
                    idx = line.find(json_marker)
                    if idx < 0:
                        if line.startswith("[PH-CAL]") or line.startswith("[TURB-CAL]") or line.startswith("[CMD]"):
                            print(f"[ESP32] {line}", flush=True)
                        continue
                    try:
                        reading = json.loads(line[idx + len(json_marker):].strip())
                    except ValueError:
                        continue  # partial line
                    self.handle_reading(reading)

                except Exception as e:
                    print(f"[SERIAL-BRIDGE] Serial error: {e}. Reconnecting in 3 s...", flush=True)
                    if ser:
                        try:
                            ser.close()
                        except Exception:
                            pass
                    ser = None
                    self.ser = None
                    time.sleep(3.0)

            if ser and ser.is_open:
                ser.close()
            self.ser = None
            print("[SERIAL-BRIDGE] Serial bridge thread terminated.", flush=True)

        t = threading.Thread(target=reader, daemon=True)
        t.start()

    def start_command_watcher(self):
        """Watches trigger file for instant IPC command dispatch."""
        def watcher():
            trigger_file = os.path.join(BASE_DIR, "models", "fusion", ".command_trigger.json")
            last_cmd_ts = ""
            if os.path.exists(trigger_file):
                try:
                    with open(trigger_file, "r") as f:
                        data = json.load(f)
                    last_cmd_ts = data.get("timestamp", "")
                except Exception:
                    pass
            while self.running:
                try:
                    if os.path.exists(trigger_file):
                        with open(trigger_file, "r") as f:
                            data = json.load(f)
                        cmd_ts = data.get("timestamp", "")
                        if cmd_ts and cmd_ts != last_cmd_ts:
                            last_cmd_ts = cmd_ts
                            cmd = data.get("command")
                            dev_id = data.get("device_id", "AQUA_FRESH_001")
                            print(f"\n[LIVE-GATEWAY] ⚡ IPC Command Trigger Detected: {cmd} for {dev_id} (TS: {cmd_ts})", flush=True)
                            self.handle_command(cmd, dev_id, data, origin="IPC_TRIGGER")
                except Exception:
                    pass
                time.sleep(0.05)

        t = threading.Thread(target=watcher, daemon=True)
        t.start()

    def run(self, serial_port=None, use_mqtt=True):
        if not use_mqtt:
            print("[LIVE-GATEWAY] MQTT disabled (--no-mqtt); serial -> database/dashboard only.", flush=True)
            self.start_serial_bridge(serial_port, 115200)
            self.start_command_watcher()
            try:
                while self.running:
                    time.sleep(1.0)
            except KeyboardInterrupt:
                pass
            finally:
                self.running = False
            return
        try:
            client = mqtt.Client(client_id=f"AquaGateway_Bridge_{int(time.time())}", callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
        except AttributeError:
            client = mqtt.Client(client_id=f"AquaGateway_Bridge_{int(time.time())}")
        
        self.mqtt_client = client
        client.on_connect = self.on_connect
        client.on_message = self.on_message

        print(f"[LIVE-GATEWAY] Connecting to broker {BROKER}:{PORT}...", flush=True)
        try:
            client.connect(BROKER, PORT, 60)
            client.loop_start()
        except Exception as e:
            print(f"[LIVE-GATEWAY] Broker connection error: {e}", flush=True)

        # Start live physical serial bridge
        self.start_serial_bridge(serial_port, 115200)

        # Start IPC command watcher
        self.start_command_watcher()

        print("[LIVE-GATEWAY] Bridge active. Subscribed to commands & forwarding live physical telemetry...", flush=True)
        try:
            while self.running:
                time.sleep(1.0)
        except KeyboardInterrupt:
            print("\n[LIVE-GATEWAY] Stopping bridge...", flush=True)
        finally:
            self.running = False
            client.loop_stop()
            client.disconnect()
            print("[LIVE-GATEWAY] Bridge stopped.", flush=True)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sensor ESP32 serial -> dashboard/MQTT bridge")
    parser.add_argument("--port", help="Serial port of the sensor ESP32, e.g. COM7 (default: auto-detect)")
    parser.add_argument("--no-mqtt", action="store_true", help="Do not connect to an MQTT broker")
    args = parser.parse_args()
    bridge = LiveGatewayBridge()
    bridge.run(serial_port=args.port, use_mqtt=not args.no_mqtt)
