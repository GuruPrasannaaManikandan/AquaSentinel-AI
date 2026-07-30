# Release Notes (Version 3.0.0)

AquaSentinel-AI Firmware Version 3.0.0 is officially released. This production package connects the cooperative scheduler and FSM edge validations to the FastAPI cloud backend and Streamlit dashboard using an isolated MQTT synchronization gateway, incorporating fault diagnostics and bootup validation testing.

## Major Release Milestones

1. **Version 3.9 - Backend Integration Layer**:
   - Integrated `BackendGateway` supporting capability profiles registration and JSON telemetry serialization.
   - Decoupled commands parsing (START, STOP, RESET, PING, OTA) from FSM execution.
   - Refined with dynamic config validation, safety rollback to defaults, and allocation-free offline telemetry buffering.
2. **Version 3.10 - Control Diagnostics & Faults**:
   - Centralized `DiagnosticsManager` tracking active faults across severities (INFO, WARNING, ERROR, CRITICAL) in static registries.
   - Software watchdog tracking task overruns (>100ms), high utilization (>95%), and sensor/network timeouts.
   - recovery manager executing escalations (Retry -> Restart -> Shutdown) via the decoupled EventDispatcher.
3. **Version 3.11 - System Verification**:
   - Automated `VerificationManager` running hardware self-tests and integration scenarios (connection loss, recovery, buffering) on boot.

## Structural Improvements

- **Hardware Isolation**: The gateway layer is isolated from physical HAL and Wi-Fi drivers, receiving connection status updates passively.
- **Memory Protection**: Eliminated heap allocation risks by utilizing static circular buffers for offline telemetry caching and diagnostics event logging.

## Known Parameters and Limitations

- **Simulated Hardware**: HAL interfaces and network services use mock drivers on C++ setups. Physical sensor integrations require DS18B20 OneWire and ADC mapping adjustments.
- **HABSOS AIS Recall**: Marine dinoflagellate anomaly classifications are mathematically constrained by feature overlaps.
