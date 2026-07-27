#ifndef STATE_H
#define STATE_H

class HAL; // Forward declaration

/**
 * @brief Enum class specifying firmware states.
 */
enum class State {
    BOOT,
    INITIALIZING,
    SELF_TEST,
    IDLE,
    MONITORING,
    WARNING,
    ALERT,
    FAULT,
    RECOVERY,
    SHUTDOWN
};

/**
 * @brief Abstract base class representing behaviors executed in states.
 */
class StateBehavior {
public:
    virtual ~StateBehavior() {}
    virtual void onEnter(HAL& hal) = 0;
    virtual void onUpdate(HAL& hal) = 0;
    virtual void onExit(HAL& hal) = 0;
};

#endif
