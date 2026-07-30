# Hardware Self-Test

The `HardwareSelfTest` validates virtual hardware structures, driver configurations, and memory resources on bootup.

## Executed Self-Tests

1. **HAL Interface Check**: Verifies that the global `HAL` pointer is initialized.
2. **Sensor ADC Verification**: Performs sample reads across sensors and verifies that returned values are numeric (not NaN or Inf) and fit normal bounds (e.g. Temperature between -10C and 60C, pH between 0 and 14).
3. **GPIO Indicators Check**: Checks mock writes to LED and buzzer outputs.
4. **Memory Heap Verification**: Queries `ESP.getFreeHeap()`. The self-test fails if free memory falls below **20 KB**, indicating a leak or heap overrun.
5. **Scheduler Check**: Confirms task lists are loaded.
6. **FSM Check**: Confirms FSM registers are allocated.
