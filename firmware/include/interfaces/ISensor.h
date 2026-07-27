#ifndef ISENSOR_H
#define ISENSOR_H

/**
 * @brief Abstract interface representing a physical water sensor.
 */
class ISensor {
public:
    virtual ~ISensor() {}
    virtual bool initialize() = 0;
    virtual float read() = 0;
    virtual bool selfTest() = 0;
    virtual const char* status() = 0;
    virtual void shutdown() = 0;
};

#endif
