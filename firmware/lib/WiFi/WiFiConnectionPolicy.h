#ifndef WIFI_CONNECTION_POLICY_H
#define WIFI_CONNECTION_POLICY_H

class WiFiConnectionPolicy {
private:
    bool _autoConnect;
    bool _reconnectEnabled;
    int _maxRetryCount;
    unsigned long _connectionTimeoutMs;
    int _minRSSI;
    int _recoveryRSSI;

public:
    WiFiConnectionPolicy(bool autoConnect = true, bool reconnect = true, int maxRetries = 3, unsigned long timeout = 10000, int minRSSI = -80, int recoveryRSSI = -75);
    ~WiFiConnectionPolicy() {}

    bool isAutoConnect() const { return _autoConnect; }
    bool isReconnectEnabled() const { return _reconnectEnabled; }
    int getMaxRetryCount() const { return _maxRetryCount; }
    unsigned long getConnectionTimeout() const { return _connectionTimeoutMs; }
    int getMinRSSI() const { return _minRSSI; }
    int getRecoveryRSSI() const { return _recoveryRSSI; }
};

#endif
