# Diagnostics Observer Pattern

The `DiagnosticsManager` implements a read-only Observer Pattern to notify other components of health metrics and fault updates.

## Observer Interface

```cpp
class IDiagnosticsObserver {
public:
    virtual ~IDiagnosticsObserver() {}
    virtual void onHealthStatusAggregated(const SubsystemHealth& health) = 0;
    virtual void onFaultStateChanged(int faultId, FaultSeverity severity, bool active, const char* description) = 0;
    virtual void onRecoveryExecuted(int faultId, const char* status) = 0;
};
```

## Observers List

1. **Backend**: Listens for health aggregates to format and publish to `aquatic/<device_id>/diagnostics` and sync active faults to the cloud.
2. **Logger**: Writes logs to the Serial console.
3. **Dashboard**: Renders status grids, load bars, and active fault lists.
4. **Future OTA**: Watches for critical recoveries to safely lock down OTA triggers.

## Read-Only Restrictions

- Observers are registered with `DiagnosticsObserverManager`.
- Observers cannot call `DiagnosticsManager` setters.
- Pointers and structs are passed as `const` references, preventing observers from modifying diagnostics data.
