import datetime
import json
import logging
from src.iot.sensor_simulator import AquaticSensorSimulator
from src.iot.edge_validation import EdgeValidator
from src.iot.actuators import VirtualActuators

# V2 sub-layer imports
from src.iot.config import DeviceConfig
from src.iot.drivers.sensors import VirtualEnvironment
from src.iot.hal import HAL
from src.iot.scheduler import SimpleScheduler, Task, Queue, Event
from src.iot.communication import CommunicationLayer

class ESP32Device:
    """
    Simulates an ESP32 microcontroller deployed at an aquatic site.
    Implements a strict finite state machine (FSM) representing the device lifecycle:
    BOOT -> INITIALIZING -> CONNECTING -> ONLINE -> SENSING -> PUBLISHING -> WAITING -> ERROR -> RECOVERING
    
    Refactored in Version 2.0 to run a tick-based task scheduler with HAL, virtual drivers,
    network simulation, and configuration layers.
    """
    def __init__(self, device_id: str, ecosystem_type: str = "Freshwater", dataset_route: str = "caml", location: dict = None, use_mock: bool = True):
        self.device_id = device_id
        self.ecosystem_type = ecosystem_type
        self.dataset_route = dataset_route
        self.location = location if location else {"latitude": 27.5, "longitude": -81.2}
        
        self.state = "BOOT"
        self.sensor_status = "OK"
        self.firmware_version = "2.0.0"

        # 1. Load configuration layer
        self.config = DeviceConfig(device_id=device_id)
        self.sampling_interval = self.config.get_sampling_interval()

        # 2. Setup virtual physical environment
        self.simulator = AquaticSensorSimulator(ecosystem_type=ecosystem_type)
        self.env = VirtualEnvironment(simulator=self.simulator)

        # 3. Setup Hardware Abstraction Layer (HAL)
        self.hal = HAL(config=self.config, env=self.env)

        # 4. Setup legacy actuators wrapper linked directly to HAL
        self.actuators = VirtualActuators(hal=self.hal)

        # 5. Setup Communication Layer
        self.comm = CommunicationLayer(client_id=device_id, use_mock=use_mock)

        # Gateway/Server subscription messages routing
        self.comm.client.set_on_message(self._on_command_or_decision_received)

        # 6. Edge Validation
        self.validator = EdgeValidator(bounds=self.config.get_physical_bounds())

        # Log buffers
        self.state_logs = []
        self.command_history = []
        self.published_telemetry = []

        # 7. Setup RTOS Scheduler & Queues
        self.scheduler = SimpleScheduler()
        self.telemetry_queue = Queue()
        self.cycle_output_queue = Queue()

        self._register_rtos_tasks()
        self._transition_to("BOOT")

    # Property descriptors to expose wifi/mqtt state seamlessly
    @property
    def wifi_connected(self) -> bool:
        return self.comm.wifi_connected
    @wifi_connected.setter
    def wifi_connected(self, val: bool):
        self.comm.wifi_connected = val

    @property
    def mqtt_connected(self) -> bool:
        return self.comm.mqtt_connected
    @mqtt_connected.setter
    def mqtt_connected(self, val: bool):
        self.comm.mqtt_connected = val

    @property
    def client(self):
        """Exposes client for backend callback hook compatibility."""
        return self.comm.client

    def _register_rtos_tasks(self):
        """Registers virtual FreeRTOS tasks to be run cooperatively."""
        # Sensor poll task
        self.scheduler.register_task(
            Task(name="SensorTask", period_ticks=1, callback=self._sensor_task_handler, priority=2)
        )
        # Communication task
        self.scheduler.register_task(
            Task(name="CommTask", period_ticks=1, callback=self._communication_task_handler, priority=1)
        )
        # Health status check task
        self.scheduler.register_task(
            Task(name="HealthTask", period_ticks=1, callback=self._health_task_handler, priority=3)
        )

    def _sensor_task_handler(self):
        """Scheduled task reading from HAL and queueing validated telemetry."""
        if self.state not in ["ONLINE", "WAITING", "SENSING"]:
            return

        self._transition_to("SENSING")
        raw_readings = self.hal.read_all_sensors()

        # Validate
        is_valid, validation_errors, health = self.validator.validate(raw_readings)
        self.sensor_status = health

        # Construct payload
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

        if not is_valid:
            self.state_logs.append(f"Edge Validation Failure: {validation_errors}")

        self.telemetry_queue.put(telemetry)
        self._transition_to("PUBLISHING")

    def _communication_task_handler(self):
        """Scheduled task responsible for dequeuing telemetry and publishing via MQTT."""
        if self.state != "PUBLISHING":
            return

        telemetry = self.telemetry_queue.get()
        if not telemetry:
            return

        try:
            # Publish telemetry
            topic = self.config.get_mqtt().get("topics", {}).get("telemetry", f"aquatic/{self.device_id}/telemetry")
            self.comm.publish(topic, telemetry)
            self.published_telemetry.append(telemetry)

            # Publish status status
            status_topic = self.config.get_mqtt().get("topics", {}).get("status", f"aquatic/{self.device_id}/status")
            status_payload = {
                "device_id": self.device_id,
                "state": "ONLINE",
                "sensor_status": self.sensor_status,
                "firmware_version": self.firmware_version
            }
            self.comm.publish(status_topic, status_payload)

            if self.sensor_status == "FAULT":
                self._transition_to("ERROR")
            else:
                self._transition_to("WAITING")

            # Route telemetry to the cycle output queue for execute_one_complete_cycle
            self.cycle_output_queue.put(telemetry)

        except Exception as e:
            self.state_logs.append(f"MQTT Publish Failed: {e}")
            self._transition_to("ERROR")

    def _health_task_handler(self):
        """Scheduled task responsible for checking hardware health status."""
        # Simple task mapping: monitors WiFi state changes or logs health diagnostics
        pass

    def _transition_to(self, new_state: str):
        old_state = self.state
        self.state = new_state
        log_msg = f"State transition: {old_state} -> {new_state}"
        self.state_logs.append(log_msg)

    def boot(self) -> bool:
        """Initializes boot sequence."""
        if self.state != "BOOT":
            return False
        self._transition_to("INITIALIZING")
        return True

    def initialize_sensors(self) -> bool:
        """Simulates sensor hardware check using the HAL."""
        if self.state != "INITIALIZING":
            return False
        
        self.hal.init_hardware()
        self.sensor_status = "OK"
        self._transition_to("CONNECTING")
        return True

    def connect_network(self, host: str = "localhost", port: int = 1883) -> bool:
        """Simulates Wi-Fi and MQTT connection."""
        if self.state != "CONNECTING":
            return False
        
        wifi_cfg = self.config.get_wifi()
        self.comm.connect_wifi(wifi_cfg.get("ssid", "DefaultSSID"), wifi_cfg.get("password", "DefaultPW"))
        
        if self.comm.connect_mqtt(host, port):
            # Subscribe to command and decision channels
            topics = self.config.get_mqtt().get("topics", {})
            cmd_topic = topics.get("command", f"aquatic/{self.device_id}/command")
            dec_topic = topics.get("decision", f"aquatic/{self.device_id}/decision")
            
            self.comm.subscribe(cmd_topic)
            self.comm.subscribe(dec_topic)
            
            self._transition_to("ONLINE")
            return True
        else:
            self.state_logs.append("Network Connection Failed")
            self._transition_to("ERROR")
            return False

    def poll_and_validate(self, scenario: str = "NORMAL", timestamp=None) -> dict:
        """Polls raw sensors, runs edge validation, and constructs telemetry payload (Sync version)."""
        if self.state not in ["ONLINE", "WAITING", "SENSING"]:
            return None
        
        self._transition_to("SENSING")
        if timestamp is None:
            timestamp = datetime.datetime.now()

        # Update environment to sync with simulator
        raw_data = self.simulator.generate_reading(scenario=scenario, timestamp=timestamp)
        dataset_backed = ["NORMAL", "KNOWN_BLOOM_RISK", "FRESHWATER_CONTEXT_RISK", "MARINE_BLOOM_RISK", "ENVIRONMENTAL_STRESS", "UNUSUAL_ENVIRONMENTAL_CONDITION", "SENSOR_FAULT"]
        if raw_data["latitude"] is not None and scenario not in dataset_backed:
            raw_data["latitude"] = self.location["latitude"]
            raw_data["longitude"] = self.location["longitude"]

        self.env.update_environment(raw_data, scenario, timestamp)

        # Read from HAL
        raw_readings = self.hal.read_all_sensors()

        # Local edge validation
        is_valid, validation_errors, health = self.validator.validate(raw_readings)
        self.sensor_status = health

        # Construct versioned Telemetry payload
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

        if not is_valid:
            self.state_logs.append(f"Edge Validation Failure: {validation_errors}")

        self._transition_to("PUBLISHING")
        return telemetry

    def publish_telemetry(self, telemetry: dict) -> bool:
        """Publishes telemetry payload to MQTT topic (Sync version)."""
        if self.state != "PUBLISHING":
            return False
        
        try:
            topic = self.config.get_mqtt().get("topics", {}).get("telemetry", f"aquatic/{self.device_id}/telemetry")
            self.comm.publish(topic, telemetry)
            self.published_telemetry.append(telemetry)
            
            # Publish state status
            status_topic = self.config.get_mqtt().get("topics", {}).get("status", f"aquatic/{self.device_id}/status")
            status_payload = {
                "device_id": self.device_id,
                "state": "ONLINE",
                "sensor_status": self.sensor_status,
                "firmware_version": self.firmware_version
            }
            self.comm.publish(status_topic, status_payload)
            
            if self.sensor_status == "FAULT":
                self._transition_to("ERROR")
            else:
                self._transition_to("WAITING")
            return True
        except Exception as e:
            self.state_logs.append(f"MQTT Publish Failed: {e}")
            self._transition_to("ERROR")
            return False

    def run_reconnection(self) -> bool:
        """Attempts recovery and reconnect from ERROR state."""
        if self.state != "ERROR":
            return False
        
        self._transition_to("RECOVERING")
        try:
            self.comm.disconnect_mqtt()
            self.comm.connect_mqtt()
            
            topics = self.config.get_mqtt().get("topics", {})
            cmd_topic = topics.get("command", f"aquatic/{self.device_id}/command")
            dec_topic = topics.get("decision", f"aquatic/{self.device_id}/decision")
            
            self.comm.subscribe(cmd_topic)
            self.comm.subscribe(dec_topic)
            
            self.wifi_connected = True
            self.mqtt_connected = True
            self.sensor_status = "OK"
            self._transition_to("ONLINE")
            return True
        except Exception as e:
            self.state_logs.append(f"Reconnection Recovery Failed: {e}")
            self._transition_to("ERROR")
            return False

    def execute_one_complete_cycle(self, scenario: str = "NORMAL", timestamp=None) -> dict:
        """Runs the state machine through one complete poll-validate-publish cycle using scheduled tasks."""
        if self.state == "BOOT":
            self.boot()
        if self.state == "INITIALIZING":
            self.initialize_sensors()
        if self.state == "CONNECTING":
            self.connect_network()
        
        if self.state == "ERROR":
            self.run_reconnection()

        if self.state in ["ONLINE", "WAITING", "SENSING", "PUBLISHING"]:
            if timestamp is None:
                timestamp = datetime.datetime.now()

            # Clear queues to ensure fresh cycle synchronization
            self.telemetry_queue.clear()
            self.cycle_output_queue.clear()

            # 1. Update the virtual environment with the simulated readings
            raw_data = self.simulator.generate_reading(scenario=scenario, timestamp=timestamp)
            dataset_backed = ["NORMAL", "KNOWN_BLOOM_RISK", "FRESHWATER_CONTEXT_RISK", "MARINE_BLOOM_RISK", "ENVIRONMENTAL_STRESS", "UNUSUAL_ENVIRONMENTAL_CONDITION", "SENSOR_FAULT"]
            if raw_data["latitude"] is not None and scenario not in dataset_backed:
                raw_data["latitude"] = self.location["latitude"]
                raw_data["longitude"] = self.location["longitude"]

            self.env.update_environment(raw_data, scenario, timestamp)

            # 2. Step the scheduler to trigger SensorTask & CommTask
            self.scheduler.step()

            # 3. Fetch validated telemetry output generated during scheduler execution
            telemetry = self.cycle_output_queue.get()
            return telemetry
        return None

    def _on_command_or_decision_received(self, topic: str, payload: dict):
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
                self.comm.disconnect_mqtt()
                self._transition_to("BOOT")
            else:
                self.actuators.execute_command(cmd_type)

        # 2. Decision/Actuator Channel
        elif topic.endswith("/decision"):
            fusion_state = payload.get("fusion", {}).get("final_state")
            if fusion_state:
                # Update physical actuators (LEDs, aerator) via HAL
                self.actuators.update_state(fusion_state)
