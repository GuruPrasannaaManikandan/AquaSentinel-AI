import os
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

    def register_decision_callback(self, callback):
        self.on_decision_callbacks.append(callback)

    def register_telemetry_callback(self, callback):
        self.on_telemetry_callbacks.append(callback)

    def start_simulation(self):
        """Starts background simulation runner."""
        if self.simulation_thread and self.simulation_thread.is_alive():
            return False
        
        # Connect client lines
        self.runtime.start()
        self.simulation_active = True
        self.simulation_shutdown_event.clear()
        self.simulation_thread = threading.Thread(target=self._run_simulation_loop, daemon=True)
        self.simulation_thread.start()
        return True

    def stop_simulation(self):
        """Stops background simulation runner."""
        if not self.simulation_active:
            return False
        
        self.simulation_active = False
        self.simulation_shutdown_event.set()
        if self.simulation_thread:
            self.simulation_thread.join(timeout=2.0)
        self.runtime.stop()
        return True

    def set_scenario(self, device_id, scenario):
        """Sets scenario type for a device."""
        if device_id not in self.scenarios:
            raise ValueError(f"Device ID {device_id} not registered.")
        self.scenarios[device_id] = scenario
        return True

    def run_single_cycle(self):
        """Runs a single simulation cycle step synchronously."""
        if self.simulation_active:
            raise ValueError("Cannot trigger single-step cycle while background simulation is active.")
            
        # Check connection status
        if not self.runtime.devices["AQUA_FRESH_001"].wifi_connected:
            self.runtime.start()
        
        timestamp = datetime.datetime.now()
        self.last_run_timestamp = timestamp
        return self.runtime.execute_cycle(self.scenarios, timestamp)

    def send_device_command(self, device_id, command, payload=None):
        """Dispatches manual override commands to ESP32 device via gateway client."""
        if device_id not in self.runtime.devices:
            raise ValueError(f"Device ID {device_id} is not registered.")
        
        cmd_topic = f"aquatic/{device_id}/command"
        cmd_payload = {
            "command": command,
            "device_id": device_id,
            "payload": payload or {}
        }
        
        # Publish
        self.runtime.gateway.client.publish(cmd_topic, cmd_payload)
        
        # Log command
        timestamp = datetime.datetime.now().isoformat()
        self.event_store.log_command(timestamp, device_id, command, cmd_payload, "SENT")
        return True

    def _run_simulation_loop(self):
        """Background thread target polling cycles repeatedly."""
        while self.simulation_active:
            try:
                # Check connection status
                if not self.runtime.devices["AQUA_FRESH_001"].wifi_connected:
                    self.runtime.start()
                # Direct execute_cycle to avoid raising active guard in run_single_cycle
                timestamp = datetime.datetime.now()
                self.last_run_timestamp = timestamp
                self.runtime.execute_cycle(self.scenarios, timestamp)
            except Exception as e:
                # Gateway crash logging
                AlertSystem.trigger_gateway_error_alert("SYSTEM", str(e), self.event_store)
            
            # Wait for 2.0 seconds or until shutdown event is set
            if self.simulation_shutdown_event.wait(timeout=2.0):
                break
