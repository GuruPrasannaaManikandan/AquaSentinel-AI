import datetime
from src.iot.drivers.base_driver import BaseSensorDriver

class VirtualEnvironment:
    """
    Simulates the physical medium (water body) in which the IoT device resides.
    Used to coordinate correlated readings across multiple virtual drivers.
    """
    def __init__(self, simulator=None):
        self.simulator = simulator
        self.current_readings = {}
        self.scenario = "NORMAL"
        self.timestamp = None

    def update_environment(self, readings: dict, scenario: str = "NORMAL", timestamp=None):
        """Updates the current physical state of the environment."""
        self.current_readings = readings
        self.scenario = scenario
        self.timestamp = timestamp

    def get_reading(self, field_name: str):
        """Retrieves a reading from the environmental state."""
        return self.current_readings.get(field_name)


class VirtualTemperatureSensorDriver(BaseSensorDriver):
    def __init__(self, name: str, pin: int = None, env: VirtualEnvironment = None, config: dict = None):
        super().__init__(name, pin, config)
        self.env = env

    def read(self) -> float:
        if self.status == "FAULT":
            return None
        val = self.env.get_reading("temperature_c") if self.env else 20.0
        if val is None:
            return None
        # Apply calibration
        offset = self.config.get("offset", 0.0)
        scale = self.config.get("scale", 1.0)
        return float(val * scale + offset)


class VirtualSalinitySensorDriver(BaseSensorDriver):
    def __init__(self, name: str, pin: int = None, env: VirtualEnvironment = None, config: dict = None):
        super().__init__(name, pin, config)
        self.env = env

    def read(self) -> float:
        if self.status == "FAULT":
            return None
        val = self.env.get_reading("salinity_ppt") if self.env else 0.2
        if val is None:
            return None
        # Apply calibration
        offset = self.config.get("offset", 0.0)
        scale = self.config.get("scale", 1.0)
        return float(val * scale + offset)


class VirtualPHSensorDriver(BaseSensorDriver):
    def __init__(self, name: str, pin: int = None, env: VirtualEnvironment = None, config: dict = None):
        super().__init__(name, pin, config)
        self.env = env

    def read(self) -> float:
        if self.status == "FAULT":
            return None
        val = self.env.get_reading("ph") if self.env else 7.0
        if val is None:
            return None
        # Apply calibration
        offset = self.config.get("offset", 0.0)
        scale = self.config.get("scale", 1.0)
        return float(val * scale + offset)


class VirtualTurbiditySensorDriver(BaseSensorDriver):
    def __init__(self, name: str, pin: int = None, env: VirtualEnvironment = None, config: dict = None):
        super().__init__(name, pin, config)
        self.env = env

    def read(self) -> float:
        if self.status == "FAULT":
            return None
        val = self.env.get_reading("turbidity_ntu") if self.env else 1.0
        if val is None:
            return None
        # Apply calibration
        offset = self.config.get("offset", 0.0)
        scale = self.config.get("scale", 1.0)
        return float(val * scale + offset)


class VirtualDOSensorDriver(BaseSensorDriver):
    def __init__(self, name: str, pin: int = None, env: VirtualEnvironment = None, config: dict = None):
        super().__init__(name, pin, config)
        self.env = env

    def read(self) -> float:
        if self.status == "FAULT":
            return None
        val = self.env.get_reading("dissolved_oxygen_mg_l") if self.env else 8.0
        if val is None:
            return None
        # Apply calibration
        offset = self.config.get("offset", 0.0)
        scale = self.config.get("scale", 1.0)
        return float(val * scale + offset)


class VirtualGPSSensorDriver(BaseSensorDriver):
    def __init__(self, name: str, pin: int = None, env: VirtualEnvironment = None, config: dict = None):
        super().__init__(name, pin, config)
        self.env = env

    def read(self) -> tuple:
        """Returns GPS coordinates as a tuple (latitude, longitude)."""
        if self.status == "FAULT":
            return None, None
        if not self.env:
            return 27.5, -81.2
        lat = self.env.get_reading("latitude")
        lon = self.env.get_reading("longitude")
        return (lat, lon)


class VirtualRTCSensorDriver(BaseSensorDriver):
    def __init__(self, name: str, pin: int = None, env: VirtualEnvironment = None, config: dict = None):
        super().__init__(name, pin, config)
        self.env = env

    def read(self) -> tuple:
        """Returns time coordinates as a tuple (timestamp, provenance_timestamp)."""
        if self.status == "FAULT":
            return None, None
        if not self.env:
            now = datetime.datetime.now().isoformat()
            return now, now
        ts = self.env.get_reading("timestamp")
        prov_ts = self.env.get_reading("provenance_timestamp")
        return (ts, prov_ts)


class VirtualDistanceToWaterDriver(BaseSensorDriver):
    def __init__(self, name: str, pin: int = None, env: VirtualEnvironment = None, config: dict = None):
        super().__init__(name, pin, config)
        self.env = env

    def read(self) -> float:
        if self.status == "FAULT":
            return None
        val = self.env.get_reading("distance_to_water_m")
        if val is None:
            return None
        return float(val)


class VirtualSampleDepthDriver(BaseSensorDriver):
    def __init__(self, name: str, pin: int = None, env: VirtualEnvironment = None, config: dict = None):
        super().__init__(name, pin, config)
        self.env = env

    def read(self) -> float:
        if self.status == "FAULT":
            return None
        val = self.env.get_reading("sample_depth")
        if val is None:
            return None
        return float(val)
