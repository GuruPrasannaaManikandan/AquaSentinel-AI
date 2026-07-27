#ifndef WIFI_RETRY_MANAGER_H
#define WIFI_RETRY_MANAGER_H

class WiFiRetryManager {
private:
    int _retryCount;
    int _maxRetries;
    unsigned long _baseIntervalMs;
    unsigned long _maxIntervalMs;
    unsigned long _lastRetryTime;

public:
    WiFiRetryManager(int maxRetries = 5, unsigned long baseIntervalMs = 2000, unsigned long maxIntervalMs = 30000);
    ~WiFiRetryManager() {}

    void incrementRetry();
    void reset();
    bool shouldRetry(unsigned long currentTime);
    
    /**
     * @brief Computes exponential backoff interval: base * 2^retries
     */
    unsigned long getNextDelay() const;
    
    int getRetryCount() const { return _retryCount; }
    bool isExhausted() const { return _retryCount >= _maxRetries; }
};

#endif
