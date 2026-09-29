#include "WiFiManager.h"
#include <Arduino.h>

#ifdef LOW
#undef LOW
#endif
#ifdef HIGH
#undef HIGH
#endif

WiFiManager::WiFiManager(IWiFiService* service, EventDispatcher* dispatcher, ICredentialsProvider* credentials, const WiFiConnectionPolicy& policy)
    : _service(service), _dispatcher(dispatcher), _credentials(credentials), _policy(policy),
      _retryManager(policy.getMaxRetryCount(), policy.getConnectionTimeout()),
      _currentState(WiFiState::DISCONNECTED), _connectingTimeStart(0),
      _sessionStartTimeMs(0), _totalConnects(0), _totalConnectTimeMs(0), _totalConnectionDurationMs(0) {
    
    memset(&_diagnostics, 0, sizeof(_diagnostics));
    _diagnostics.minRSSI = 0;
    _diagnostics.maxRSSI = 0;
    strcpy(_diagnostics.currentIp, "0.0.0.0");
    strcpy(_diagnostics.currentMac, "00:00:00:00:00:00");
    strcpy(_diagnostics.lastDisconnectReason, "None");
    _diagnostics.connectionSuccessPercentage = 100.0f;
}

void WiFiManager::initialize() {
    disconnect();
    _currentState = WiFiState::DISCONNECTED;
    _retryManager.reset();
}

void WiFiManager::connect() {
    if (_currentState == WiFiState::CONNECTED || _currentState == WiFiState::CONNECTING) {
        return;
    }

    _currentState = WiFiState::CONNECTING;
    _connectingTimeStart = millis();
    _service->begin(_credentials->getSSID(), _credentials->getPassword(), "AquaSentinel-ESP32");

    if (_dispatcher) {
        _dispatcher->publish(Event::WIFI_CONNECT_REQUEST, EventSource::NETWORK, EventPriority::NORMAL);
    }
}

void WiFiManager::disconnect() {
    _service->disconnect();
    WiFiState prev = _currentState;
    _currentState = WiFiState::DISCONNECTED;
    
    actionOnDisconnect("User Request");
    
    _observerManager.notifyStateTransition(prev, WiFiState::DISCONNECTED);
}

// Transition Guards
bool WiFiManager::guardSSIDFound() {
    // Simulated SSID check. In production, this queries scan results.
    return true;
}

bool WiFiManager::guardAuthSuccess() {
    // Simulated authentication handshake.
    return true;
}

bool WiFiManager::guardIPAcquired() {
    return (strcmp(_service->getIPAddress(), "0.0.0.0") != 0);
}

// Transition Actions
void WiFiManager::actionOnConnect(unsigned long duration) {
    _totalConnects++;
    _totalConnectTimeMs += duration;

    _diagnostics.connectionCount++;
    _diagnostics.averageConnectTimeMs = _totalConnectTimeMs / _totalConnects;
    
    if (duration > _diagnostics.longestConnectionMs) {
        _diagnostics.longestConnectionMs = duration;
    }
    if (duration < _diagnostics.shortestConnectionMs || _diagnostics.shortestConnectionMs == 0) {
        _diagnostics.shortestConnectionMs = duration;
    }

    _sessionStartTimeMs = millis();
    strcpy(_diagnostics.currentIp, _service->getIPAddress());
    strcpy(_diagnostics.currentMac, _service->getMACAddress());
    
    _diagnostics.connectionSuccessPercentage = ((float)_diagnostics.connectionCount / (float)(_diagnostics.connectionCount + _diagnostics.failureCount)) * 100.0f;

    // Log connection history
    _history.addRecord(WiFiState::DHCP, WiFiState::CONNECTED, _service->getRSSI(), _diagnostics.currentIp, "Success", _retryManager.getRetryCount(), 0);

    if (_dispatcher) {
        _dispatcher->publish(Event::WIFI_CONNECTED, EventSource::NETWORK, EventPriority::HIGH);
    }
}

void WiFiManager::actionOnDisconnect(const char* reason) {
    unsigned long sessionDuration = 0;
    if (_sessionStartTimeMs > 0) {
        sessionDuration = millis() - _sessionStartTimeMs;
        _totalConnectionDurationMs += sessionDuration;
        _diagnostics.averageConnectionDurationMs = _totalConnectionDurationMs / _diagnostics.connectionCount;
        _sessionStartTimeMs = 0;
    }

    strcpy(_diagnostics.lastDisconnectReason, reason);
    strcpy(_diagnostics.currentIp, "0.0.0.0");

    _history.addRecord(_currentState, WiFiState::DISCONNECTED, 0, "0.0.0.0", reason, _retryManager.getRetryCount(), sessionDuration);

    if (_dispatcher) {
        _dispatcher->publish(Event::WIFI_DISCONNECTED, EventSource::NETWORK, EventPriority::CRITICAL);
    }
}

