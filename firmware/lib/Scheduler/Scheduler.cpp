#include "Scheduler.h"
#include <Arduino.h>

Scheduler::Scheduler(ITimeProvider* timeProvider) 
    : _timeProvider(timeProvider), _health(SchedulerHealth::IDLE), _diagnostics(timeProvider) {
    if (_timeProvider) {
        _diagnostics.start();
    }
}

Scheduler::~Scheduler() {}

void Scheduler::setTimeProvider(ITimeProvider* provider) {
    _timeProvider = provider;
    _diagnostics.setTimeProvider(provider);
    _diagnostics.start();
}

bool Scheduler::registerTask(Task* task) {
    return _taskManager.registerTask(task);
}

bool Scheduler::enableTask(TaskId id) {
    return _taskManager.enableTask(id);
}

bool Scheduler::disableTask(TaskId id) {
    return _taskManager.disableTask(id);
}

void Scheduler::execute() {
    if (!_timeProvider) {
        _health = SchedulerHealth::FAULT;
        return;
    }

    // Record loop start timestamps (for loop latency metrics)
    _diagnostics.recordLoopStart();

    unsigned long currentTime = _timeProvider->now();
    int highestPriorityIndex = -1;
    TaskPriority highestPriority = TaskPriority::BACKGROUND;
    bool foundDueTask = false;

    // 1. Identify due tasks and select highest priority
    for (int i = 0; i < _taskManager.getTaskCount(); i++) {
        Task* t = _taskManager.getTaskByIndex(i);
        if (t->isDue(currentTime)) {
            // Task priority sorting comparison
            if (!foundDueTask || t->getPriority() > highestPriority) {
                highestPriority = t->getPriority();
                highestPriorityIndex = i;
                foundDueTask = true;
            }
        }
    }

    // 2. Execute selected task
    if (highestPriorityIndex != -1) {
        _health = SchedulerHealth::RUNNING;
        Task* t = _taskManager.getTaskByIndex(highestPriorityIndex);
        
        // Safety: check if execution overrun missed window
        if ((long)(currentTime - t->getNextRunTime()) > (long)t->getInterval()) {
            t->recordMissed();
        }

        unsigned long startUs = micros();
        t->execute(currentTime, this);
        unsigned long durationUs = micros() - startUs;

        // Verify task state for failures
        bool success = (t->getState() != TaskState::ERROR);
        _diagnostics.recordTaskExecution(durationUs, success);

        // Detect overload warnings (if task runs longer than 50ms)
        if (durationUs > 50000) {
            _health = SchedulerHealth::OVERLOADED;
            Serial.print("[WARNING] Task OVERRUN: ");
            Serial.print(t->getName());
            Serial.print(" took ");
            Serial.print(durationUs / 1000);
            Serial.println(" ms!");
        }
    } else {
        _health = SchedulerHealth::IDLE;
    }
}
