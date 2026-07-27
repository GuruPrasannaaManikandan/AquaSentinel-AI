#ifndef TASK_H
#define TASK_H

#include "TaskId.h"
#include "TaskPriority.h"
#include "TaskContext.h"

enum class TaskState {
    READY,
    RUNNING,
    WAITING,
    DISABLED,
    ERROR,
    COMPLETED
};

// TaskCallback now accepts a reference to the TaskContext
typedef void (*TaskCallback)(TaskContext&);

class Task {
private:
    TaskId _id;
    const char* _name;
    unsigned long _intervalMs;
    TaskPriority _priority;
    bool _enabled;
    TaskCallback _callback;
    TaskState _state;

    // Timing and Count Statistics
    unsigned long _lastRunTime;
    unsigned long _nextRunTime;
    unsigned long _runCount;
    unsigned long _successCount;
    unsigned long _failureCount;

    // Runtime Microseconds Statistics
    unsigned long _maxDurationUs;
    unsigned long _minDurationUs;
    unsigned long _avgDurationUs;

    // Jitter Statistics (ms)
    unsigned long _avgJitterMs;
    unsigned long _maxJitterMs;
    unsigned long _minJitterMs;
    unsigned long _currentJitterMs;
    unsigned long _missedExecutions;

public:
    Task(TaskId id, const char* name, unsigned long intervalMs, TaskCallback callback, TaskPriority priority = TaskPriority::NORMAL, bool enabled = true);
    
    TaskId getId() const { return _id; }
    const char* getName() const { return _name; }
    unsigned long getInterval() const { return _intervalMs; }
    TaskPriority getPriority() const { return _priority; }
    bool isEnabled() const { return _enabled; }
    TaskState getState() const { return _state; }
    
    void setEnabled(bool enabled);
    void setState(TaskState state) { _state = state; }
    
    // Getters for Stats
    unsigned long getLastRunTime() const { return _lastRunTime; }
    unsigned long getNextRunTime() const { return _nextRunTime; }
    unsigned long getRunCount() const { return _runCount; }
    unsigned long getSuccessCount() const { return _successCount; }
    unsigned long getFailureCount() const { return _failureCount; }
    unsigned long getMaxDuration() const { return _maxDurationUs; }
    unsigned long getMinDuration() const { return _minDurationUs; }
    unsigned long getAvgDuration() const { return _avgDurationUs; }
    unsigned long getAvgJitter() const { return _avgJitterMs; }
    unsigned long getMaxJitter() const { return _maxJitterMs; }
    unsigned long getMinJitter() const { return _minJitterMs; }
    unsigned long getCurrentJitter() const { return _currentJitterMs; }
    unsigned long getMissedExecutions() const { return _missedExecutions; }

    bool isDue(unsigned long currentTime) const;
    void execute(unsigned long currentTime, void* schedulerRef);
    void recordMissed();
    void resetStats();
};

#endif
