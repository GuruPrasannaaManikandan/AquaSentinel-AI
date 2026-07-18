import os
import datetime
from src.iot.esp32_device import ESP32Device
from src.iot.gateway import Gateway

class DeviceRuntimeManager:
    """
    Manages the end-to-end execution of multiple virtual IoT devices and the Central Gateway.
    Handles coordinate setup, running time-step cycles, and synchronizing state responses.
    """
    def __init__(self, workspace_dir=None, use_mock=True):
        self.gateway = Gateway(workspace_dir=workspace_dir, use_mock=use_mock)
        self.devices = {}
        
        # Initialize standard devices from registry
        self.devices["AQUA_FRESH_001"] = ESP32Device(
            device_id="AQUA_FRESH_001",
            ecosystem_type="Freshwater",
            dataset_route="caml",
            location={"latitude": 27.5, "longitude": -81.2}
        )
        self.devices["AQUA_MARINE_001"] = ESP32Device(
            device_id="AQUA_MARINE_001",
            ecosystem_type="Marine",
            dataset_route="habsos",
            location={"latitude": 27.5, "longitude": -82.5}
        )

    def start(self):
        """Starts connection for the gateway and all virtual devices."""
        self.gateway.connect()
        for device in self.devices.values():
            # Reset state to force clean connection transition
            device.state = "BOOT"
            # Device runs through BOOT -> INITIALIZING -> CONNECTING -> ONLINE
            device.boot()
            device.initialize_sensors()
            device.connect_network()

    def stop(self):
        """Disconnects gateway and devices cleanly."""
        self.gateway.disconnect()
        for device in self.devices.values():
            device.client.disconnect()

    def execute_cycle(self, scenarios=None, timestamp=None):
        """
        Executes exactly one complete cycle across all registered virtual devices.
        Workflow: 
          Sensors -> Poll -> Edge Validate -> Telemetry -> Gateway Route -> inference -> Fusion -> Decision -> Actuator update.
        """
        if scenarios is None:
            scenarios = {}
        if timestamp is None:
            timestamp = datetime.datetime.now()

        cycle_results = {}
        for device_id, device in self.devices.items():
            scenario = scenarios.get(device_id, "NORMAL")
            # This triggers the entire synchronous MQTT publish-receive loop
            telemetry = device.execute_one_complete_cycle(scenario=scenario, timestamp=timestamp)
            cycle_results[device_id] = {
                "telemetry": telemetry,
                "state": device.state,
                "sensor_status": device.sensor_status,
                "actuator_state": device.actuators.get_summary()
            }
        return cycle_results
