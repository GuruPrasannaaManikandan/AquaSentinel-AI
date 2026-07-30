# Backend Pipeline & Flow Mapping

This document maps the data flow from raw edge sensor acquisition to cloud AI model decision and actuator override routing.

## Complete Data Flow Map

```
[ ESP32 Node ]
      │
      ▼ (sensorPollingTask)
  Read HAL Sensors (temperature, pH, DO, turbidity, salinity)
      │
      ▼
  Validate readings at edge (NAN/INF/freeze guards)
      │
      ▼
  Format JSON Telemetry Payload (adds RSSI, Battery, Sequence No., ISO Timestamp)
      │
      ├───────────────────────(If Connection Lost)───────────────────────┐
      │                                                                  v
      ▼ (If Connected)                                      [ Offline circular queue ]
  Publish to aquatic/+/telemetry                                         │
      │                                                                  v
      ▼ (MQTT Broker)                                         Flushes on Reconnect
  Central MQTT Broker
      │
      ▼ (Subscribe)
  Gateway Service (gateway.py)
      │
      ├───────────────────────(If Sensor Fault)──────────────────────────┐
      │                                                                  v
      ▼ (If Sensor Valid)                                      State: SENSOR_FAULT
  Run Preprocessing Pipeline (Imputers & Scalers)                       │
  Convert Temporal Cyclic features (Season, Day of Year, Month)          │
  Resolve Geography (US Census regions & State IDs)                      │
      │                                                                  │
      ├───────────(Route: caml)───────────┐                              │
      │                                   │                              │
      ▼                                   ▼                              │
  CAML Classifier (Freshwater)     HABSOS Classifier (Marine)            │
  - Random Forest                  - Logistic Regression                 │
  - Target classes: 1 to 5         - Target classes: 1 to 4              │
      │                                   │                              │
      └─────────────────┬─────────────────┘                              │
                        │                                                │
                        v                                                │
  Evidence Fusion Engine (decision_pipeline.py) <────────────────────────┘
  - Fuse ML prediction + confidence + AIS anomaly status
  - Resolve final state (NORMAL, WARNING, CRITICAL, UNKNOWN_ANOMALY)
      │
      ├────────────────────────(If state CRITICAL)───────────────────────┐
      │                                                                  │
      v                                                                  v
  Log Decision Event in SQLite DB                                 Publish command: ACTIVATE_BUZZER
  Publish to aquatic/+/decision                                          │
      │                                                                  v
      v                                                            Receive command at ESP32
  Stream via WS / REST app                                        Buzzer activated at edge
  Update Streamlit Dashboard
```

## AI Preprocessing Details

- **Temporal features cyclic mapping**:
  $$\text{Month}_{\sin} = \sin\left(\frac{2\pi \cdot \text{Month}}{12}\right), \quad \text{Month}_{\cos} = \cos\left(\frac{2\pi \cdot \text{Month}}{12}\right)$$
  $$\text{Day}_{\sin} = \sin\left(\frac{2\pi \cdot \text{DayOfYear}}{365.25}\right), \quad \text{Day}_{\cos} = \cos\left(\frac{2\pi \cdot \text{DayOfYear}}{365.25}\right)$$
- **Geographic mapping**:
  - `longitude <= -114.0` $\rightarrow$ `west`
  - `longitude >= -80.0` and `latitude >= 38.0` $\rightarrow$ `northeast`
  - `-105.0 <= longitude < -80.0` and `latitude >= 36.5` $\rightarrow$ `midwest`
  - Other coordinates $\rightarrow$ `south`
  - `longitude <= -93.5` $\rightarrow$ `STATE_ID: TX`, else `FL` (HABSOS).
