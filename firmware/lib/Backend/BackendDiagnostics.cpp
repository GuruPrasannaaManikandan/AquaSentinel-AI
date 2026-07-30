#include "BackendDiagnostics.h"
#include <Arduino.h>

BackendDiagnostics::BackendDiagnostics() {
    reset();
}

void BackendDiagnostics::reset() {
    _messagesPublished = 0;
    _messagesReceived = 0;
    _syncSuccess = 0;
    _syncFailure = 0;
    _reconnectCount = 0;
    _totalSyncTimeMs = 0;
    _lastSyncTimestamp = 0;

    _configUpdates = 0;
    _rollbackCount = 0;
    _offlineBufferUsage = 0;
    _droppedTelemetry = 0;
    _sessionDurationMs = 0;
    _sessionStartMs = 0;
}

void BackendDiagnostics::recordPublish() {
    _messagesPublished++;
}

void BackendDiagnostics::recordReceive() {
    _messagesReceived++;
}

void BackendDiagnostics::recordSyncSuccess(unsigned long durationMs) {
    _syncSuccess++;
    _totalSyncTimeMs += durationMs;
    _lastSyncTimestamp = millis();
}

void BackendDiagnostics::recordSyncFailure() {
    _syncFailure++;
}

void BackendDiagnostics::recordReconnect() {
    _reconnectCount++;
}

void BackendDiagnostics::recordConfigUpdate() {
    _configUpdates++;
}

void BackendDiagnostics::recordRollback() {
    _rollbackCount++;
}

void BackendDiagnostics::updateOfflineBufferUsage(unsigned long usage) {
    _offlineBufferUsage = usage;
}

void BackendDiagnostics::recordDroppedTelemetry() {
    _droppedTelemetry++;
}

void BackendDiagnostics::startSession() {
    _sessionStartMs = millis();
}

void BackendDiagnostics::endSession() {
    if (_sessionStartMs > 0) {
        _sessionDurationMs += (millis() - _sessionStartMs);
        _sessionStartMs = 0;
    }
}

unsigned long BackendDiagnostics::getAverageSyncTimeMs() const {
    if (_syncSuccess == 0) return 0;
    return _totalSyncTimeMs / _syncSuccess;
}

float BackendDiagnostics::getSyncSuccessRate() const {
    unsigned long totalAttempts = _syncSuccess + _syncFailure;
    if (totalAttempts == 0) return 0.0f;
    return (static_cast<float>(_syncSuccess) / totalAttempts) * 100.0f;
}

float BackendDiagnostics::getSyncFailureRate() const {
    unsigned long totalAttempts = _syncSuccess + _syncFailure;
    if (totalAttempts == 0) return 0.0f;
    return (static_cast<float>(_syncFailure) / totalAttempts) * 100.0f;
}

unsigned long BackendDiagnostics::getSessionDurationSeconds() const {
    unsigned long totalDuration = _sessionDurationMs;
    if (_sessionStartMs > 0) {
        totalDuration += (millis() - _sessionStartMs);
    }
    return totalDuration / 1000;
}
