#include "ArduinoTimeProvider.h"
#include <Arduino.h>

unsigned long ArduinoTimeProvider::now() {
    return millis();
}
