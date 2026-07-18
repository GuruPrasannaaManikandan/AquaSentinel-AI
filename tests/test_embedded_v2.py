import unittest
import os
import datetime
from src.iot.config import DeviceConfig
from src.iot.drivers.sensors import VirtualEnvironment, VirtualPHSensorDriver, VirtualGPSSensorDriver
from src.iot.drivers.actuators import VirtualLEDDriver
from src.iot.hal import HAL
from src.iot.scheduler import SimpleScheduler, Task, Queue, Event
from src.iot.esp32_device import ESP32Device

class TestEmbeddedV2(unittest.TestCase):
    def test_1_queue_and_event(self):
        """Test embedded queue buffer capacity and event signal behaviors."""
        q = Queue(maxsize=2)
        self.assertTrue(q.put("a"))
        self.assertTrue(q.put("b"))
        self.assertFalse(q.put("c"))  # exceeds maxsize
        self.assertEqual(q.get(), "a")
        self.assertEqual(q.get(), "b")
        self.assertIsNone(q.get())

        e = Event()
        self.assertFalse(e.is_set())
        e.set()
        self.assertTrue(e.is_set())
        e.clear()
        self.assertFalse(e.is_set())

    def test_2_scheduler_priority_and_tick(self):
        """Verify scheduler prioritizes and runs tasks periodically based on ticks."""
        scheduler = SimpleScheduler()
        calls = []
        task_a = Task("TaskA", period_ticks=2, callback=lambda: calls.append("A"), priority=1)
        task_b = Task("TaskB", period_ticks=1, callback=lambda: calls.append("B"), priority=5)

        scheduler.register_task(task_a)
        scheduler.register_task(task_b)

        # Tick 1: TaskB should run (period 1), TaskA should not run yet (period 2)
        scheduler.step()
        self.assertEqual(calls, ["B"])

        # Tick 2: Both run, TaskB runs first due to higher priority (5 vs 1)
        calls.clear()
        scheduler.step()
        self.assertEqual(calls, ["B", "A"])

    def test_3_config_loading_and_fallback(self):
        """Ensure device config reads JSON files correctly and falls back to default safely."""
        cfg_exist = DeviceConfig("AQUA_FRESH_001")
        self.assertEqual(cfg_exist.get_sampling_interval(), 10)
        self.assertEqual(cfg_exist.get_gpio().get("ph"), 32)

        cfg_fallback = DeviceConfig("DYNAMIC_TEST_DEV")
        self.assertEqual(cfg_fallback.get_sampling_interval(), 10)
        self.assertEqual(cfg_fallback.get_wifi().get("ssid"), "AquaNet_Default")

    def test_4_calibration_offset_scale(self):
        """Assert calibration offset and scale multiplier are correctly applied to sensor drivers."""
        env = VirtualEnvironment()
        env.update_environment({"ph": 7.0})
        
        # Raw ph: 7.0, Calibrated: scale=1.5, offset=-0.5 -> 7.0 * 1.5 - 0.5 = 10.0
        driver = VirtualPHSensorDriver("PH_CAL", config={"offset": -0.5, "scale": 1.5}, env=env)
        self.assertEqual(driver.read(), 10.0)

    def test_5_hal_unified_telemetry_and_actuators(self):
        """Verify HAL unified telemetry aggregation and actuator writing integration."""
        cfg = DeviceConfig("AQUA_FRESH_001")
        env = VirtualEnvironment()
        readings = {
            "temperature_c": 25.0,
            "salinity_ppt": 0.2,
            "ph": 8.0,
            "turbidity_ntu": 3.5,
            "dissolved_oxygen_mg_l": 9.0,
            "latitude": 27.5,
            "longitude": -81.2,
            "timestamp": "2026-07-19T00:00:00",
            "provenance_timestamp": "2026-07-19T00:00:00",
            "distance_to_water_m": 250.0,
            "sample_depth": 0.5
        }
        env.update_environment(readings)
        hal = HAL(config=cfg, env=env)
        
        # Verify telemetry structure aggregation
        hal_readings = hal.read_all_sensors()
        self.assertEqual(hal_readings["ph"], 8.0)
        self.assertEqual(hal_readings["temperature_c"], 25.0)
        self.assertEqual(hal_readings["latitude"], 27.5)

        # Verify actuator control propagation
        self.assertEqual(hal.read_actuator("green_led"), "OFF")
        hal.write_actuator("green_led", "ON")
        self.assertEqual(hal.read_actuator("green_led"), "ON")

    def test_6_esp32_device_rtos_cycle(self):
        """Perform end-to-end cycle test on ESP32Device to verify task scheduler execution flow."""
        dev = ESP32Device("AQUA_FRESH_001")
        dev.boot()
        dev.initialize_sensors()
        dev.connect_network()
        
        # Execute one tick-based complete cycle
        telemetry = dev.execute_one_complete_cycle(scenario="NORMAL")
        self.assertIsNotNone(telemetry)
        self.assertEqual(telemetry["device_id"], "AQUA_FRESH_001")
        self.assertEqual(dev.state, "WAITING")
