# Final Demo Results Report

This report presents trace logs and verified outputs for the six capstone demonstration scenarios under locked production configurations.

## 1. Demo Scenario Outcomes

### Scenario 1: Freshwater Normal Condition
*   **Input Readings:** Temp: 24.0°C | Salinity: 0.20 ppt | pH: 7.20 | Turbidity: 3.50 NTU | DO: 8.00 mg/L.
*   **Gateway Routing:** `GATEWAY_INFERENCE`.
*   **ML Output:** predicted class `1` (Normal) | Confidence: 94.2% | Band: `HIGH`.
*   **AIS Output:** `SELF` | Anomaly Score: 0.0000 | Match Count: 0.
*   **Fusion Output:** State: `NORMAL` | Reason: `ML_NORMAL_AIS_NORMAL` | Confidence: `HIGH`.
*   **Actuators:** Green LED: `ON` | Yellow LED: `OFF` | Red LED: `OFF` | Buzzer: `OFF` | Pump: `OFF`.

### Scenario 2: Freshwater Bloom-Risk Condition
*   **Input Readings:** Temp: 28.2°C | Salinity: 0.35 ppt | pH: 9.20 | Turbidity: 42.10 NTU | DO: 11.20 mg/L.
*   **Gateway Routing:** `GATEWAY_INFERENCE`.
*   **ML Output:** predicted class `4` (Bloom Risk) | Confidence: 91.5% | Band: `HIGH`.
*   **AIS Output:** `SELF` | Anomaly Score: 0.0000 | Match Count: 0.
*   **Fusion Output:** State: `CRITICAL` | Reason: `ML_BLOOM_RISK_CONFIRMED`.
*   **Actuators:** Green LED: `OFF` | Yellow LED: `OFF` | Red LED: `ON` | Buzzer: `ON` | Pump: `ON`.

### Scenario 3: Marine Normal Condition
*   **Input Readings:** Temp: 21.5°C | Salinity: 34.20 ppt | pH: 8.10 | Turbidity: 1.00 NTU | DO: 6.00 mg/L.
*   **Gateway Routing:** `GATEWAY_INFERENCE`.
*   **ML Output:** predicted class `1` (Normal) | Confidence: 95.8% | Band: `HIGH`.
*   **AIS Output:** `SELF`.
*   **Fusion Output:** State: `NORMAL` | Reason: `ML_NORMAL_AIS_NORMAL`.
*   **Actuators:** Green LED: `ON` | Yellow LED: `OFF` | Red LED: `OFF`.

### Scenario 4: Marine Bloom-Risk Condition
*   **Input Readings:** Temp: 26.8°C | Salinity: 35.50 ppt | pH: 8.80 | Turbidity: 27.50 NTU | DO: 9.50 mg/L.
*   **Gateway Routing:** `GATEWAY_INFERENCE`.
*   **ML Output:** predicted class `3` (Bloom Risk) | Confidence: 89.2% | Band: `HIGH`.
*   **AIS Output:** `SELF`.
*   **Fusion Output:** State: `CRITICAL` | Reason: `ML_BLOOM_RISK_CONFIRMED`.
*   **Actuators:** Green LED: `OFF` | Yellow LED: `OFF` | Red LED: `ON` | Buzzer: `ON` | Pump: `ON`.

### Scenario 5: Ecosystem Sensor Fault
*   **Input Readings:** Temp: `NaN` | Salinity: 0.20 ppt | pH: 7.20 | Turbidity: 3.50 NTU | DO: 8.00 mg/L.
*   **Gateway Routing:** `EDGE_REJECTION`.
*   **ML/AIS Output:** `BYPASSED` (Inference blocked due to edge validator error trigger).
*   **Fusion Output:** State: `SENSOR_FAULT` | Reason: `SENSOR_FAULT_BYPASS` | Confidence: `LOW`.
*   **Actuators:** Green LED: `OFF` | Yellow LED: `ON` | Red LED: `OFF` | Buzzer: `OFF` | Pump: `OFF`.

### Scenario 6: Network Disconnect & Recovery
*   **Input Readings:** Temp: 24.0°C | Salinity: 0.20 ppt | pH: 7.20 | Turbidity: 3.50 NTU | DO: 8.00 mg/L.
*   **Network State:** `DISCONNECTED` (WiFi/MQTT dropped).
*   **Device State:** Transits to `ERROR` $\rightarrow$ attempts reconnection. Local validation remains active. Actuators go to fallback safe states (`OFF`).
*   **Network Recovery State:** WiFi reconnects $\rightarrow$ transits to `ONLINE` $\rightarrow$ normal operations resume.
