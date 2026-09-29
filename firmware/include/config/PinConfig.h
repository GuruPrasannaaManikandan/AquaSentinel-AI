#ifndef PIN_CONFIG_H
#define PIN_CONFIG_H

/**
 * @brief Structured configuration holder for ESP32 GPIO pin definitions.
 */
struct PinConfig {
    int phPin = 32;
    int turbidityPin = 34;
    int doPin = 35;
    int tempPin = 33;
    int salinityPin = 36;
    int gpsRxPin = 16;
    int gpsTxPin = 17;
    int greenLedPin = 25;
    int yellowLedPin = 26;
    int redLedPin = 27;
    int buzzerPin = 14;
    int pumpRelayPin = 19;
};

#endif
