import os
import json

class DeviceConfig:
    """
    Manages loading and querying configurations for a specific virtual device.
    Provides a default configuration fallback to ensure dynamic test devices (e.g., test suites) function.
    """
    def __init__(self, device_id: str, workspace_dir: str = None):
        self.device_id = device_id
        if workspace_dir is None:
            # Fallback path traversal
            workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_path = os.path.join(workspace_dir, "config", "device_config.json")
        self.data = self._load_config()

    def _load_config(self) -> dict:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    all_configs = json.load(f)
                    return all_configs.get("devices", {}).get(self.device_id, self._get_default_config())
            except Exception:
                pass
        return self._get_default_config()

    def _get_default_config(self) -> dict:
        """Returns a generic configuration if the device is not registered in the JSON file."""
        return {
            "device_id": self.device_id,
            "ecosystem_type": "Freshwater",
            "dataset_route": "caml",
            "wifi": {
                "ssid": "AquaNet_Default",
                "password": "default_password"
            },
            "mqtt": {
                "host": "localhost",
                "port": 1883,
                "topics": {
                    "telemetry": f"aquatic/{self.device_id}/telemetry",
                    "status": f"aquatic/{self.device_id}/status",
                    "command": f"aquatic/{self.device_id}/command",
                    "decision": f"aquatic/{self.device_id}/decision"
                }
            },
            "gpio": {
                "ph": 32,
                "turbidity": 33,
                "dissolved_oxygen": 34,
                "gps": 21,
                "rtc": 22,
                "green_led": 12,
                "yellow_led": 13,
                "red_led": 14,
                "buzzer": 15,
                "pump_relay": 16
            },
            "calibration": {},
            "thresholds": {},
            "physical_bounds": {
                "ph": {"min": 0.0, "max": 14.0},
                "turbidity_ntu": {"min": 0.0, "max": 500.0},
                "dissolved_oxygen_mg_l": {"min": 0.0, "max": 25.0},
                "temperature_c": {"min": -5.0, "max": 45.0},
                "salinity_ppt": {"min": 0.0, "max": 50.0},
                "latitude": {"min": -90.0, "max": 90.0},
                "longitude": {"min": -180.0, "max": 180.0}
            },
            "sampling_interval_seconds": 10
        }

    def get_wifi(self) -> dict:
        return self.data.get("wifi", {})

    def get_mqtt(self) -> dict:
        return self.data.get("mqtt", {})

    def get_gpio(self) -> dict:
        return self.data.get("gpio", {})

    def get_calibration(self) -> dict:
        return self.data.get("calibration", {})

    def get_thresholds(self) -> dict:
        return self.data.get("thresholds", {})

    def get_physical_bounds(self) -> dict:
        return self.data.get("physical_bounds", {})

    def get_sampling_interval(self) -> int:
        return self.data.get("sampling_interval_seconds", 10)
