#ifndef IACTUATOR_H
#define IACTUATOR_H

/**
 * @brief Abstract interface representing a physical actuator output (LED, buzzer, relay).
 */
class IActuator {
public:
    virtual ~IActuator() {}
    virtual bool initialize() = 0;
    virtual bool writeState(const char* state) = 0;
    virtual const char* readState() = 0;
    virtual bool selfTest() = 0;
    virtual const char* status() = 0;
    virtual void shutdown() = 0;
};

#endif
