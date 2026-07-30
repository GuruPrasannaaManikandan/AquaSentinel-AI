# Final Firmware Architecture

This document presents the complete architectural diagram and layer classifications of the AquaSentinel-AI firmware.

## Architecture Layer Map

```
  +───────────────────────────────────────────────────────────────+
  |              Applications & Tasks Loop (main.cpp)             |
  +───────────────────────────────┬───────────────────────────────+
                                  │
  +───────────────────────────────▼───────────────────────────────+
  |                   Centralized Control Core                    |
  |                                                               |
  |  +───────────────────────────+   +──────────────────────────+ |
  |  |    Cooperative Scheduler  |   |   Finite State Machine   | |
  |  |         (FROZEN)          |   |        (FROZEN)          | |
  |  +───────────────────────────+   +──────────────────────────+ |
  |  +───────────────────────────+   +──────────────────────────+ |
  |  |     Event Dispatcher      |   |       Event Queue        | |
  |  |         (FROZEN)          |   |        (FROZEN)          | |
  |  +───────────────────────────+   +──────────────────────────+ |
  +───────────────────────────────┬───────────────────────────────+
                                  │
  +───────────────────────────────▼───────────────────────────────+
  |                   Communications & Services                   |
  |                                                               |
  |  +───────────────────────────+   +──────────────────────────+ |
  |  |       WiFi Manager        |   |       MQTT Manager       | |
  |  |         (FROZEN)          |   |        (FROZEN)          | |
  |  +───────────────────────────+   +──────────────────────────+ |
  |  +───────────────────────────+   +──────────────────────────+ |
  |  |    Backend Gateway (v3.9) |   |    Diagnostics (v3.10)   | |
  |  |         (FROZEN)          |   |        (FROZEN)          | |
  |  +───────────────────────────+   +──────────────────────────+ |
  |  +───────────────────────────+                                |
  |  |    Verification (v3.11)   |                                |
  |  |         (FROZEN)          |                                |
  |  +───────────────────────────+                                |
  +───────────────────────────────┬───────────────────────────────+
                                  │
  +───────────────────────────────▼───────────────────────────────+
  |                  Hardware Abstraction (HAL)                   |
  |                                                               |
  |  +───────────────────────────+   +──────────────────────────+ |
  |  |  HAL Interfaces (FROZEN)  |   |  Mock Drivers (FROZEN)   | |
  |  +───────────────────────────+   +──────────────────────────+ |
  +───────────────────────────────────────────────────────────────+
```

## Subsystem Freeze Registry

Every subsystem in the AquaSentinel-AI firmware is officially **FROZEN**:

- **Cooperative Scheduler**: [FROZEN] Matches tasks scheduling limits.
- **FSM State Engine**: [FROZEN] Evaluates edge state validations.
- **Event Dispatcher**: [FROZEN] Decoupled async event router.
- **Wi-Fi Manager**: [FROZEN] Link layer wrapper.
- **MQTT Manager**: [FROZEN] Message layer broker.
- **Backend Gateway**: [FROZEN] Session shadow, configuration rollback, and offline circular queues.
- **Diagnostics Manager**: [FROZEN] Active fault lists, software watchdogs, and recovery escalations.
- **Verification Manager**: [FROZEN] Bootup self-test and automated test execution wrapper.
- **Hardware Abstraction Layer**: [FROZEN] Interfaces isolating physical ADC/GPIO outputs.
