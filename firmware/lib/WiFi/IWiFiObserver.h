#ifndef IWIFI_OBSERVER_H
#define IWIFI_OBSERVER_H

#include "WiFiState.h"

/**
 * @brief Observer callback interface tracking connection events.
 */
class IWiFiObserver {
public:
    virtual ~IWiFiObserver() {}

    virtual void onWiFiStateTransition(WiFiState fromState, WiFiState toState) = 0;
    virtual void onSignalChanged(int rssi) = 0;
};

#endif
