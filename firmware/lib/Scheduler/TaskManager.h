#ifndef TASK_MANAGER_H
#define TASK_MANAGER_H

#include "Task.h"
#include "SchedulerConfig.h"

class TaskManager {
private:
    Task* _tasks[MAX_TASKS];
    int _taskCount;

public:
    TaskManager();
    ~TaskManager();

    bool registerTask(Task* task);
    bool removeTask(TaskId id);
    bool enableTask(TaskId id);
    bool disableTask(TaskId id);
    bool pauseTask(TaskId id);
    bool resumeTask(TaskId id);
    
    Task* getTask(TaskId id) const;
    Task* getTaskByIndex(int index) const;
    int getTaskCount() const { return _taskCount; }
    void resetAllStatistics();
};

#endif
