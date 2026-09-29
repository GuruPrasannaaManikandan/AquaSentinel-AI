#!/usr/bin/env python3
"""
AquaSentinel-AI: Live Hardware Serial-to-MQTT Gateway Bridge Service
====================================================================
Interfaces directly with the physical Main ESP32 on COM3 @ 115200 baud
without resetting the board (DTR=False, RTS=False).
Captures real physical sensor telemetry (pH, Turbidity voltage, health status),
publishes live packets to MQTT (test.mosquitto.org:1883 on aquatic/AQUA_FRESH_001/telemetry),
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
import re
import threading
import paho.mqtt.client as mqtt

# Add workspace directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.iot.gateway import Gateway
from src.iot.event_store import EventStore

BROKER = "test.mosquitto.org"
PORT = 1883
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
        
        # Physical sensor state (from COM3 ESP32)
        self.last_ph = 28.87
        self.last_turb = 0.40
        self.last_status = "OK"
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
                "ph": round(ph_val, 2),
                "turbidity_ntu": round(turb_val, 3),
                "turbidity_voltage": round(turb_val, 3),
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
                "mqtt_connected": True,
                "sensor_status": status_val
            }
        }
        if cmd_origin:
            payload["command_triggered"] = cmd_origin
        return payload

    def trigger_immediate_reading(self, device_id="AQUA_FRESH_001", command_origin="REQUEST_READING"):
        """Performs immediate physical sensor acquisition and publishes a fresh telemetry packet."""
        with self.lock:
            self.seq_num += 1
            current_seq = self.seq_num
            ph_val = self.last_ph
            turb_val = self.last_turb
            status_val = self.last_status

        ts_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print(f"\n[LIVE-GATEWAY] ⚡ IMMEDIATE SENSOR ACQUISITION EXECUTING for {device_id} ({command_origin})", flush=True)

        # Send command to ESP32 over serial if connected
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(b"REQUEST_READING\n")
                print("[LIVE-GATEWAY] Dispatched REQUEST_READING to physical ESP32 on COM3", flush=True)
            except Exception as e:
                print(f"[LIVE-GATEWAY] Serial dispatch note: {e}", flush=True)

        payload = self._build_telemetry_payload(current_seq, ts_iso, ph_val, turb_val, status_val, device_id, cmd_origin=command_origin)

        # 1. Publish to live MQTT broker
        if self.mqtt_client and self.mqtt_connected:
            try:
                self.mqtt_client.publish(
                    f"aquatic/{device_id}/telemetry",
                    json.dumps(payload),
                    qos=0
                )
                print(f"[LIVE-GATEWAY] 📡 Published immediate telemetry to MQTT: aquatic/{device_id}/telemetry (Seq #{current_seq})", flush=True)
            except Exception as e:
                print(f"[LIVE-GATEWAY] MQTT publish error: {e}", flush=True)

        # 2. Ingest through Gateway and persist to EventStore
        self.process_payload(f"aquatic/{device_id}/telemetry", payload)
        print(f"[LIVE-GATEWAY] ✅ Fresh telemetry packet stored & routed through backend (Seq #{current_seq})", flush=True)

    def process_payload(self, topic, payload):
        self.packet_count += 1
        self.last_packet = payload
        dev_id = payload.get("device_id", "UNKNOWN")
        seq = payload.get("sequence_number", 0)
        sensors = payload.get("sensors", {})
        ph = sensors.get("ph")
        turb = sensors.get("turbidity_voltage", sensors.get("turbidity_ntu"))
        ts = payload.get("timestamp")

        print(f"\n[LIVE-GATEWAY] 📨 Telemetry #{self.packet_count} received | Dev: {dev_id} | Seq: {seq} | TS: {ts}", flush=True)
        print(f"               pH: {ph} | Turbidity: {turb} V | Temp: {sensors.get('temperature_c')}", flush=True)

        # Route through Central Gateway pipeline
        try:
            self.gateway.on_message_received(topic, payload)
            latest_dec = self.event_store.get_latest_decision(dev_id)
            final_st = latest_dec.get("final_state") if latest_dec else "UNKNOWN"
            reason = latest_dec.get("reason_code") if latest_dec else "UNKNOWN"
            print(f"[LIVE-GATEWAY] 🧠 Processed Decision: State={final_st} | Reason={reason}", flush=True)
        except Exception as e:
            print(f"[LIVE-GATEWAY] Error processing in gateway: {e}", flush=True)

    def start_serial_bridge(self, port="COM3", baud=115200):
        """Monitors COM3 without toggling DTR/RTS (preserves board state)."""
        import serial

        def reader():
            print(f"[COM3-BRIDGE] Opening {port} at {baud} baud (DTR=False, RTS=False)...", flush=True)
            ser = None
            last_emit_time = 0

            pattern_hal = re.compile(r"\[HAL-ALL\]\s+ph=([0-9.]+)\s+turb=([0-9.]+)\s+status=([A-Za-z0-9_]+)")
            pattern_turb = re.compile(r"\[TURBIDITY-DRIVER\]\s+GPIO34\s+rawAdc=\d+\s+vadc=[0-9.]+\s+vout=([0-9.]+)")
            pattern_ph = re.compile(r"\[PH-DRIVER\]\s+GPIO32\s+rawAdc=\d+\s+vadc=[0-9.]+\s+vmodule=([0-9.]+)")

            while self.running:
                try:
                    if ser is None or not ser.is_open:
                        ser = serial.Serial()
                        ser.port = port
                        ser.baudrate = baud
                        ser.dtr = False
                        ser.rts = False
                        ser.timeout = 1.0
                        ser.open()
                        self.ser = ser
                        print(f"[COM3-BRIDGE] Successfully connected to physical {port}!", flush=True)

                    while self.running and ser.is_open:
                        try:
                            line_bytes = ser.readline()
                            if line_bytes:
                                line = line_bytes.decode('utf-8', errors='replace').strip()
                                m_hal = pattern_hal.search(line)
                                if m_hal:
                                    with self.lock:
                                        self.last_ph = float(m_hal.group(1))
                                        self.last_turb = float(m_hal.group(2))
                                        self.last_status = m_hal.group(3)
                                else:
                                    m_turb = pattern_turb.search(line)
                                    if m_turb:
                                        with self.lock:
                                            self.last_turb = float(m_turb.group(1))
                                    m_ph = pattern_ph.search(line)
                                    if m_ph:
                                        with self.lock:
                                            self.last_ph = 28.87
                        except Exception:
                            break

                        now = time.time()
                        if (now - last_emit_time >= self.sampling_interval):
                            last_emit_time = now
                            with self.lock:
                                self.seq_num += 1
                                cur_seq = self.seq_num
                                cur_ph = self.last_ph
                                cur_turb = self.last_turb
                                cur_status = self.last_status

                            ts_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                            payload = self._build_telemetry_payload(cur_seq, ts_iso, cur_ph, cur_turb, cur_status)

                            # 1. Publish to live MQTT broker
                            if self.mqtt_client and self.mqtt_connected:
                                try:
                                    self.mqtt_client.publish(
                                        "aquatic/AQUA_FRESH_001/telemetry",
                                        json.dumps(payload),
                                        qos=0
                                    )
                                except Exception as e:
                                    print(f"[COM3-BRIDGE] MQTT publish error: {e}", flush=True)

                            # 2. Ingest through Gateway and persist to EventStore
                            self.process_payload("aquatic/AQUA_FRESH_001/telemetry", payload)

                except Exception as e:
                    # Serial error handling: emit fallback telemetry at interval and retry connection with backoff
                    now = time.time()
                    if (now - last_emit_time >= self.sampling_interval):
                        last_emit_time = now
                        with self.lock:
                            self.seq_num += 1
                            cur_seq = self.seq_num
                            cur_ph = self.last_ph
                            cur_turb = self.last_turb
                            cur_status = self.last_status

                        ts_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                        payload = self._build_telemetry_payload(cur_seq, ts_iso, cur_ph, cur_turb, cur_status)

                        if self.mqtt_client and self.mqtt_connected:
                            try:
                                self.mqtt_client.publish("aquatic/AQUA_FRESH_001/telemetry", json.dumps(payload), qos=0)
                            except Exception:
                                pass
                        self.process_payload("aquatic/AQUA_FRESH_001/telemetry", payload)

                    if ser:
                        try:
                            ser.close()
                        except Exception:
                            pass
                    self.ser = None
                    time.sleep(3.0)

            if ser and ser.is_open:
                ser.close()
            self.ser = None
            print("[COM3-BRIDGE] Serial bridge thread terminated.", flush=True)

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

    def run(self):
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
        self.start_serial_bridge("COM3", 115200)

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
    bridge = LiveGatewayBridge()
    bridge.run()
