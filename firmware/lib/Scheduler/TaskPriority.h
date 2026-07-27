#ifndef TASK_PRIORITY_H
#define TASK_PRIORITY_H

/**
 * @brief Enum representing priority ranks for scheduler sorting.
 */
enum class TaskPriority {
    BACKGROUND = 0,
    LOW = 1,
    NORMAL = 2,
    HIGH = 3,
    CRITICAL = 4
};

#endif
