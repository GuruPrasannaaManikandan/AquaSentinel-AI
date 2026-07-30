# Backend Synchronization Policy (`BackendSyncPolicy`)

The `BackendSyncPolicy` holds all timing intervals, retry limits, and recovery delays. It replaces all hardcoded timeouts and provides the gateway and configuration manager with a unified policy configuration.

## Configured Policies

| Policy Key | Default Value | Description |
| --- | --- | --- |
| **`heartbeatIntervalMs`** | `10000` | Period between heartbeat signals sent to the backend. |
| **`telemetryIntervalMs`** | `5000` | Period between telemetry publications. |
| **`diagnosticsIntervalMs`**| `30000` | Period between diagnostics publications. |
| **`registrationRetryLimit`**| `3` | Maximum registration attempts before transitioning to `FAILED`. |
| **`syncRetryLimit`** | `3` | Retry limit for telemetry synchronization attempts. |
| **`configRetryLimit`** | `3` | Retry limit for requesting configuration updates. |
| **`maxSyncAttempts`** | `5` | Absolute maximum attempts before resetting the connection. |
| **`recoveryDelayMs`** | `5000` | Time delay backoff before attempting network reconnection. |

## Decoupled Control Flow

By encapsulating these values, the `BackendGateway` is decoupled from timing specifics:
- The scheduler loop calls `BackendGateway::update()` at a high frequency.
- The gateway internally evaluates whether the active policy interval has elapsed by checking its local millisecond timer against the policy object getters.
- Reconfiguration is safe because the `ConfigurationManager` simply updates the policy object fields, which immediately takes effect on the next scheduler tick.
