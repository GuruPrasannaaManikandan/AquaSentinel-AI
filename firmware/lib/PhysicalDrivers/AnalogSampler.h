#ifndef ANALOG_SAMPLER_H
#define ANALOG_SAMPLER_H

#include <Arduino.h>

struct AnalogSample {
    int raw;      // median raw ADC count (0..4095)
    float volts;  // median pin voltage using the eFuse-calibrated ADC curve
};

/**
 * @brief Noise-robust ESP32 ADC reads shared by the analog sensor drivers.
 *
 * The ESP32 ADC is noisy and non-linear, so a single analogRead() * 3.3/4095
 * can be off by 100+ mV. This takes N samples, uses analogReadMilliVolts()
 * (factory-calibrated) and returns the median.
 */
namespace AnalogSampler {
    const int SATURATION_RAW = 4090;
    const int NO_SIGNAL_RAW = 5;

    void configurePin(int pin);
    AnalogSample readMedian(int pin, int samples);
}

#endif
