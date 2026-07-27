#ifndef PIN_CONFIG_H
#define PIN_CONFIG_H

/**
 * @brief Structured configuration holder for ESP32 GPIO pin definitions.
 */
struct PinConfig {
    int phPin = 32;
    int turbidityPin = 33;
    int doPin = 34;
    int tempPin = 18;
    int salinityPin = 36;
    int gpsRxPin = 16;
    int gpsTxPin = 17;
    int greenLedPin = 19;
    int yellowLedPin = 21;
    int redLedPin = 22;
    int buzzerPin = 23;
    int pumpRelayPin = 27;
};

#endif
