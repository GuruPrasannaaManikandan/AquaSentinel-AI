import os
import sys
import time
import argparse
import datetime

# Ensure project root is on Python's path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

from src.iot.esp32_device import ESP32Device

def main():
    parser = argparse.ArgumentParser(description="Independently Executable Virtual ESP32 Device")
    parser.add_argument("--device-id", type=str, default="AQUA_FRESH_001", help="Device ID (AQUA_FRESH_001 or AQUA_MARINE_001)")
    parser.add_argument("--ecosystem", type=str, default="Freshwater", help="Ecosystem type (Freshwater or Marine)")
    parser.add_argument("--route", type=str, default="caml", help="Dataset route (caml or habsos)")
    parser.add_argument("--host", type=str, default="localhost", help="MQTT Broker Host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT Broker Port")
    parser.add_argument("--scenario", type=str, default="NORMAL", help="Simulation scenario (NORMAL, SENSOR_FAULT, etc.)")
    parser.add_argument("--use-mock", action="store_true", help="Connect to the Mock In-Memory broker instead of real MQTT")
    parser.add_argument("--interval", type=int, default=0, help="Override sampling interval (0 uses config interval)")
    
    args = parser.parse_args()

    print("==================================================")
    print(f"Starting Virtual Embedded Device: {args.device_id}")
    print(f"Ecosystem: {args.ecosystem} | Route: {args.route}")
    print(f"MQTT Broker: {args.host}:{args.port} (Mock Mode: {args.use_mock})")
    print(f"Scenario: {args.scenario}")
    print("==================================================")

    # Instantiate virtual device
    device = ESP32Device(
        device_id=args.device_id,
        ecosystem_type=args.ecosystem,
        dataset_route=args.route,
        use_mock=args.use_mock
    )

    # Perform Boot sequence
    print("[FIRMWARE] Booting virtual microcontroller...")
    device.boot()
    time.sleep(0.5)

    print("[FIRMWARE] Initializing sensor drivers via HAL...")
    device.initialize_sensors()
    time.sleep(0.5)

    print(f"[FIRMWARE] Connecting to network (SSID: {device.config.get_wifi().get('ssid')})...")
    device.connect_network(host=args.host, port=args.port)
    
    if not device.wifi_connected or not device.mqtt_connected:
        print("[ERROR] Network connection failed. Running offline fallback.")

    interval = args.interval if args.interval > 0 else device.sampling_interval
    print(f"[FIRMWARE] Running scheduler task loops. Sampling interval: {interval}s.")
    print("Press Ctrl+C to terminate.")
    
    try:
        while True:
            timestamp = datetime.datetime.now()
            print(f"\n[TICK {device.scheduler.current_tick}] Triggering scheduler tick cycle...")
            
            # Execute one scheduled cycle
            telemetry = device.execute_one_complete_cycle(scenario=args.scenario, timestamp=timestamp)
            
            if telemetry:
                print(f"  Published Telemetry payload: {telemetry['sensors']}")
                print(f"  Device Health: {telemetry['device_health']}")
                print(f"  FSM State: {device.state}")
            else:
                print(f"  Cycle completed. No telemetry output. FSM State: {device.state}")
                
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nShutting down virtual device...")
    finally:
        device.comm.disconnect_mqtt()
        print("Device disconnected.")

if __name__ == "__main__":
    main()
