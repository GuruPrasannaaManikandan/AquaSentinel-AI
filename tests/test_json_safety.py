import unittest
import numpy as np
import pandas as pd
import math
from fastapi.testclient import TestClient
from src.backend.app import app, sanitize_json_data

class TestJSONSafety(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_sanitize_scalars(self):
        # NaN
        self.assertIsNone(sanitize_json_data(float('nan')))
        self.assertIsNone(sanitize_json_data(np.nan))
        
        # Inf
        self.assertIsNone(sanitize_json_data(float('inf')))
        self.assertIsNone(sanitize_json_data(np.inf))
        
        # -Inf
        self.assertIsNone(sanitize_json_data(float('-inf')))
        self.assertIsNone(sanitize_json_data(-np.inf))

        # NumPy types
        self.assertEqual(sanitize_json_data(np.float32(1.5)), 1.5)
        self.assertEqual(sanitize_json_data(np.int64(42)), 42)

    def test_sanitize_nested(self):
        # Nested structures
        data = {
            "a": np.nan,
            "b": [1.0, float('inf'), {"c": np.float64(2.5)}],
            "d": (3, float('-inf'))
        }
        sanitized = sanitize_json_data(data)
        expected = {
            "a": None,
            "b": [1.0, None, {"c": 2.5}],
            "d": [3, None]
        }
        self.assertEqual(sanitized, expected)

    def test_pandas_handling(self):
        self.assertIsNone(sanitize_json_data(pd.NA))
        
        # Series
        s = pd.Series([1.0, np.nan, 2.0])
        self.assertEqual(sanitize_json_data(s), [1.0, None, 2.0])

    def test_telemetry_endpoint_safety(self):
        r = self.client.get("/devices/AQUA_FRESH_001/telemetry")
        self.assertEqual(r.status_code, 200)
        
        # Ensure no NaN/Infinity/inf strings are in the raw response text
        res_text = r.text
        self.assertNotIn("NaN", res_text)
        self.assertNotIn("Infinity", res_text)
        self.assertNotIn("inf", res_text.lower().split())
        
        # Verify valid values are preserved
        data = r.json()
        if len(data) > 0:
            for item in data:
                self.assertIn("device_id", item)
                self.assertIn("turbidity_ntu", item)
                val = item["turbidity_ntu"]
                self.assertTrue(val is None or isinstance(val, (int, float)))

    def test_valid_finite_values_unchanged(self):
        test_payload = {
            "val1": 12.34,
            "val2": 100,
            "val3": "normal_string"
        }
        self.assertEqual(sanitize_json_data(test_payload), test_payload)

if __name__ == "__main__":
    unittest.main()
