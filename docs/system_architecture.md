# System Architecture and Diagrams

This document details the architectural design and software execution flows of the integrated capstone system using Mermaid diagrams.

---

## 1. Complete System Architecture
```mermaid
graph TD
    subgraph EdgeDevice["Simulated ESP32 Edge Device"]
        A["Virtual Sensors"] -->|Polled readings| B["Edge Validation FSM"]
        B -->|If Valid| C["MQTT client Node"]
        B -->|If Fault| D["Yellow Status LED"]
    end
    
    subgraph TransportBroker["In-Memory MQTT Transport"]
        C -->|Publish /telemetry| E["Broker Queue"]
    end
    
    subgraph GatewayInference["IoT Gateway Decision Loop"]
        E -->|Subscribe /telemetry| F["Gateway Coordinator"]
        F -->|Validate & Preprocess| G["ML & AIS Parallel Inference"]
        G -->|Predictions \& anomaly score| H["Evidence Fusion Engine"]
        H -->|Fused decisions state| I["Override alert Dispatcher"]
        I -->|Publish /decision| J["Broker Queue"]
    end

    subgraph ClientDashboard["Backend & Visualization Dashboard"]
        J -->|WS raw payload| K["FastAPI server (app.py)"]
        K -->|Live streams| L["Streamlit Dashboard"]
        K -->|SQLite Log| M[("aquatic_events.db")]
    end

    J -->|Subscribe /decision| N["Actuators Handler"]
    N -->|Update indicators| O["Physical LEDs / Pump Relays"]
```

---

## 2. ML/AIS Parallel Architecture
```mermaid
graph LR
    A["Raw Telemetry Input"] --> B["Ingestion Block"]
    B --> C["Supervised ML Pipeline"]
    B --> D["Negative Selection Algorithm (NSA)"]
    
    subgraph MLPipeline["Supervised Classifiers"]
        C --> C1["Scale / Cyclic Features"]
        C1 --> C2["RF / LR Classifiers"]
        C2 --> C3["Bloom Class Probability"]
    end

    subgraph AISPipeline["Anomaly Filtration Layer"]
        D --> D1["Scale to Training SELF"]
        D1 --> D2["Detector Affinity scan"]
        D2 --> D3["Unsupervised Anomaly Flag"]
    end

    C3 --> E["Evidence Fusion Engine"]
    D3 --> E
```

---

## 3. ESP32 Finite State Machine
```mermaid
stateDiagram-v2
    [*] --> BOOT
    BOOT --> INITIALIZING : System power-up
    INITIALIZING --> CONNECTING : Sensors active
    CONNECTING --> ONLINE : Wifi / Broker OK
    CONNECTING --> ERROR : Timeout / Lost radio
    ONLINE --> SENSING : Interval trigger
    SENSING --> PUBLISHING : Validator returns VALID
    SENSING --> ERROR : Validator returns FAULT
    PUBLISHING --> WAITING : MQTT publish success
    WAITING --> SENSING : Poll timer tick
    ERROR --> RECOVERING : Restart trigger
    RECOVERING --> CONNECTING : Hardware reset
```

---

## 4. MQTT Communication Flow
```mermaid
sequenceDiagram
    participant Device as ESP32 Device
    participant Broker as MQTT Broker
    participant Gateway as IoT Gateway
    
    Device->>Broker: Connect Heartbeat
    Gateway->>Broker: Subscribe "aquatic/+/telemetry"
    Device->>Broker: Publish "aquatic/device_id/telemetry" (payload)
    Broker->>Gateway: Forward telemetry (payload)
    Gateway->>Broker: Publish "aquatic/device_id/decision" (decision details)
    Broker->>Device: Forward decision (LED/pump triggers)
```

---

## 5. Gateway Inference Flow
```mermaid
graph TD
    A["Receive Telemetry Message"] --> B{"Is ID Authorized?"}
    B -- No --> C["Log Error / Drop Message"]
    B -- Yes --> D{"Is sensor_status = 'FAULT'?"}
    D -- Yes --> E["Bypass Inference; Trigger SENSOR_FAULT state"]
    D -- No --> F["Convert Timestamps to Cyclic features"]
    F --> G["Execute Supervised ML classifier"]
    F --> H["Execute AIS NSA anomaly scan"]
    G --> I["Combine Evidence in Fusion Engine"]
    H --> I
    I --> J["Write Logs to SQLite Event Store"]
    J --> K["Publish Decision Frame to MQTT Bus"]
```

---

## 6. Fusion Decision Flow
```mermaid
graph TD
    A["Supervised ML class & confidence"] --> B["Evidence Fusion Check"]
    C["AIS NSA anomaly flag"] --> B
    
    B --> D{"Is ML confidence HIGH?"}
    D -- Yes --> E{"Is Class = Normal?"}
    E -- Yes --> F["Emit NORMAL state"]
    E -- No --> G["Emit CRITICAL warning state"]
    
    D -- No --> H{"Is AIS Anomaly Flagged?"}
    H -- Yes --> I["Emit UNKNOWN_ANOMALY state"]
    H -- No --> J["Emit WARNING state"]
```

---

## 7. Backend and Dashboard Flow
```mermaid
graph LR
    subgraph BackendAPI["FastAPI backend"]
        A["Services layer"] -->|GET queries| B["SQLite Event Store"]
        A -->|Intercepts telemetry| C["WebSocket Manager"]
    end
    
    subgraph Frontend["Streamlit App"]
        D["UI charts & gauges"] -->|Poll HTTP| A
        E["Real-time telemetry stream"] -->|WebSocket Connection| C
    end
```

---

## 8. Database Persistence Flow
```mermaid
graph TD
    A["Gateway Ingestion"] --> B[("aquatic_events.db")]
    
    B --> C["telemetry_logs table"]
    B --> D["validation_logs table"]
    B --> E["fusion_decisions table"]
    B --> F["actuator_logs table"]
    B --> G["command_logs table"]
    B --> H["alerts table"]
```
