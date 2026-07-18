import datetime
import json
import logging
from src.iot.mqtt_client import MQTTClient
from src.iot.sensor_simulator import AquaticSensorSimulator
from src.iot.edge_validation import EdgeValidator
from src.iot.actuators import VirtualActuators

class ESP32Device:
    """
    Simulates an ESP32 microcontroller deployed at an aquatic site.
    Implements a strict finite state machine (FSM) representing the device lifecycle:
    BOOT -> INITIALIZING -> CONNECTING -> ONLINE -> SENSING -> PUBLISHING -> WAITING -> ERROR -> RECOVERING
    """
    def __init__(self, device_id, ecosystem_type="Freshwater", dataset_route="caml", location=None):
        self.device_id = device_id
        self.ecosystem_type = ecosystem_type
        self.dataset_route = dataset_route
        self.location = location if location else {"latitude": 27.5, "longitude": -81.2}
        
        self.state = "BOOT"
        self.wifi_connected = False
        self.mqtt_connected = False
        self.sensor_status = "OK"
        self.sampling_interval = 10 # virtual seconds
        self.firmware_version = "1.0.0"

        # Subsystems
        self.client = MQTTClient(client_id=device_id)
        self.simulator = AquaticSensorSimulator(ecosystem_type=ecosystem_type)
        self.validator = EdgeValidator()
        self.actuators = VirtualActuators()

        # Connect command callbacks
        self.client.set_on_message(self._on_command_or_decision_received)

        # Logs
        self.state_logs = []
        self.command_history = []
        self.published_telemetry = []

        self._transition_to("BOOT")

    def _transition_to(self, new_state):
        old_state = self.state
        self.state = new_state
        log_msg = f"State transition: {old_state} -> {new_state}"
        self.state_logs.append(log_msg)

    def boot(self):
        """Initializes boot sequence."""
        if self.state != "BOOT":
            return False
        self._transition_to("INITIALIZING")
        return True

    def initialize_sensors(self):
        """Simulates sensor hardware check."""
        if self.state != "INITIALIZING":
            return False
        # Perform check
        self.sensor_status = "OK"
        self._transition_to("CONNECTING")
        return True

    def connect_network(self, host="localhost", port=1883):
        """Simulates Wi-Fi and MQTT connection."""
        if self.state != "CONNECTING":
            return False
        
        # Connect client
        try:
            self.wifi_connected = True
            self.client.connect(host, port)
            self.mqtt_connected = True
            
            # Subscribe to command and decision channels
            self.client.subscribe(f"aquatic/{self.device_id}/command")
            self.client.subscribe(f"aquatic/{self.device_id}/decision")
            
            self._transition_to("ONLINE")
            return True
        except Exception as e:
            self.state_logs.append(f"Network Connection Failed: {e}")
            self.wifi_connected = False
            self.mqtt_connected = False
            self._transition_to("ERROR")
            return False

    def poll_and_validate(self, scenario="NORMAL", timestamp=None):
        """Polls raw sensors, runs edge validation, and constructs telemetry payload."""
        if self.state not in ["ONLINE", "WAITING", "SENSING"]:
            return None
        
        self._transition_to("SENSING")
        if timestamp is None:
            timestamp = datetime.datetime.now()

        # 1. Poll virtual sensors
        raw_readings = self.simulator.generate_reading(scenario=scenario, timestamp=timestamp)
        
        # Override GPS coordinate from location profile if not using dataset-backed demonstration scenarios
        dataset_backed = ["NORMAL", "KNOWN_BLOOM_RISK", "FRESHWATER_CONTEXT_RISK", "MARINE_BLOOM_RISK", "ENVIRONMENTAL_STRESS", "UNUSUAL_ENVIRONMENTAL_CONDITION", "SENSOR_FAULT"]
        if raw_readings["latitude"] is not None and scenario not in dataset_backed:
            raw_readings["latitude"] = self.location["latitude"]
            raw_readings["longitude"] = self.location["longitude"]

        # 2. Local edge validation
        is_valid, validation_errors, health = self.validator.validate(raw_readings)
        self.sensor_status = health

        # 3. Construct versioned Telemetry payload
        telemetry = {
            "schema_version": "1.0",
            "device_id": self.device_id,
            "timestamp": raw_readings["timestamp"],
            "provenance_timestamp": raw_readings.get("provenance_timestamp"),
            "dataset_route": self.dataset_route,
            "location": {
                "latitude": raw_readings["latitude"],
                "longitude": raw_readings["longitude"]
            },
            "sensors": {
                "temperature_c": raw_readings["temperature_c"],
                "salinity_ppt": raw_readings["salinity_ppt"],
                "ph": raw_readings["ph"],
                "turbidity_ntu": raw_readings["turbidity_ntu"],
                "dissolved_oxygen_mg_l": raw_readings["dissolved_oxygen_mg_l"],
                "distance_to_water_m": raw_readings.get("distance_to_water_m"),
                "sample_depth": raw_readings.get("sample_depth")
            },
            "device_health": {
                "wifi_connected": self.wifi_connected,
                "mqtt_connected": self.mqtt_connected,
                "sensor_status": self.sensor_status
            }
        }

        # If data is completely invalid due to FAULT, we flag errors in logs but publish degraded
        if not is_valid:
            self.state_logs.append(f"Edge Validation Failure: {validation_errors}")

        self._transition_to("PUBLISHING")
        return telemetry

    def publish_telemetry(self, telemetry):
        """Publishes telemetry payload to MQTT topic."""
        if self.state != "PUBLISHING":
            return False
        
        try:
            topic = f"aquatic/{self.device_id}/telemetry"
            self.client.publish(topic, telemetry)
            self.published_telemetry.append(telemetry)
            
            # Publish state status
            status_topic = f"aquatic/{self.device_id}/status"
            status_payload = {
                "device_id": self.device_id,
                "state": "ONLINE",
                "sensor_status": self.sensor_status,
                "firmware_version": self.firmware_version
            }
            self.client.publish(status_topic, status_payload)
            
            if self.sensor_status == "FAULT":
                self._transition_to("ERROR")
            else:
                self._transition_to("WAITING")
            return True
        except Exception as e:
            self.state_logs.append(f"MQTT Publish Failed: {e}")
            self._transition_to("ERROR")
            return False

    def run_reconnection(self):
        """Attempts recovery and reconnect from ERROR state."""
        if self.state != "ERROR":
            return False
        
        self._transition_to("RECOVERING")
        # Attempt reconnection
        try:
            self.client.disconnect()
            self.client.connect()
            self.client.subscribe(f"aquatic/{self.device_id}/command")
            self.client.subscribe(f"aquatic/{self.device_id}/decision")
            
            self.wifi_connected = True
            self.mqtt_connected = True
            self.sensor_status = "OK"
            self._transition_to("ONLINE")
            return True
        except Exception as e:
            self.state_logs.append(f"Reconnection Recovery Failed: {e}")
            self._transition_to("ERROR")
            return False

    def execute_one_complete_cycle(self, scenario="NORMAL", timestamp=None):
        """Runs the state machine through one complete poll-validate-publish cycle."""
        if self.state == "BOOT":
            self.boot()
        if self.state == "INITIALIZING":
            self.initialize_sensors()
        if self.state == "CONNECTING":
            self.connect_network()
        
        if self.state == "ERROR":
            self.run_reconnection()

        if self.state in ["ONLINE", "WAITING"]:
            telemetry = self.poll_and_validate(scenario=scenario, timestamp=timestamp)
            if telemetry:
                self.publish_telemetry(telemetry)
                return telemetry
        return None

    def _on_command_or_decision_received(self, topic, payload):
        """Handles messages from subscribed command and decision topics."""
        # 1. Command Channel
        if topic.endswith("/command"):
            cmd_type = payload.get("command")
            self.command_history.append({
                "timestamp": datetime.datetime.now().isoformat(),
                "command": cmd_type,
                "payload": payload,
                "status": "EXECUTED"
            })
            
            # Execute physical action
            if cmd_type == "RESTART_DEVICE":
                self.state_logs.append("Executing Command: RESTART_DEVICE")
                self.client.disconnect()
                self._transition_to("BOOT")
            else:
                self.actuators.execute_command(cmd_type)

        # 2. Decision/Actuator Channel
        elif topic.endswith("/decision"):
            fusion_state = payload.get("fusion", {}).get("final_state")
            if fusion_state:
                # Update physical actuators (LEDs, aerator)
                self.actuators.update_state(fusion_state)
