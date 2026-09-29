#include "Task.h"
#include <Arduino.h>

#ifdef DISABLED
#undef DISABLED
#endif

Task::Task(TaskId id, const char* name, unsigned long intervalMs, TaskCallback callback, TaskPriority priority, bool enabled)
    : _id(id), _name(name), _intervalMs(intervalMs), _callback(callback), _priority(priority), _enabled(enabled), _state(enabled ? TaskState::READY : TaskState::DISABLED) {
    resetStats();
}

void Task::setEnabled(bool enabled) {
    _enabled = enabled;
    _state = enabled ? TaskState::READY : TaskState::DISABLED;
}

bool Task::isDue(unsigned long currentTime) const {
    if (!_enabled || _state == TaskState::ERROR) return false;
    return (long)(currentTime - _nextRunTime) >= 0;
}

void Task::execute(unsigned long currentTime, void* schedulerRef) {
    if (!_callback) {
        _state = TaskState::ERROR;
        _failureCount++;
        return;
    }

    _state = TaskState::RUNNING;

    // Calculate Jitter (ms)
    long jitter = (long)(currentTime - _nextRunTime);
    _currentJitterMs = (jitter > 0) ? (unsigned long)jitter : 0;
    
    _runCount++;

    // Jitter Statistics update
    if (_currentJitterMs > _maxJitterMs) _maxJitterMs = _currentJitterMs;
    if (_currentJitterMs < _minJitterMs || _minJitterMs == 0) _minJitterMs = _currentJitterMs;
    _avgJitterMs = (_avgJitterMs * (_runCount - 1) + _currentJitterMs) / _runCount;

    // Create Context
    TaskContext context;
    context.currentTime = currentTime;
    context.runCount = _runCount;
    context.lastRunTime = _lastRunTime;
    context.avgDurationUs = _avgDurationUs;
    context.maxDurationUs = _maxDurationUs;
    context.taskId = _id;
    context.priority = _priority;
    context.schedulerRef = schedulerRef;

    unsigned long startUs = micros();
    
    // Execute callback passing context reference
    _callback(context);
    
    unsigned long endUs = micros();
    unsigned long duration = endUs - startUs;

    _lastRunTime = currentTime;
    _nextRunTime = currentTime + _intervalMs;
    _successCount++;

    // Runtime Statistics update
    if (duration > _maxDurationUs) _maxDurationUs = duration;
    if (duration < _minDurationUs || _minDurationUs == 0) _minDurationUs = duration;
    _avgDurationUs = (_avgDurationUs * (_runCount - 1) + duration) / _runCount;
    
    _state = TaskState::WAITING;
}

void Task::recordMissed() {
    _missedExecutions++;
    _nextRunTime += _intervalMs;
}

void Task::resetStats() {
    _lastRunTime = 0;
    _nextRunTime = millis();
    _runCount = 0;
    _successCount = 0;
    _failureCount = 0;
    _maxDurationUs = 0;
    _minDurationUs = 0;
    _avgDurationUs = 0;
    _avgJitterMs = 0;
    _maxJitterMs = 0;
    _minJitterMs = 0;
    _currentJitterMs = 0;
    _missedExecutions = 0;
}
