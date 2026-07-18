from src.iot.drivers import (
    VirtualTemperatureSensorDriver,
    VirtualSalinitySensorDriver,
    VirtualPHSensorDriver,
    VirtualTurbiditySensorDriver,
    VirtualDOSensorDriver,
    VirtualGPSSensorDriver,
    VirtualRTCSensorDriver,
    VirtualDistanceToWaterDriver,
    VirtualSampleDepthDriver,
    VirtualLEDDriver,
    VirtualBuzzerDriver,
    VirtualRelayDriver
)

class HAL:
    """
    Hardware Abstraction Layer (HAL).
    Instantiates drivers based on configurations, hides underlying sensor logic/pin details,
    and provides a unified read/write API for firmware application execution.
    """
    def __init__(self, config, env):
        self.config = config
        self.env = env
        self.sensors = {}
        self.actuators = {}
        self._init_drivers()

    def _init_drivers(self):
        gpio = self.config.get_gpio()
        cal = self.config.get_calibration()

        # Instantiate physical-like sensor drivers
        self.sensors["temperature"] = VirtualTemperatureSensorDriver("TEMP_01", gpio.get("temperature"), self.env, cal.get("temperature", {}))
        self.sensors["salinity"] = VirtualSalinitySensorDriver("SAL_01", gpio.get("salinity"), self.env, cal.get("salinity", {}))
        self.sensors["ph"] = VirtualPHSensorDriver("PH_01", gpio.get("ph"), self.env, cal.get("ph", {}))
        self.sensors["turbidity"] = VirtualTurbiditySensorDriver("TURB_01", gpio.get("turbidity"), self.env, cal.get("turbidity", {}))
        self.sensors["dissolved_oxygen"] = VirtualDOSensorDriver("DO_01", gpio.get("dissolved_oxygen"), self.env, cal.get("dissolved_oxygen", {}))
        
        # Spatial and Time sources
        self.sensors["gps"] = VirtualGPSSensorDriver("GPS_01", gpio.get("gps"), self.env)
        self.sensors["rtc"] = VirtualRTCSensorDriver("RTC_01", gpio.get("rtc"), self.env)

        # Supplementary drivers (CAML distance / HABSOS depth)
        self.sensors["distance_to_water"] = VirtualDistanceToWaterDriver("DIST_01", gpio.get("distance_to_water"), self.env)
        self.sensors["sample_depth"] = VirtualSampleDepthDriver("DEPTH_01", gpio.get("sample_depth"), self.env)

        # Instantiate physical-like actuators
        self.actuators["green_led"] = VirtualLEDDriver("LED_GREEN", gpio.get("green_led"))
        self.actuators["yellow_led"] = VirtualLEDDriver("LED_YELLOW", gpio.get("yellow_led"))
        self.actuators["red_led"] = VirtualLEDDriver("LED_RED", gpio.get("red_led"))
        self.actuators["buzzer"] = VirtualBuzzerDriver("BUZZER_01", gpio.get("buzzer"))
        self.actuators["pump_relay"] = VirtualRelayDriver("RELAY_01", gpio.get("pump_relay"))

    def init_hardware(self) -> bool:
        """Initializes all sensors and actuators, returning True if all succeeded."""
        success = True
        for sensor in self.sensors.values():
            if not sensor.init():
                success = False
        return success

    def read_sensor(self, name: str):
        """Reads a specific sensor value by its logical name."""
        if name in self.sensors:
            return self.sensors[name].read()
        return None

    def read_all_sensors(self) -> dict:
        """Reads all sensors and structures their output into a unified telemetry payload format."""
        readings = {}
        for name, driver in self.sensors.items():
            if name == "gps":
                lat, lon = driver.read()
                readings["latitude"] = lat
                readings["longitude"] = lon
            elif name == "rtc":
                ts, prov_ts = driver.read()
                readings["timestamp"] = ts
                readings["provenance_timestamp"] = prov_ts
            elif name == "temperature":
                readings["temperature_c"] = driver.read()
            elif name == "salinity":
                readings["salinity_ppt"] = driver.read()
            elif name == "ph":
                readings["ph"] = driver.read()
            elif name == "turbidity":
                readings["turbidity_ntu"] = driver.read()
            elif name == "dissolved_oxygen":
                readings["dissolved_oxygen_mg_l"] = driver.read()
            elif name == "distance_to_water":
                readings["distance_to_water_m"] = driver.read()
            elif name == "sample_depth":
                readings["sample_depth"] = driver.read()
        return readings

    def write_actuator(self, name: str, state: str) -> bool:
        """Sets the state of a logical actuator ("ON" / "OFF")."""
        if name in self.actuators:
            return self.actuators[name].set_state(state)
        return False

    def read_actuator(self, name: str) -> str:
        """Gets the state of a logical actuator ("ON" / "OFF")."""
        if name in self.actuators:
            return self.actuators[name].get_state()
        return "OFF"
