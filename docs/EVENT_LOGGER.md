# Event Logger (`EventLogger`)

The `EventLogger` provides a circular log tracking general status changes, warnings, fault registrations, and recoveries.

## Static Circular Storage

- Bounded capacity: `MAX_LOG_ENTRIES = 50`.
- Implements an allocation-free circular queue. Pushing to a full buffer overwrites the oldest log item, preventing dynamic memory allocations during runtime.
- Operates under read-only extraction rules.

## Log Categories

1. **`FAULT`**: Initial registrations of subsystem errors (e.g. sensor timeout).
2. **`RECOVERY`**: Recovery action logs, retry milestones, and resolved confirmations.
3. **`WARNING`**: Threshold alerts and configuration rollbacks.
4. **`CONFIG`**: Versioned configurations successfully applied.
5. **`CONN`**: Network connect and disconnect logs.
6. **`STATE`**: Subsystem initializations and transitions.

## Log Output Format

Example logged outputs:

```text
[EVENT-LOGGER] [STATE] Diagnostics Manager Initialized
[EVENT-LOGGER] [FAULT] [SENSORS] Fault ID 12: Sensor Polling Timeout
[EVENT-LOGGER] [RECOVERY] Escalating recovery for fault 12 to: RETRY_1_OF_3
[EVENT-LOGGER] [RECOVERY] Cleared fault ID 12
```
