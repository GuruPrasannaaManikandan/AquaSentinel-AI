#include "WiFiRetryManager.h"
#include <Arduino.h>

WiFiRetryManager::WiFiRetryManager(int maxRetries, unsigned long baseIntervalMs, unsigned long maxIntervalMs)
    : _retryCount(0), _maxRetries(maxRetries), _baseIntervalMs(baseIntervalMs), _maxIntervalMs(maxIntervalMs), _lastRetryTime(0) {}

void WiFiRetryManager::incrementRetry() {
    _retryCount++;
    _lastRetryTime = millis();
}

void WiFiRetryManager::reset() {
    _retryCount = 0;
    _lastRetryTime = 0;
}

unsigned long WiFiRetryManager::getNextDelay() const {
    if (_retryCount == 0) return _baseIntervalMs;
    
    // Shift base interval exponentially: base * 2^(retryCount-1)
    // Prevent shift overflows if retries are large
    int shifts = (_retryCount > 10) ? 10 : _retryCount;
    unsigned long delay = _baseIntervalMs * (1 << (shifts - 1));
    
    return (delay > _maxIntervalMs) ? _maxIntervalMs : delay;
}

bool WiFiRetryManager::shouldRetry(unsigned long currentTime) {
    if (isExhausted()) return false;
    
    unsigned long requiredDelay = getNextDelay();
    return (currentTime - _lastRetryTime >= requiredDelay);
}
