#include "SchedulerDiagnostics.h"
#include <Arduino.h>

SchedulerDiagnostics::SchedulerDiagnostics(ITimeProvider* timeProvider) 
    : _timeProvider(timeProvider) {
    reset();
}

void SchedulerDiagnostics::setTimeProvider(ITimeProvider* provider) {
    _timeProvider = provider;
}

void SchedulerDiagnostics::start() {
    if (_timeProvider) {
        _startTime = _timeProvider->now();
    }
}

void SchedulerDiagnostics::recordLoopStart() {
    unsigned long currentUs = micros();
    _loopCount++;

    if (_lastLoopTimeUs > 0) {
        unsigned long latency = currentUs - _lastLoopTimeUs;
        _totalLoopLatencyUs += latency;
    }
    _lastLoopTimeUs = currentUs;
}

void SchedulerDiagnostics::recordTaskExecution(unsigned long durationUs, bool success) {
    if (!success) {
        _taskFailures++;
    }

    _totalTaskExecutionTimeUs += durationUs;

    if (durationUs > _longestExecutionUs) {
        _longestExecutionUs = durationUs;
    }
    if (durationUs < _shortestExecutionUs || _shortestExecutionUs == 0) {
        _shortestExecutionUs = durationUs;
    }
}

unsigned long SchedulerDiagnostics::getUptimeMs() const {
    if (!_timeProvider) return 0;
    return _timeProvider->now() - _startTime;
}

float SchedulerDiagnostics::getSchedulerUtilization() const {
    unsigned long uptimeMs = getUptimeMs();
    if (uptimeMs == 0) return 0.0f;

    // Convert total task execution microsecond duration to millisecond
    unsigned long execMs = _totalTaskExecutionTimeUs / 1000;
    float utilization = ((float)execMs / (float)uptimeMs) * 100.0f;
    return (utilization > 100.0f) ? 100.0f : utilization;
}

unsigned long SchedulerDiagnostics::getAverageLoopLatencyUs() const {
    if (_loopCount <= 1) return 0;
    return _totalLoopLatencyUs / (_loopCount - 1);
}

void SchedulerDiagnostics::reset() {
    _startTime = 0;
    _taskFailures = 0;
    _longestExecutionUs = 0;
    _shortestExecutionUs = 0;
    _totalTaskExecutionTimeUs = 0;
    _loopCount = 0;
    _lastLoopTimeUs = 0;
    _totalLoopLatencyUs = 0;
}
