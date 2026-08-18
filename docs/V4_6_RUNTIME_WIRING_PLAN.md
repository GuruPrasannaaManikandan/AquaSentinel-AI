# Version 4.6 — Runtime Wiring Remediation & Architecture Plan

**Date**: 2026-08-17  
**Module**: [`src/fusion/decision_adapter.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/fusion/decision_adapter.py)  
**Target Extension File**: [`src/fusion/decision_pipeline.py`](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/fusion/decision_pipeline.py)  
**Status**: **PROPOSED DESIGN / REMEDIATION PLAN (NO CODE MODIFIED YET)**

---

## 1. V3.8 Frozen-File Classification

| File Path | V3.8 FROZEN? | WHY | SAFE TO MODIFY? |
| :--- | :--- | :--- | :--- |
| `src/iot/gateway.py` | **NO** | Part of V3.7 Central Gateway routing & persistence; not part of V3.8 release freeze. | **YES** |
| `src/iot/esp32_device.py` | **YES** | Core V3.8 RTOS lifecycle state machine (`BOOT` $\rightarrow$ `WAITING`), scheduler task registration, and HAL integration. | **NO (MUST REMAIN FROZEN)** |
| `src/iot/communication.py` | **YES** | V3.8 Wi-Fi & MQTT network simulation layer. | **NO (MUST REMAIN FROZEN)** |
| `src/iot/scheduler.py` | **YES** | V3.8 FreeRTOS cooperative task scheduler and Queue kernel implementation. | **NO (MUST REMAIN FROZEN)** |
| `src/iot/hal.py` | **YES** | V3.8 Hardware Abstraction Layer for virtual GPIO, ADC, PWM pin maps. | **NO (MUST REMAIN FROZEN)** |
| `src/iot/actuators.py` | **YES** | V3.8 physical/virtual LED indicators, Buzzer alarm, and Aerator Relay driver. | **NO (MUST REMAIN FROZEN)** |
| `src/fusion/decision_pipeline.py` | **NO** | V3.5 decision coordination pipeline linking Supervised ML, Unsupervised AIS, and `FusionEngine`. | **YES (RECOMMENDED EXTENSION POINT)** |
| `src/fusion/fusion_engine.py` | **NO** | V3.5 evidence engine (already extended in V4.5 for multimodal fusion). | **YES** |

---

## 2. FSM & Decision Terminology Clarification

> [!IMPORTANT]
> **FSM Lifecycle States vs Actuator Decision States**:
> - **RTOS Device Lifecycle FSM States (`ESP32Device.state`)**: `BOOT`, `INITIALIZING`, `CONNECTING`, `ONLINE`, `SENSING`, `PUBLISHING`, `WAITING`, `ERROR`, `RECOVERING`.
> - **System Decision / Actuator Decision States**: `NORMAL`, `WARNING`, `CRITICAL`, `UNKNOWN_ANOMALY`, `SENSOR_FAULT`.
>
> The device lifecycle state machine (`self.state`) manages RTOS tasks and network connectivity. The actuator decision mechanism (`VirtualActuators.update_state()`) updates physical LED/Buzzer/Pump pin outputs in response to system decisions. V4.6 adapts decisions into system events without altering device lifecycle states.

---

## 3. Current Test-Only Path vs Proposed Production Runtime Path

### Current Test-Only Path:
```
tests/test_v4_6_fsm_integration.py
      ↓
DecisionAdapter.adapt()
      ↓
SystemEvent
      ↓
VirtualActuators.update_state()
```
*(Production `src/iot/gateway.py` currently executes `DecisionPipeline` $\rightarrow$ `FusionEngine.fuse()`, publishing raw fused dictionaries directly to MQTT without calling `DecisionAdapter`)*.

---

### Proposed Multimodal Production Runtime Path:

```
                  Sensor Telemetry + ESP32-CAM Image
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

## 4. Recommended Runtime Wiring Option

### Selected Option: Option A — Wiring inside `src/fusion/decision_pipeline.py`

- **Implementation Plan**:
  1. Instantiating `DecisionAdapter` inside `DecisionPipeline.__init__()`.
  2. In `DecisionPipeline.run_pipeline(...)`, after executing `FusionEngine.fuse(ml, ais, sensors, visual_evidence)`, calling `self.adapter.adapt(fused_result)`.
  3. Embedding the generated `SystemEvent` into the returned decision dictionary:
     ```json
     {
       "dataset": "caml",
       "fusion": {
         "final_state": "CRITICAL",
         "reason_code": "MULTIMODAL_BLOOM_CONFIRMED",
         "multimodal": true
       },
       "system_event": {
         "event_id": "evt_a1b2c3d4",
         "event_type": "SYSTEM_STATE_CRITICAL",
         "target_fsm_state": "CRITICAL",
         "conflict_detected": false,
         "adapter_time_ms": 0.08
       }
     }
     ```
- **Why Option A is Optimal**:
  - **Minimal Architectural Touch**: Modifies exactly **ONE** non-frozen file (`src/fusion/decision_pipeline.py`).
  - **Universal Production Coverage**: Automatically connects `Gateway`, FastAPI backend endpoints, CLI tools, and background tasks to the `DecisionAdapter` without altering `gateway.py` or any V3.8 frozen files.
  - **100% Backward Compatible**: The `fusion["final_state"]` property remains identical, allowing `ESP32Device` to consume MQTT decision payloads seamlessly.

---

## 5. Protection of Frozen V3.8 Architecture

- **`src/iot/esp32_device.py`**: **UNTOUCHED**. Continues to receive decision payloads via MQTT topic `aquatic/<device_id>/decision` and passes `fusion_state` to `VirtualActuators.update_state()`.
- **`src/iot/actuators.py`**: **UNTOUCHED**. Continues to drive physical/virtual LEDs, buzzer, and pump relay.
- **`src/iot/scheduler.py`**: **UNTOUCHED**. RTOS task queues and tick loop remain pristine.
- **`src/iot/hal.py`**: **UNTOUCHED**. Driver pin maps remain pristine.

---

## 6. Verification Plan Post-Wiring

1. **Focused V4.6 Suite**: `python -m unittest tests/test_v4_6_fsm_integration.py` (Verify 18/18 PASS).
2. **Gateway Live Runtime Test**: Run `Gateway` receiving MQTT telemetry + visual evidence, verifying `SystemEvent` generation in published decision payloads.
3. **All V4 Test Suites**: `python -m unittest discover -s tests -p "test_v4_*.py"` (Verify 51/51 PASS).
4. **Full System Regression**: `python run_phase9.py` (Verify 237/237 PASS).
