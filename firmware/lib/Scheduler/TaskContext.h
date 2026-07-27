#ifndef TASK_CONTEXT_H
#define TASK_CONTEXT_H

#include "TaskId.h"
#include "TaskPriority.h"

/**
 * @brief Context structure passed to task callback functions at execution runtime.
 */
struct TaskContext {
    unsigned long currentTime;
    unsigned long runCount;
    unsigned long lastRunTime;
    unsigned long avgDurationUs;
    unsigned long maxDurationUs;
    TaskId taskId;
    TaskPriority priority;
    void* schedulerRef; // Reference to the orchestrating scheduler instance
};

#endif
