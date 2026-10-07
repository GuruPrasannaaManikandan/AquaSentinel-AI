#include "AnalogSampler.h"
#include <stdlib.h>

namespace {
const int MAX_SAMPLES = 64;

int compareInts(const void* a, const void* b) {
    return (*(const int*)a - *(const int*)b);
}
}

void AnalogSampler::configurePin(int pin) {
    pinMode(pin, INPUT);
    analogReadResolution(12);
    analogSetPinAttenuation(pin, ADC_11db); // 0 - ~3.1 V full scale
}

AnalogSample AnalogSampler::readMedian(int pin, int samples) {
    if (samples < 1) samples = 1;
    if (samples > MAX_SAMPLES) samples = MAX_SAMPLES;

    int raws[MAX_SAMPLES];
    int mvs[MAX_SAMPLES];
    for (int i = 0; i < samples; i++) {
        raws[i] = analogRead(pin);
        mvs[i] = (int)analogReadMilliVolts(pin);
        delayMicroseconds(200);
    }
    qsort(raws, samples, sizeof(int), compareInts);
    qsort(mvs, samples, sizeof(int), compareInts);

    AnalogSample s;
    s.raw = raws[samples / 2];
    s.volts = mvs[samples / 2] / 1000.0f;
    return s;
}
