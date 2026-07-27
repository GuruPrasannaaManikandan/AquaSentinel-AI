#ifndef EVENT_PRIORITY_H
#define EVENT_PRIORITY_H

/**
 * @brief Enum class specifying prioritization bands for FSM event processing.
 */
enum class EventPriority {
    BACKGROUND = 0,
    LOW = 1,
    NORMAL = 2,
    HIGH = 3,
    CRITICAL = 4
};

#endif
