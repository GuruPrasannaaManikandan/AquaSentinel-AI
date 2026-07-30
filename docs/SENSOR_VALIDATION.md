# Sensor Validation

This document describes the validation of telemetry sensor data at the edge.

## Edge Validation Rules

Before telemetry data is serialized, the edge validator applies validation rules:

1. **Numerical Checks**:
   Rejects sensor readings containing `NaN` or `Inf` values.
2. **Range Boundaries**:
   - **Temperature**: Must fall between -10°C and 60°C.
   - **pH**: Must fall between 0.0 and 14.0.
   - **Salinity**: Must fall between 0.0 ppt and 50.0 ppt.
   - **Turbidity**: Must fall between 0.0 NTU and 3,000.0 NTU.
   - **Dissolved Oxygen**: Must fall between 0.0 mg/L and 20.0 mg/L.
3. **Frozen Value Check**:
   Rejects sensor readings that do not change over 5 consecutive cycles.
4. **Calibration Calibration offsets**:
   Verifies that sensor calculations apply calibration offsets configured in memory.
5. **Sensor Timeout**:
   If sensor polls take longer than **15 seconds** without updating, a sensor timeout warning is triggered.
