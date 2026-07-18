from src.iot.mqtt_client import MQTTClient

class CommunicationLayer:
    """
    Handles network communication interfaces.
    Simulates Wi-Fi stack connection status and wraps MQTT protocol operations.
    """
    def __init__(self, client_id: str, use_mock: bool = True):
        self.client_id = client_id
        self.wifi_connected = False
        self.mqtt_connected = False
        self.client = MQTTClient(client_id=client_id, use_mock=use_mock)

    def connect_wifi(self, ssid: str, password: str) -> bool:
        """Simulates joining a Wi-Fi Access Point."""
        if ssid and password:
            self.wifi_connected = True
            return True
        self.wifi_connected = False
        return False

    def disconnect_wifi(self):
        """Simulates disconnecting from Wi-Fi."""
        self.wifi_connected = False
        self.mqtt_connected = False

    def connect_mqtt(self, host: str = "localhost", port: int = 1883) -> bool:
        """Connects the MQTT client if Wi-Fi is active."""
        if not self.wifi_connected:
            self.mqtt_connected = False
            return False
        try:
            self.client.connect(host, port)
            self.mqtt_connected = True
            return True
        except Exception:
            self.mqtt_connected = False
            return False

    def disconnect_mqtt(self):
        """Disconnects the MQTT client."""
        try:
            self.client.disconnect()
        except Exception:
            pass
        self.mqtt_connected = False

    def publish(self, topic: str, payload: dict) -> bool:
        """Publishes payload via MQTT client."""
        if not self.mqtt_connected:
            return False
        return self.client.publish(topic, payload)

    def subscribe(self, topic: str, callback = None) -> bool:
        """Subscribes to an MQTT topic."""
        if not self.mqtt_connected:
            return False
        if callback:
            self.client.set_on_message(callback)
        return self.client.subscribe(topic)
