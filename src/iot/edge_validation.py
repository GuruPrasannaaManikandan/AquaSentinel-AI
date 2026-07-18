import numpy as np
import datetime

class EdgeValidator:
    """
    Performs local embedded-side validation on telemetry readings before transmission.
    Checks for NaN/inf values, impossible ranges, missing keys, invalid GPS coordinates, 
    and frozen/repeated values.
    """
    def __init__(self, history_limit=5):
        self.history_limit = history_limit
        # Keeps track of the last few readings for each sensor to check for frozen states
        self.history = {
            "temperature_c": [],
            "salinity_ppt": [],
            "ph": [],
            "turbidity_ntu": [],
            "dissolved_oxygen_mg_l": []
        }

    def validate(self, readings):
        """
        Validates the readings dictionary.
        Returns:
          is_valid (bool): True if reading passes critical safety checks.
          errors (list of str): List of validation error strings.
          health_status (str): "OK", "DEGRADED", or "FAULT".
        """
        errors = []
        health_status = "OK"

        # 1. Check required sensor keys exist
        required_keys = ["latitude", "longitude", "ph", "turbidity_ntu", "dissolved_oxygen_mg_l"]
        for k in required_keys:
            if k not in readings:
                errors.append(f"Missing required sensor field: {k}")
                health_status = "FAULT"
                return False, errors, health_status

        # 2. Check for NaN/Inf/None values
        for k, v in readings.items():
            if k in ["timestamp", "provenance_timestamp"]:
                continue
            if v is None:
                errors.append(f"Sensor value {k} is None/missing.")
                health_status = "FAULT"
                continue
            if not isinstance(v, (int, float)):
                errors.append(f"Sensor value {k} is not numeric (type: {type(v)}).")
                health_status = "FAULT"
                continue
            if not np.isfinite(v):
                errors.append(f"Sensor value {k} is non-finite (NaN or Inf).")
                health_status = "FAULT"

        # 3. Check physical boundaries
        bounds = {
            "temperature_c": (-5.0, 45.0),
            "salinity_ppt": (0.0, 50.0),
            "ph": (0.0, 14.0),
            "turbidity_ntu": (0.0, 500.0),
            "dissolved_oxygen_mg_l": (0.0, 25.0),
            "latitude": (-90.0, 90.0),
            "longitude": (-180.0, 180.0)
        }

        for k, range_lim in bounds.items():
            if k in readings and readings[k] is not None and isinstance(readings[k], (int, float)):
                val = readings[k]
                min_lim, max_lim = range_lim
                if not (min_lim <= val <= max_lim):
                    errors.append(f"Sensor value {k}={val} is outside physical bounds [{min_lim}, {max_lim}].")
                    health_status = "FAULT"

        # 4. Check for frozen/repeated values
        for k in self.history.keys():
            if k in readings and readings[k] is not None and isinstance(readings[k], (int, float)):
                self.history[k].append(readings[k])
                if len(self.history[k]) > self.history_limit:
                    self.history[k].pop(0)

                # If history is full and all values are exactly identical, raise a frozen fault
                if len(self.history[k]) == self.history_limit:
                    if len(set(self.history[k])) == 1:
                        errors.append(f"Sensor frozen fault detected on {k}: repeated value {readings[k]}.")
                        health_status = "FAULT"

        # 5. Check GPS validity
        # If coordinates are exactly 0.0 or out of Florida boundaries when deployed, raise alert
        if "latitude" in readings and "longitude" in readings:
            lat = readings["latitude"]
            lon = readings["longitude"]
            if lat == 0.0 or lon == 0.0:
                errors.append("Invalid GPS lock: coordinates are 0.0, 0.0.")
                health_status = "DEGRADED"

        # 6. Check timestamp validity
        if "timestamp" in readings:
            try:
                dt = datetime.datetime.fromisoformat(readings["timestamp"])
                now = datetime.datetime.now()
                # Check if timestamp is more than 1 hour in the future or past (stale)
                diff = abs((now - dt).total_seconds())
                if diff > 3600.0:
                    errors.append(f"Stale timestamp detected: {readings['timestamp']}")
                    health_status = "DEGRADED"
            except Exception as e:
                errors.append(f"Invalid timestamp format: {e}")
                health_status = "FAULT"

        # Determine validity: if we have any FAULT level errors, invalid
        is_valid = health_status != "FAULT"

        return is_valid, errors, health_status
