#include "WiFiConnectionPolicy.h"

WiFiConnectionPolicy::WiFiConnectionPolicy(bool autoConnect, bool reconnect, int maxRetries, unsigned long timeout, int minRSSI, int recoveryRSSI)
    : _autoConnect(autoConnect), _reconnectEnabled(reconnect), _maxRetryCount(maxRetries), _connectionTimeoutMs(timeout), _minRSSI(minRSSI), _recoveryRSSI(recoveryRSSI) {}
