# Version 4.6 — Final Runtime Integration Acceptance Audit Report

**Date**: 2026-08-17  
**Module**: [`src/fusion/decision_adapter.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/fusion/decision_adapter.py)  
**Gateway Module**: [`src/iot/gateway.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/gateway.py)  
**Device Module**: [`src/iot/esp32_device.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/esp32_device.py)  
**Verdict**: **B) ONLY VERIFIED THROUGH AN ISOLATED END-TO-END TEST**

---

## 1. Primary Verdict

> **PRIMARY VERDICT**:  
> **B) ONLY VERIFIED THROUGH AN ISOLATED END-TO-END TEST**
>
> The `DecisionAdapter` module ([`src/fusion/decision_adapter.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/fusion/decision_adapter.py)) is implemented, unit-tested, and verified through an isolated end-to-end integration test ([`tests/test_v4_6_fsm_integration.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/tests/test_v4_6_fsm_integration.py)).  
> However, **"V4.6 adapter exists but is not yet wired into the production gateway runtime."**

---

## 2. Production Call Site Audit

| Search Term | Production File (`src/`) Matches | Test File (`tests/`) Matches |
| :--- | :--- | :--- |
| `DecisionAdapter(` | `0` (Only definition in `src/fusion/decision_adapter.py`) | `1` (`tests/test_v4_6_fsm_integration.py`) |
| `DecisionAdapter.adapt(` | `0` | `1` (`tests/test_v4_6_fsm_integration.py`) |
| `SystemEvent` | `0` (Only dataclass definition in `src/fusion/decision_adapter.py`) | `1` (`tests/test_v4_6_fsm_integration.py`) |

---

## 3. Real Execution Path Trace (Production Gateway & Device)

```
[Production Gateway Execution Path]

Sensor Telemetry / JPEG Payload
             │
             ▼
src/iot/gateway.py :: Gateway.on_message_received()
             │
             ▼
src/fusion/decision_pipeline.py :: DecisionPipeline.run_pipeline()
             │
             ▼
src/fusion/fusion_engine.py :: FusionEngine.fuse()
             │
             ▼
   [Decision Dictionary Payload]
             │
             ▼
src/iot/gateway.py :: Gateway.client.publish("aquatic/<device_id>/decision")
             │
             ▼
    MQTT Broker Transmission
             │
             ▼
src/iot/esp32_device.py :: ESP32Device._on_command_or_decision_received()
             │
             ▼
src/iot/actuators.py :: VirtualActuators.update_state(fusion_state)
             │
             ▼
src/iot/hal.py :: HAL.write_actuator(...)
```

---

## 4. Test vs Production Classification

- **[`tests/test_v4_6_fsm_integration.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/tests/test_v4_6_fsm_integration.py)** $\rightarrow$ **TEST ONLY**. Instantiates `DecisionAdapter` and invokes `.adapt()`.
- **[`src/iot/gateway.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/gateway.py)** $\rightarrow$ **PRODUCTION RUNTIME**. Currently calls `FusionEngine.fuse()` and publishes the raw fused dictionary directly to MQTT without routing through `DecisionAdapter`.

---

## 5. Gateway Runtime Integration Status

- **Inspection Finding**: In `Gateway.on_message_received()`, incoming telemetry is processed by `self.pipeline.run_pipeline(...)`. The resulting decision dictionary is published directly to MQTT topic `aquatic/<device_id>/decision`.
- **Official Status Statement**:  
  *"V4.6 adapter exists but is not yet wired into the production gateway runtime."*

---

## 6. ESP32 Device & FSM Execution Mechanics

- **Inspection Finding**:
  - `ESP32Device` ([`src/iot/esp32_device.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/esp32_device.py)) manages device lifecycle states via `self.state` (`BOOT`, `INITIALIZING`, `CONNECTING`, `ONLINE`, `SENSING`, `PUBLISHING`, `WAITING`, `ERROR`, `RECOVERING`).
  - When an MQTT decision arrives on `aquatic/<device_id>/decision`, `_on_command_or_decision_received()` extracts `fusion_state` (`NORMAL`, `WARNING`, `CRITICAL`, `UNKNOWN_ANOMALY`) and calls `self.actuators.update_state(fusion_state)`.
- **FSM Question Verdict**:
  - `SystemEvent.target_fsm_state` $\rightarrow$ `VirtualActuators.update_state()` is **B) Direct actuator-state invocation**.
  - It updates physical peripheral states (Green/Yellow/Red LEDs, Buzzer, Aerator Pump Relay via `HAL.write_actuator`) based on the fused decision, without altering the device lifecycle state machine (`self.state`).

---

## 7. Summary & Recommendations

1. **V4.6 Module Integrity**: `DecisionAdapter` is fully implemented and passes all 18 unit test scenarios in `tests/test_v4_6_fsm_integration.py`.
2. **Wiring into Production Runtime**: In future integration phases, `Gateway.on_message_received()` in `src/iot/gateway.py` can be updated to invoke `DecisionAdapter.adapt(decision)` prior to MQTT publication, cleanly exposing `SystemEvent` telemetry to the network.
