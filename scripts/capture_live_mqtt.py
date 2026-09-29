import paho.mqtt.client as mqtt
import json
import time
import sys

BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "aquatic/AQUA_FRESH_001/telemetry"

received_packet = None

def on_connect(client, userdata, flags, rc):
    print(f"[LIVE-TEST] Connected to broker {BROKER}:{PORT} with rc={rc}")
    client.subscribe(TOPIC)
    print(f"[LIVE-TEST] Subscribed to {TOPIC}")

def on_message(client, userdata, msg):
    global received_packet
    print(f"\n[LIVE-TEST] >>> LIVE MQTT PACKET RECEIVED ON TOPIC: {msg.topic}")
    payload_str = msg.payload.decode('utf-8', errors='replace')
    print(f"[LIVE-TEST] Raw Payload:\n{payload_str}\n")
    try:
        data = json.loads(payload_str)
        print(f"[LIVE-TEST] Parsed JSON Structure:")
        print(json.dumps(data, indent=2))
        received_packet = data
    except Exception as e:
        print(f"[LIVE-TEST] JSON parse error: {e}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "live_listener_gateway_01")
client.on_connect = on_connect
client.on_message = on_message

print(f"[LIVE-TEST] Connecting to {BROKER}:{PORT}...")
client.connect(BROKER, PORT, 10)
client.loop_start()

start_time = time.time()
while time.time() - start_time < 15 and received_packet is None:
    time.sleep(0.5)

client.loop_stop()
client.disconnect()

if received_packet:
    print("\n[LIVE-TEST] SUCCESS: Real live MQTT packet captured from physical ESP32!")
    sys.exit(0)
else:
    print("\n[LIVE-TEST] Timeout waiting for MQTT packet.")
    sys.exit(1)
