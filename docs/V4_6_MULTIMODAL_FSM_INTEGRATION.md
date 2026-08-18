# Version 4.6 — Multimodal Decision → Existing FSM Integration Documentation

**Date**: 2026-08-17  
**Module**: [`src/fusion/decision_adapter.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/fusion/decision_adapter.py)  
**Production Call Site**: [`src/fusion/decision_pipeline.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/fusion/decision_pipeline.py) (Option A Runtime Wiring)  
**Actuator Interface**: [`src/iot/actuators.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/actuators.py)  
**FSM Core**: [`src/iot/esp32_device.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/esp32_device.py)  
**Status**: **RUNTIME-INTEGRATED & FULLY FUNCTIONALLY VERIFIED**

> **Authoritative Architectural Design Statements**:  
> 1. *"The existing V3.6 FSM remains the authoritative state-transition and actuator-decision mechanism."*  
> 2. *"Option A Option: DecisionAdapter is wired directly into `DecisionPipeline.run_pipeline()`, providing a single production call site for Gateway, backend API, CLI, and test runners."*

---

## 1. Architectural Overview & Production Call Chain

Version 4.6 bridges the V4.5 Multimodal Evidence Fusion engine (`FusedEvidence`) directly to the existing V3.6 Event-Driven Finite State Machine (FSM) and Actuator Manager (`VirtualActuators`).

```
                Sensor Telemetry + ESP32-CAM Image Payload
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
         src/fusion/decision_adapter.py :: DecisionAdapter.adapt()
                                  │
                                  ▼
                 Enhanced Multimodal Decision Payload
               (Includes SystemEvent & FusedEvidence)
                                  │
                                  ▼
       MQTT Publication to topic: aquatic/<device_id>/decision
                                  │
                                  ▼
      src/iot/esp32_device.py :: ESP32Device._on_command_or_decision_received()
                                  │
                                  ▼
         src/iot/actuators.py :: VirtualActuators.update_state(fusion_state)
                                  │
                                  ▼
                   src/iot/hal.py :: HAL Pin Output Execution
```

---

## 2. Terminology & State Categorization

- **RTOS Device Lifecycle FSM States (`ESP32Device.state`)**: `BOOT`, `INITIALIZING`, `CONNECTING`, `ONLINE`, `SENSING`, `PUBLISHING`, `WAITING`, `ERROR`, `RECOVERING`.
- **System Decision / Actuator Decision States**: `NORMAL`, `WARNING`, `CRITICAL`, `UNKNOWN_ANOMALY`, `SENSOR_FAULT`.

`DecisionAdapter` maps multimodal fused decisions to abstract system events without altering device lifecycle states or FreeRTOS task loops.

---

## 3. Event Vocabulary & Actuator Mapping

| V4.5 Fused State | Abstract SystemEvent Type | Target Actuator Decision State | Actuator Output (`VirtualActuators`) |
| :--- | :--- | :--- | :--- |
| `NORMAL` | `SYSTEM_STATE_NORMAL` | `NORMAL` | Green LED `ON`, Aerator/Buzzer `OFF` |
| `WARNING` | `SYSTEM_STATE_WARNING` | `WARNING` | Yellow LED `ON`, Pump/Aerator `ON`, Buzzer `OFF` |
| `CRITICAL` | `SYSTEM_STATE_CRITICAL` | `CRITICAL` | Red LED `ON`, Buzzer Sound Alarm `ON`, Pump `ON` |
| `UNKNOWN_ANOMALY` | `SYSTEM_STATE_UNKNOWN_ANOMALY` | `UNKNOWN_ANOMALY` | Yellow & Red LEDs `ON` (OOD alert), Pump/Buzzer `OFF` |
| `SENSOR_FAULT` | `SYSTEM_STATE_SENSOR_FAULT` | `SENSOR_FAULT` | Yellow & Red LEDs `ON`, Buzzer `ON`, Pump `OFF` |

---

## 4. Production Integration Details (Option A)

- **Single Production Call Site**: Modified `src/fusion/decision_pipeline.py`.
- **Additive Payload Structure**:
  ```json
  {
    "dataset": "caml",
    "fusion": {
      "final_state": "CRITICAL",
      "reason_code": "MULTIMODAL_BLOOM_CONFIRMED",
      "multimodal": true
    },
    "system_event": {
      "event_id": "evt_7f8a9b",
      "event_type": "SYSTEM_STATE_CRITICAL",
      "target_fsm_state": "CRITICAL",
      "multimodal": true,
      "sensor_contribution": true,
      "visual_contribution": true,
      "conflict_detected": false,
      "adapter_time_ms": 0.06
    }
  }
  ```
- **100% Backward Compatibility**: All legacy consumers accessing `decision["fusion"]["final_state"]` operate identically.

---

## 5. Verification & Test Results

- **Focused V4.6 Suite ([`tests/test_v4_6_fsm_integration.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/tests/test_v4_6_fsm_integration.py))**: 20/20 **PASSED** (Includes production wiring tests `test_19` and `test_20`).
- **All V4 Unit Test Suites (53 tests)**: 53/53 **PASSED**.
- **Full System Regression Suite (`python run_phase9.py`)**: **239/239 PASSED** (236 passed, 3 skipped, 0 failed).
- **V3.8 Architecture Protection**: **ZERO V3.8 source files modified**.
