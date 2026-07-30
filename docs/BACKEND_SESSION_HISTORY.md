# Backend Session History (`BackendSessionHistory`)

The `BackendSessionHistory` maintains connection records in bounded static memory. It provides visibility into connection stability over time.

## Session Entry Properties

Each session entry is represented by a `SessionHistoryItem`:

- **`timestamp`**: The system millisecond count when the log entry was compiled.
- **`sessionStartMs`**: System uptime (ms) when the connection session began.
- **`sessionEndMs`**: System uptime (ms) when the connection session ended.
- **`syncTimeMs`**: The average round-trip synchronization latency (ms) calculated during this session.
- **`bytesSent`**: Estimated total bytes sent during the session.
- **`bytesReceived`**: Estimated total bytes received.
- **`reconnectCount`**: Reconnect trigger count recorded during the session.
- **`failureReason`**: Description of the disconnect error (e.g., "Network Loss / Recovery Triggered").

## Circular Storage

The history class allocates a static array of size `MAX_BACKEND_SESSIONS = 5`.
When a session starts, we record the start time. When a session disconnects, we format the metrics block and push it into the circular buffer. If the log exceeds 5 entries, the oldest session log is overwritten.
This guarantees that connection diagnostics logs are preserved without leaking memory.
