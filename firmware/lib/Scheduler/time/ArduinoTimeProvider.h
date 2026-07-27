#ifndef ARDUINO_TIME_PROVIDER_H
#define ARDUINO_TIME_PROVIDER_H

#include "ITimeProvider.h"

class ArduinoTimeProvider : public ITimeProvider {
public:
    ArduinoTimeProvider() {}
    ~ArduinoTimeProvider() override {}
    unsigned long now() override;
};

#endif
