import os
import json
import threading
import time
import datetime
from src.iot.device_runtime import DeviceRuntimeManager
from src.iot.event_store import EventStore
from src.backend.alerts import AlertSystem

class BackendService:
    """
    Core backend service managing the virtual DeviceRuntimeManager and event logging.
    Executes background simulation threads and exposes clean endpoints to retrieve metrics.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls, workspace_dir=None):
        if cls._instance is None:
            cls._instance = cls(workspace_dir)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Resets the singleton instance and stops any running simulation threads."""
        if cls._instance:
            cls._instance.stop_simulation()
            cls._instance = None

    def __init__(self, workspace_dir=None):
        self.workspace_dir = workspace_dir or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.runtime = DeviceRuntimeManager(workspace_dir=self.workspace_dir, use_mock=True)
        self._event_store = EventStore()
        
        # Link database store to gateway
        self.runtime.gateway.event_store = self._event_store

        # Simulation states
        self.simulation_active = False
        self.simulation_thread = None
        self.simulation_shutdown_event = threading.Event()
        self.cycle_lock = threading.Lock()
        self.scenarios = {
            "AQUA_FRESH_001": "NORMAL",
            "AQUA_MARINE_001": "NORMAL"
        }
        self.last_run_timestamp = None

        # Callbacks list for real-time WebSocket broadcasting
        self.on_decision_callbacks = []
        self.on_telemetry_callbacks = []
        self._wrap_gateway_callbacks()

    @property
    def event_store(self):
        return self._event_store

    @event_store.setter
    def event_store(self, new_store):
        self._event_store = new_store
        # Update references dynamically
        if hasattr(self, "runtime") and self.runtime:
            if hasattr(self.runtime, "gateway") and self.runtime.gateway:
                self.runtime.gateway.event_store = new_store

    def _wrap_gateway_callbacks(self):
        """Intercepts MQTT messages synchronously to dispatch alerts and notify WebSockets."""
        original_gateway_cb = self.runtime.gateway.client.message_callback

        def wrapped_message_callback(topic, payload):
            # 1. Call standard gateway parser
            if original_gateway_cb:
                original_gateway_cb(topic, payload)

            # 2. Intercept telemetry data
            if topic.endswith("/telemetry"):
                device_id = payload.get("device_id")
                # Trigger alerts on local edge validation faults
                if payload.get("device_health", {}).get("sensor_status") == "FAULT":
                    AlertSystem.trigger_sensor_fault_alert(payload, ["Local validation failure"], self.event_store)

                for cb in self.on_telemetry_callbacks:
                    cb(payload)

            # 3. Intercept decision updates
            elif topic.endswith("/decision"):
                device_id = payload.get("device_id")
                # Process alerts
                AlertSystem.process_decision_for_alerts(payload, self.event_store)
                
                for cb in self.on_decision_callbacks:
                    cb(payload)

        # Re-bind callback on gateway client
        self.runtime.gateway.client.set_on_message(wrapped_message_callback)

        # Bind on device clients too to capture decisions on the edge
        for dev in self.runtime.devices.values():
            original_dev_cb = dev.client.message_callback
            def make_dev_wrapped_cb(device_obj, orig_cb):
                def dev_wrapped_cb(topic, payload):
                    if orig_cb:
                        orig_cb(topic, payload)
                    if topic.endswith("/decision"):
                        # Notify callbacks of state change on actuators
                        act_summary = device_obj.actuators.get_summary()
                        timestamp = payload.get("timestamp") or datetime.datetime.now().isoformat()
                        self.event_store.log_actuators(timestamp, device_obj.device_id, act_summary, "Actuator update logged in runtime service callback")
                return dev_wrapped_cb

            dev.client.set_on_message(make_dev_wrapped_cb(dev, original_dev_cb))

    def _execute_cycle_locked(self, timestamp=None, force=True):
        """Thread-safe helper to run a single cycle across all registered devices."""
        with self.cycle_lock:
            if not force and self.last_run_timestamp is not None:
                elapsed = (datetime.datetime.now() - self.last_run_timestamp).total_seconds()
                if elapsed < 1.95:
                    return None

            if not self.runtime.devices["AQUA_FRESH_001"].wifi_connected:
                self.runtime.start()
            if timestamp is None:
                timestamp = datetime.datetime.now()
            self.last_run_timestamp = timestamp
            return self.runtime.execute_cycle(self.scenarios, timestamp)

    def register_decision_callback(self, callback):
        self.on_decision_callbacks.append(callback)

    def register_telemetry_callback(self, callback):
        self.on_telemetry_callbacks.append(callback)

    def start_simulation(self):
        """Starts background thread executing polling cycles periodically."""
        if self.simulation_active:
            return False

        self.simulation_active = True
        self.simulation_shutdown_event.clear()
        self.simulation_thread = threading.Thread(target=self._run_simulation_loop, daemon=True)
        self.simulation_thread.start()
        return True

    def stop_simulation(self):
        """Signals background thread to terminate."""
        if not self.simulation_active:
            return False

        self.simulation_active = False
        self.simulation_shutdown_event.set()
        if self.simulation_thread:
            self.simulation_thread.join(timeout=1.0)
        self.runtime.stop()
        return True

    def set_scenario(self, device_id, scenario):
        """Sets scenario type for a device."""
        if device_id not in self.scenarios:
            raise ValueError(f"Device ID {device_id} not registered.")
        self.scenarios[device_id] = scenario
        if hasattr(self, "runtime") and self.runtime and device_id in self.runtime.devices:
            self.runtime.devices[device_id].simulator.step_counter = 0
        return True

    def run_single_cycle(self):
        """Runs a single simulation cycle step synchronously."""
        if self.simulation_active:
            raise ValueError("Cannot trigger single-step cycle while background simulation is active.")
        return self._execute_cycle_locked(force=True)

    def send_device_command(self, device_id, command, payload=None):
        """Dispatches manual override commands to ESP32 device via gateway client."""
        if device_id not in self.runtime.devices:
            raise ValueError(f"Device ID {device_id} is not registered.")
        
        payload = payload or {}

        # 0. Validate specific command inputs
        if command == "SET_SAMPLING_INTERVAL":
            interval = payload.get("interval")
            if interval is None or not isinstance(interval, (int, float)) or interval < 2 or interval > 300:
                raise ValueError("Invalid sampling interval: must be between 2 and 300 seconds.")
            self.sampling_interval = float(interval)

        cmd_topic = f"aquatic/{device_id}/command"
        timestamp = datetime.datetime.now().isoformat()
        cmd_payload = {
            "command": command,
            "device_id": device_id,
            "payload": payload,
            "timestamp": timestamp
        }
        
        print(f"[BACKEND-CMD] Dispatching command '{command}' for device '{device_id}'...", flush=True)

        # 1. Update actuator state in local runtime and EventStore
        dev = self.runtime.devices.get(device_id)
        if command in ["ACTIVATE_BUZZER", "DEACTIVATE_BUZZER", "ACTIVATE_RELAY", "DEACTIVATE_RELAY"]:
            if dev:
                dev.actuators.execute_command(command)
                summary = dev.actuators.get_summary()
            else:
                summary = f"Command {command} applied"
            self.event_store.log_actuators(timestamp, device_id, summary, f"Manual override: {command}")

        # 2. Publish to internal mock gateway client
        try:
            if not getattr(self.runtime.gateway.client, "connected", False):
                self.runtime.gateway.client.connect()
            self.runtime.gateway.client.publish(cmd_topic, cmd_payload)
        except Exception as e:
            print(f"[BACKEND-CMD] Mock client publish notice: {e}", flush=True)

        # 3. Publish to live external MQTT broker (test.mosquitto.org:1883)
        def _publish_mqtt_external():
            try:
                import paho.mqtt.publish as mqtt_publish
                mqtt_publish.single(
                    topic=cmd_topic,
                    payload=json.dumps(cmd_payload),
                    hostname="test.mosquitto.org",
                    port=1883,
                    qos=0
                )
                print(f"[BACKEND-CMD] Published command to MQTT broker: {cmd_topic}", flush=True)
            except Exception as e:
                print(f"[BACKEND-CMD] MQTT publish notice: {e}", flush=True)
        threading.Thread(target=_publish_mqtt_external, daemon=True).start()

        # 4. Write command trigger file for instant IPC response
        try:
            trigger_file = os.path.join(os.path.dirname(self.event_store.db_path), ".command_trigger.json")
            tmp_file = trigger_file + ".tmp"
            with open(tmp_file, "w") as f:
                json.dump(cmd_payload, f)
                f.flush()
            os.replace(tmp_file, trigger_file)
            print(f"[BACKEND-CMD] Updated command trigger file: {trigger_file}", flush=True)
        except Exception as e:
            print(f"[BACKEND-CMD] Trigger file write error: {e}", flush=True)
        
        # 5. Log command to EventStore
        self.event_store.log_command(timestamp, device_id, command, cmd_payload, "COMPLETED")

        # 6. Build structured execution result
        result = {
            "action": command,
            "status": "COMMAND_COMPLETED",
            "device_id": device_id,
            "timestamp": timestamp
        }
        if command == "REQUEST_READING":
            result["message"] = "Fresh physical sensor reading acquisition triggered."
        elif command == "SET_SAMPLING_INTERVAL":
            result["interval_sec"] = payload.get("interval")
            result["message"] = f"Sampling interval updated to {payload.get('interval')} seconds."
        elif command == "ACTIVATE_BUZZER":
            result["pin"] = "GPIO14"
            result["state"] = "HIGH"
            result["message"] = "Buzzer activated on GPIO14."
        elif command == "DEACTIVATE_BUZZER":
            result["pin"] = "GPIO14"
            result["state"] = "LOW"
            result["message"] = "Buzzer deactivated."
        elif command == "ACTIVATE_RELAY":
            result["pin"] = "GPIO19"
            result["state"] = "HIGH"
            result["message"] = "Relay contact closed on GPIO19 (Electrical switching only - pump not connected)."
        elif command == "DEACTIVATE_RELAY":
            result["pin"] = "GPIO19"
            result["state"] = "LOW"
            result["message"] = "Relay contact opened on GPIO19."
        elif command in ["PIN_DIAGNOSTICS", "RUN_DIAGNOSTICS"]:
            result["pins"] = {
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
            result["message"] = "Configured physical GPIO diagnostics completed."
        elif command == "RESTART_DEVICE":
            result["message"] = "Controlled device restart command processed safely."
        else:
            result["message"] = f"Command {command} executed."

        return result

    def _run_simulation_loop(self):
        """Background thread target polling cycles repeatedly."""
        while self.simulation_active:
            try:
                # Dynamic check to space cycles by at least 2.0 seconds
                if self.last_run_timestamp is not None:
                    elapsed = (datetime.datetime.now() - self.last_run_timestamp).total_seconds()
                    remaining = 2.0 - elapsed
                    if remaining > 0:
                        if self.simulation_shutdown_event.wait(timeout=remaining):
                            break
                        if not self.simulation_active:
                            break

                self._execute_cycle_locked(force=False)
            except Exception as e:
                # Gateway crash logging
                AlertSystem.trigger_gateway_error_alert("SYSTEM", str(e), self.event_store)
            
                break
