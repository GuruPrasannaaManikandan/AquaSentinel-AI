#ifndef TASK_PRIORITY_H
#define TASK_PRIORITY_H

#ifdef LOW
#undef LOW
#endif
#ifdef HIGH
#undef HIGH
#endif

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
