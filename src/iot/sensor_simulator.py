import numpy as np
import datetime

class AquaticSensorSimulator:
    """
    Simulates scientifically plausible aquatic sensor readings for freshwater (CAML) 
    and marine (HABSOS) ecosystems under various operational scenarios.
    Uses fixed random seeds for reproducible demonstration.
    """
    def __init__(self, ecosystem_type="Freshwater", random_seed=42):
        self.ecosystem_type = ecosystem_type
        self.rng = np.random.RandomState(random_seed)
        self.step_counter = 0

        # Base coordinate configs
        if ecosystem_type.lower() == "freshwater":
            self.base_lat = 27.5
            self.base_lon = -81.2
        else:
            self.base_lat = 27.5
            self.base_lon = -82.5

    def reset_seed(self, seed):
        self.rng = np.random.RandomState(seed)
        self.step_counter = 0

    def generate_reading(self, scenario="NORMAL", timestamp=None):
        """
        Generates simulated readings dictionary based on the scenario.
        Supported scenarios: 
          NORMAL, KNOWN_BLOOM_RISK, SENSOR_FAULT, 
          UNUSUAL_ENVIRONMENTAL_CONDITION, GRADUAL_ENVIRONMENTAL_DEGRADATION, SUDDEN_EVENT
        """
        self.step_counter += 1
        if timestamp is None:
            # Default to current time or standard summer day
            timestamp = datetime.datetime.now()
        op_timestamp = timestamp

        # Lat/Lon drift slightly
        lat = self.base_lat + self.rng.normal(0, 0.0005)
        lon = self.base_lon + self.rng.normal(0, 0.0005)

        # Baseline physical conditions
        is_fresh = self.ecosystem_type.lower() == "freshwater"

        if scenario == "NORMAL":
            if is_fresh:
                # CAML Row 5 (low risk context: pred = 1, true = 3)
                lat = 35.9086
                lon = -79.1469
                distance_to_water = 270.0
                timestamp = datetime.datetime(2021, 4, 28, 12, 0, 0)
                
                # Normal sensors
                temperature = self.rng.uniform(20.0, 26.0)
                salinity = self.rng.uniform(0.1, 0.3)
                ph = self.rng.uniform(7.2, 7.8)
                turbidity = self.rng.uniform(1.0, 5.0)
                do = self.rng.uniform(7.5, 9.0)
                sample_depth = 0.5
            else: # Marine
                # HABSOS Row 4 (normal context: pred = normal, true = normal)
                lat = 26.6649
                lon = -80.0418
                temperature = 20.4
                salinity = 29.88
                sample_depth = 0.5
                timestamp = datetime.datetime(1993, 1, 20, 12, 0, 0)
                
                # Other normal sensors
                ph = self.rng.uniform(8.1, 8.3)
                turbidity = self.rng.uniform(2.0, 8.0)
                do = self.rng.uniform(6.5, 8.0)
                distance_to_water = 0.0

        elif scenario in ["KNOWN_BLOOM_RISK", "FRESHWATER_CONTEXT_RISK", "MARINE_BLOOM_RISK"]:
            # Bloom-Risk scenarios mapped to actual prediction boundaries
            if is_fresh:
                if scenario in ["KNOWN_BLOOM_RISK", "FRESHWATER_CONTEXT_RISK"]:
                    # CAML Row 2 (high risk context: pred = 4, true = 4)
                    lat = 36.9818
                    lon = -120.2210
                    distance_to_water = 3662.0
                    timestamp = datetime.datetime(2021, 7, 14, 12, 0, 0)
                else:
                    # Normal for freshwater if Marine only
                    lat = 35.9086
                    lon = -79.1469
                    distance_to_water = 270.0
                    timestamp = datetime.datetime(2021, 4, 28, 12, 0, 0)
                
                # Normal sensors (CAML ML ignores sensors)
                temperature = self.rng.uniform(20.0, 26.0)
                salinity = self.rng.uniform(0.1, 0.3)
                ph = self.rng.uniform(7.2, 7.8)
                turbidity = self.rng.uniform(1.0, 5.0)
                do = self.rng.uniform(7.5, 9.0)
                sample_depth = 0.5
            else: # Marine
                if scenario in ["KNOWN_BLOOM_RISK", "MARINE_BLOOM_RISK"]:
                    # HABSOS Row 964 (warning context: pred = warning, true = normal)
                    lat = 24.66587
                    lon = -81.36588
                    temperature = 23.0
                    salinity = 31.9
                    sample_depth = 0.5
                    timestamp = datetime.datetime(2023, 12, 18, 12, 0, 0)
                else:
                    # Normal for Marine if Freshwater only
                    lat = 26.6649
                    lon = -80.0418
                    temperature = 20.4
                    salinity = 29.88
                    sample_depth = 0.5
                    timestamp = datetime.datetime(1993, 1, 20, 12, 0, 0)
                
                # Other sensors
                ph = self.rng.uniform(8.4, 8.9)
                turbidity = self.rng.uniform(15.0, 45.0)
                do = self.rng.uniform(8.0, 11.5)
                distance_to_water = 0.0

        elif scenario == "ENVIRONMENTAL_STRESS":
            if is_fresh:
                # Coordinates/time normal, but sensors at stress values
                lat = 35.9086
                lon = -79.1469
                distance_to_water = 270.0
                timestamp = datetime.datetime(2021, 4, 28, 12, 0, 0)
                
                temperature = 31.0
                salinity = 0.4
                ph = 9.2
                turbidity = 45.0
                do = 13.0
                sample_depth = 0.5
            else:
                # Coordinates/time normal, but sensors at stress values
                lat = 26.6649
                lon = -80.0418
                temperature = 32.0
                salinity = 15.0
                sample_depth = 0.5
                timestamp = datetime.datetime(1993, 1, 20, 12, 0, 0)
                
                ph = 7.4
                turbidity = 50.0
                do = 4.0
                distance_to_water = 0.0

        elif scenario == "UNUSUAL_ENVIRONMENTAL_CONDITION":
            # Kept for backward compatibility in test suites: maps to unusual coordinates
            if is_fresh:
                lat = 37.0
                lon = -122.0
                distance_to_water = 6000.0
                timestamp = datetime.datetime(2021, 7, 14, 12, 0, 0)
                temperature = 18.0
                salinity = 0.2
                ph = 7.5
                turbidity = 3.0
                do = 8.0
                sample_depth = 0.5
            else:
                lat = 25.0
                lon = -80.0
                temperature = 38.0
                salinity = 42.0
                sample_depth = 45.0
                timestamp = datetime.datetime(1993, 1, 20, 12, 0, 0)
                ph = 8.2
                turbidity = 5.0
                do = 7.0
                distance_to_water = 0.0

        elif scenario == "GRADUAL_ENVIRONMENTAL_DEGRADATION":
            drift = min(self.step_counter * 0.05, 3.0)
            if is_fresh:
                lat = 35.9086
                lon = -79.1469
                distance_to_water = 270.0
                timestamp = datetime.datetime(2021, 4, 28, 12, 0, 0)
                temperature = 23.0
                salinity = 0.2
                ph = max(7.5 - drift * 0.4, 5.0)
                turbidity = 3.0 + drift * 5.0
                do = max(8.25 - drift * 1.5, 3.0)
                sample_depth = 0.5
            else:
                lat = 26.6649
                lon = -80.0418
                temperature = 24.0
                salinity = 35.0
                sample_depth = 0.5
                timestamp = datetime.datetime(1993, 1, 20, 12, 0, 0)
                ph = max(8.2 - drift * 0.3, 6.5)
                turbidity = 5.0 + drift * 8.0
                do = max(7.2 - drift * 1.2, 2.5)
                distance_to_water = 0.0

        elif scenario == "SUDDEN_EVENT":
            if is_fresh:
                lat = 35.9086
                lon = -79.1469
                distance_to_water = 270.0
                timestamp = datetime.datetime(2021, 4, 28, 12, 0, 0)
                temperature = 17.0
                salinity = 0.08
                ph = 6.8
                turbidity = 65.0
                do = 6.0
                sample_depth = 0.5
            else:
                lat = 26.6649
                lon = -80.0418
                temperature = 19.0
                salinity = 26.0
                sample_depth = 0.5
                timestamp = datetime.datetime(1993, 1, 20, 12, 0, 0)
                ph = 7.6
                turbidity = 55.0
                do = 5.5
                distance_to_water = 0.0

        elif scenario == "SENSOR_FAULT":
            # Simulates bad sensor states
            fault_type = self.step_counter % 3
            if fault_type == 0:
                # NaN / Out of range
                temperature = np.nan
                salinity = -999.0
                ph = 99.0
                turbidity = np.inf
                do = -5.0
                distance_to_water = -100.0
                sample_depth = -10.0
            elif fault_type == 1:
                # Completely frozen values
                temperature = 22.2
                salinity = 35.0 if not is_fresh else 0.2
                ph = 7.0
                turbidity = 2.0
                do = 8.0
                distance_to_water = 50.0
                sample_depth = 1.0
            else:
                # Missing readings (None)
                temperature = None
                salinity = None
                ph = None
                turbidity = None
                do = None
                distance_to_water = None
                sample_depth = None
        else:
            raise ValueError(f"Unknown scenario: {scenario}")

        # Return structured readings dictionary
        return {
            "timestamp": op_timestamp.isoformat() if isinstance(op_timestamp, datetime.datetime) else op_timestamp,
            "provenance_timestamp": timestamp.isoformat() if isinstance(timestamp, datetime.datetime) else timestamp,
            "latitude": float(lat) if lat is not None else None,
            "longitude": float(lon) if lon is not None else None,
            "temperature_c": float(temperature) if (temperature is not None and np.isfinite(temperature)) else temperature,
            "salinity_ppt": float(salinity) if (salinity is not None and np.isfinite(salinity)) else salinity,
            "ph": float(ph) if (ph is not None and np.isfinite(ph)) else ph,
            "turbidity_ntu": float(turbidity) if (turbidity is not None and np.isfinite(turbidity)) else turbidity,
            "dissolved_oxygen_mg_l": float(do) if (do is not None and np.isfinite(do)) else do,
            "distance_to_water_m": float(distance_to_water) if (distance_to_water is not None and np.isfinite(distance_to_water)) else distance_to_water,
            "sample_depth": float(sample_depth) if (sample_depth is not None and np.isfinite(sample_depth)) else sample_depth
        }
