#ifndef SCHEDULER_HEALTH_H
#define SCHEDULER_HEALTH_H

/**
 * @brief Enum representing overall health of the scheduler loop.
 */
enum class SchedulerHealth {
    IDLE,       // No tasks pending
    RUNNING,    // Executing tasks normally
    OVERLOADED, // Loop latency too high, tasks missing windows
    STARVING,   // Tasks waiting due to other long-running tasks
    FAULT       // Severe engine failure
};

#endif
