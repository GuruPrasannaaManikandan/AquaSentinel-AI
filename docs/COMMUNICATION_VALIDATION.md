# Communication Validation

This document describes how the communication verification suite validates network loss, recovery, and offline data buffering.

## Wi-Fi Disconnection & Reconnection Scenario

- **Disconnection Trigger**: The test runner sets `mockWiFi.setStatus(WiFiState::DISCONNECTED)` and updates the gateway with `setWiFiConnected(false)`.
- **FSM and Gateway Verification**: The test suite checks if FSM and backend gateway transition to `RECOVERING`.
- **Offline Telemetry Buffering**: Telemetry data published while disconnected is verified to queue inside the `OfflineTelemetryBuffer`.
- **Reconnection Recovery**: The runner restores state to `WiFiState::CONNECTED` and triggers reconnects.
- **Flushing Queue**: The suite verifies that cached telemetry data is flushed to MQTT and the offline buffer count returns to zero.

## MQTT Disconnection & Recovery Scenario

- **Disconnection**: The runner calls `mockMQTT.disconnect()`.
- **FSM and Gateway Verification**: Checks if the gateway transitions to `RECOVERING`.
- **Reconnection**: The runner connects the mock MQTT client back and verifies normal operations.
