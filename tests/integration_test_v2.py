import unittest
import os
import sys

# Ensure project root is on Python's path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

from src.iot.esp32_device import ESP32Device
from src.iot.gateway import Gateway
from src.iot.event_store import EventStore
from src.iot.drivers.base_driver import BaseSensorDriver

class TestIntegrationV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db_path = os.path.join(project_dir, "models", "fusion", "test_integration_events.db")
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass
        cls.event_store = EventStore(db_path=cls.test_db_path)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

    def test_end_to_end_integration_flow(self):
        print("\n==================================================")
        print("RUNNING END-TO-END INTEGRATION TEST SUITE (VERSION 2.1)")
        print("==================================================")

        # -----------------------------------------------------------------
        # TEST A: Telemetry Flow (Device -> Gateway -> EventStore)
        # -----------------------------------------------------------------
        print("\n--- Test A: Telemetry Flow ---")
        device = ESP32Device(device_id="AQUA_FRESH_001", use_mock=True)
        gateway = Gateway(workspace_dir=project_dir, use_mock=True)
        gateway.event_store = self.event_store

        # Hook device client to mock broker
        device.boot()
        device.initialize_sensors()
        device.connect_network()
        
        # Connect Gateway
        gateway.connect()

        # Execute one complete tick cycle on device
        print("[Device] Generating and publishing telemetry...")
        telemetry = device.execute_one_complete_cycle(scenario="NORMAL")
        self.assertIsNotNone(telemetry)
        self.assertEqual(telemetry["device_id"], "AQUA_FRESH_001")

        # Gateway handles published messages synchronously in mock mode
        print("[Gateway] Receiving and processing message...")
        # Since use_mock=True connects both client interfaces to the InMemoryMQTTBroker singleton,
        # the Gateway's subscription callback fires synchronously on publish.
        
        # Verify telemetry was logged
        latest_telemetry = self.event_store.get_latest_telemetry("AQUA_FRESH_001")
        self.assertIsNotNone(latest_telemetry)
        self.assertEqual(latest_telemetry["device_id"], "AQUA_FRESH_001")
        print("  SUCCESS: Telemetry successfully logged in EventStore.")

        # Verify decision was logged
        decisions = self.event_store.get_historical_decisions("AQUA_FRESH_001")
        self.assertTrue(len(decisions) > 0)
        self.assertEqual(decisions[0]["final_state"], "NORMAL")
        print("  SUCCESS: Evidence Fusion completed. State: NORMAL.")

        # -----------------------------------------------------------------
        # TEST B: Resiliency on Disconnect
        # -----------------------------------------------------------------
        print("\n--- Test B: Device Disconnection ---")
        print("[Device] Stopping MQTT Client connection...")
        device.comm.disconnect_mqtt()
        self.assertFalse(device.mqtt_connected)
        
        # Verify backend gateway and storage remains active and does not crash
        print("[Gateway] Verifying backend stability...")
        # We trigger a gateway check or insert manual telemetry check
        self.assertTrue(gateway.client.connected)
        print("  SUCCESS: Backend is running stably. Telemetry channel is active.")

        # -----------------------------------------------------------------
        # TEST C: Automatic Reconnection
        # -----------------------------------------------------------------
        print("\n--- Test C: Device Reconnection ---")
        print("[Device] Re-initiating connection...")
        device.state = "ERROR"
        device.run_reconnection()
        self.assertTrue(device.mqtt_connected)
        self.assertEqual(device.state, "ONLINE")

        print("[Device] Resuming telemetry tick cycle...")
        telemetry_new = device.execute_one_complete_cycle(scenario="NORMAL")
        self.assertIsNotNone(telemetry_new)
        print("  SUCCESS: Reconnection successful. Telemetry resumed.")

        # -----------------------------------------------------------------
        # TEST D: Fault Injection & Alert Propagation
        # -----------------------------------------------------------------
        print("\n--- Test D: Fault Injection & Propagation ---")
        print("[Device] Injecting SENSOR_FAULT scenario...")
        
        # Run fault scenario cycle
        telemetry_fault = device.execute_one_complete_cycle(scenario="SENSOR_FAULT")
        self.assertIsNotNone(telemetry_fault)
        self.assertEqual(telemetry_fault["device_health"]["sensor_status"], "FAULT")
        print("  [HAL] Sensor fault detected. Telemetry status flagged.")

        # Verify gateway routed correctly as fault bypass
        decisions_fault = self.event_store.get_historical_decisions("AQUA_FRESH_001")
        latest_decision = decisions_fault[-1]
        self.assertEqual(latest_decision["final_state"], "SENSOR_FAULT")
        self.assertEqual(latest_decision["reason_code"], "SENSOR_FAULT_BYPASS")
        print("  [Gateway] SENSOR_FAULT bypass triggered. Fusion state: SENSOR_FAULT.")
        print("  SUCCESS: Fault information successfully propagated and persisted.")

        # -----------------------------------------------------------------
        # TEST E: Driver Swapping (Hardware Abstraction Proof)
        # -----------------------------------------------------------------
        print("\n--- Test E: Driver Swapping ---")
        print("[HAL] Swapping VirtualTemperatureSensorDriver with ESP32PhysicalDriver mock...")

        class ESP32PhysicalTemperatureDriver(BaseSensorDriver):
            """Mock of physical temperature driver using machine.ADC/I2C."""
            def read(self) -> float:
                # Mock reading 28.5 degrees directly from chip hardware registers
                return 28.5

        # Swap temperature driver inside the HAL without modifying device loop or config layers
        physical_driver = ESP32PhysicalTemperatureDriver("TEMP_ESP32", pin=35)
        device.hal.sensors["temperature"] = physical_driver

        # Run cycle and verify it uses the swapped driver value
        telemetry_swap = device.execute_one_complete_cycle(scenario="NORMAL")
        self.assertIsNotNone(telemetry_swap)
        self.assertEqual(telemetry_swap["sensors"]["temperature_c"], 28.5)
        print("  [HAL] Successfully read physical driver value: 28.5 C.")
        print("  SUCCESS: Swapped driver execution succeeded with zero code modifications above the driver layer.")

        print("\n==================================================")
        print("ALL VERSION 2.1 INTEGRATION TESTS PASSED SUCCESSFULLY!")
        print("==================================================")

if __name__ == "__main__":
    unittest.main()
