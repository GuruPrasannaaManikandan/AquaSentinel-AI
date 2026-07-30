# Fault Registry (`FaultRegistry`)

The `FaultRegistry` serves as the bounded database logging active and historical faults.

## Static Allocation Policy

To avoid heap fragmentation and stack leaks under memory-constrained runtime conditions, the registry:
- Declares a static array of size `MAX_FAULT_RECORDS = 20`.
- Implements a circular write pointer to wrap around when logs exceed 20 records.
- Performs no dynamic memory allocations.

## FaultRecord Schema

Each record contains:

- **`faultId`**: Strongly typed integer representing the specific failure code.
- **`subsystem`**: String identifying the failing module (e.g. `SCHEDULER`, `SENSORS`, `MQTT`).
- **`timestamp`**: System uptime (ms) when the fault was logged or cleared.
- **`severity`**: Diagnostic classification index (`INFO`, `WARNING`, `ERROR`, `CRITICAL`).
- **`description`**: Explanatory diagnostic message string.
- **`recoveryStatus`**: Log indicating the recovery stage (e.g. `PENDING`, `RESOLVED`, `ESCALATED`).
- **`active`**: Boolean flag showing if the error is currently active.
