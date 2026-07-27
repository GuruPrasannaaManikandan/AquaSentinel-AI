#include "TaskManager.h"
#include "time/ITimeProvider.h"
#include "SchedulerHealth.h"
#include "SchedulerDiagnostics.h"

#ifndef SCHEDULER_H
#define SCHEDULER_H

class Scheduler {
private:
    TaskManager _taskManager;
    ITimeProvider* _timeProvider;
    SchedulerHealth _health;
    SchedulerDiagnostics _diagnostics;

public:
    Scheduler(ITimeProvider* timeProvider = nullptr);
    ~Scheduler();

    void setTimeProvider(ITimeProvider* provider);
    bool registerTask(Task* task);
    bool enableTask(TaskId id);
    bool disableTask(TaskId id);
    
    /**
     * @brief Run cooperative execution tick.
     * Evaluates registered tasks and runs the highest-priority pending task.
     */
    void execute();

    TaskManager& getTaskManager() { return _taskManager; }
    SchedulerHealth getHealth() const { return _health; }
    const SchedulerDiagnostics& getDiagnostics() const { return _diagnostics; }
};

#endif
