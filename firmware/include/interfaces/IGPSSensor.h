#ifndef IGPSSENSOR_H
#define IGPSSENSOR_H

/**
 * @brief Abstract interface representing a GPS sensor module.
 */
class IGPSSensor {
public:
    virtual ~IGPSSensor() {}
    virtual bool initialize() = 0;
    virtual void read(double &lat, double &lon) = 0;
    virtual bool selfTest() = 0;
    virtual const char* status() = 0;
    virtual void shutdown() = 0;
};

#endif