void WiFiManager::update() {
    _service->update();
    WiFiState rawStatus = _service->getStatus();
    unsigned long nowMs = millis();
    WiFiState prev = _currentState;

    if (_currentState != rawStatus) {
        // Run state machine validations
        if (_currentState == WiFiState::CONNECTING && rawStatus == WiFiState::AUTHENTICATING) {
            if (guardSSIDFound()) {
                _currentState = WiFiState::AUTHENTICATING;
            } else {
                _diagnostics.failureCount++;
                _diagnostics.lastDisconnectReason[0] = '\0';
                strcpy(_diagnostics.lastDisconnectReason, "SSID Not Found");
                _currentState = WiFiState::FAILED;
                disconnect();
            }
        } 
        else if (_currentState == WiFiState::AUTHENTICATING && rawStatus == WiFiState::DHCP) {
            if (guardAuthSuccess()) {
                _currentState = WiFiState::DHCP;
            } else {
                _diagnostics.authenticationFailures++;
                _diagnostics.failureCount++;
                _currentState = WiFiState::FAILED;
                disconnect();
            }
        } 
        else if (_currentState == WiFiState::DHCP && rawStatus == WiFiState::CONNECTED) {
            if (guardIPAcquired()) {
                _currentState = WiFiState::CONNECTED;
                unsigned long duration = nowMs - _connectingTimeStart;
                actionOnConnect(duration);
            } else {
                _diagnostics.dhcpFailures++;
                _diagnostics.failureCount++;
                _currentState = WiFiState::FAILED;
                disconnect();
            }
        }
        else if (_currentState == WiFiState::CONNECTED && rawStatus == WiFiState::DISCONNECTED) {
            _currentState = WiFiState::RECONNECTING;
            actionOnDisconnect("Link Loss");
            _retryManager.incrementRetry();
        }
        else {
            // Keep state aligned
            _currentState = rawStatus;
        }

        // Notify State Change Observers
        if (prev != _currentState) {
            _observerManager.notifyStateTransition(prev, _currentState);
        }
    }

    // Check timeout during connecting phases
    if ((_currentState == WiFiState::CONNECTING || _currentState == WiFiState::AUTHENTICATING || _currentState == WiFiState::DHCP) &&
        (nowMs - _connectingTimeStart >= _policy.getConnectionTimeout())) {
        
        _diagnostics.failureCount++;
        _currentState = WiFiState::FAILED;
        actionOnDisconnect("Timeout");
        disconnect();

        if (_dispatcher) {
            _dispatcher->publish(Event::WIFI_TIMEOUT, EventSource::NETWORK, EventPriority::HIGH);
        }
    }

    // Handle reconnect timers if in failed or reconnecting modes
    if (_currentState == WiFiState::RECONNECTING || _currentState == WiFiState::FAILED) {
        if (_policy.isReconnectEnabled() && _retryManager.shouldRetry(nowMs)) {
            Serial.print("[WIFI-MANAGER] Reconnection attempt #");
            Serial.println(_retryManager.getRetryCount() + 1);

            _retryManager.incrementRetry();
            _currentState = WiFiState::CONNECTING;
            _connectingTimeStart = nowMs;
            _service->begin(_credentials->getSSID(), _credentials->getPassword(), "AquaSentinel-ESP32");

            if (_dispatcher) {
                _dispatcher->publish(Event::WIFI_RECONNECTING, EventSource::NETWORK, EventPriority::NORMAL);
            }
        } else if (_retryManager.isExhausted()) {
            _currentState = WiFiState::FAILED;
            _retryManager.reset();

            if (_dispatcher) {
                _dispatcher->publish(Event::WIFI_CONNECTION_FAILED, EventSource::NETWORK, EventPriority::CRITICAL);
            }
        }
    }

    // Monitor RSSI statistics if connected
    if (_currentState == WiFiState::CONNECTED) {
        int rssi = _service->getRSSI();
        _diagnostics.rssi = rssi;

        // RSSI Bounds
        if (rssi > _diagnostics.maxRSSI || _diagnostics.maxRSSI == 0) _diagnostics.maxRSSI = rssi;
        if (rssi < _diagnostics.minRSSI || _diagnostics.minRSSI == 0) _diagnostics.minRSSI = rssi;
        _diagnostics.averageRSSI = (_diagnostics.averageRSSI * 9 + rssi) / 10;

        _observerManager.notifySignalChanged(rssi);

        // Check weak signal policy floor
        if (rssi < _policy.getMinRSSI()) {
            if (_dispatcher) {
                _dispatcher->publish(Event::WIFI_SIGNAL_WEAK, EventSource::NETWORK, EventPriority::LOW);
            }
        }
    }

    // Keep diagnostics in sync
    _diagnostics.currentState = _currentState;
}

bool WiFiManager::isConnected() const {
    return _currentState == WiFiState::CONNECTED;
}

const char* WiFiManager::getIPAddress() const {
    return _service->getIPAddress();
}

int WiFiManager::getRSSI() const {
    return _service->getRSSI();
}

const char* WiFiManager::getMAC() const {
    return _service->getMACAddress();
}
