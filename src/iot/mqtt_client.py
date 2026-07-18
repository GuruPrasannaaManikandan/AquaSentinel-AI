import json
import logging

class InMemoryMQTTBroker:
    """
    An in-memory MQTT broker simulator supporting topic subscription, publishing, 
    and wildcard '+' and '#' matching. Fully deterministic for isolated unit testing.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Resets the broker singleton instance."""
        cls._instance = None

    def __init__(self):
        self.subscriptions = {} # topic -> list of subscriber clients

    def subscribe(self, client, topic):
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        if client not in self.subscriptions[topic]:
            self.subscriptions[topic].append(client)

    def unsubscribe(self, client, topic):
        if topic in self.subscriptions and client in self.subscriptions[topic]:
            self.subscriptions[topic].remove(client)

    def publish(self, sender_client, topic, payload):
        for sub_topic, clients in self.subscriptions.items():
            if self._match_topic(sub_topic, topic):
                for client in clients:
                    # Notify subscriber client
                    client._on_message_received(topic, payload)

    def _match_topic(self, sub_topic, pub_topic):
        sub_parts = sub_topic.split('/')
        pub_parts = pub_topic.split('/')
        if '#' in sub_parts:
            idx = sub_parts.index('#')
            return pub_parts[:idx] == sub_parts[:idx]
        if len(sub_parts) != len(pub_parts):
            return False
        for s, p in zip(sub_parts, pub_parts):
            if s == '+':
                continue
            if s != p:
                return False
        return True


class MQTTClient:
    """
    Virtual MQTT client supporting connections, publish, subscribe, and callback configurations.
    If `use_mock=True`, connects to InMemoryMQTTBroker (default).
    If `use_mock=False`, connects to a real MQTT broker using `paho-mqtt`.
    """
    def __init__(self, client_id, use_mock=True):
        self.client_id = client_id
        self.use_mock = use_mock
        self.connected = False
        self.subscribed_topics = []
        self.message_callback = None

        if self.use_mock:
            self.broker = InMemoryMQTTBroker.get_instance()
        else:
            import paho.mqtt.client as mqtt
            # Support both older and newer paho-mqtt versions
            try:
                self.paho_client = mqtt.Client(client_id=client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
            except AttributeError:
                self.paho_client = mqtt.Client(client_id=client_id)
            self.paho_client.on_message = self._paho_on_message

    def _paho_on_message(self, client, userdata, msg):
        try:
            payload_str = msg.payload.decode('utf-8')
            self._on_message_received(msg.topic, payload_str)
        except Exception as e:
            logging.error(f"Error handling paho-mqtt message: {e}")

    def connect(self, host="localhost", port=1883, keepalive=60):
        if self.use_mock:
            self.connected = True
            return True
        else:
            try:
                self.paho_client.connect(host, port, keepalive)
                self.paho_client.loop_start()
                self.connected = True
                return True
            except Exception as e:
                logging.error(f"Failed to connect to real MQTT broker: {e}")
                self.connected = False
                return False

    def disconnect(self):
        if self.use_mock:
            # Unsubscribe from all topics
            for topic in list(self.subscribed_topics):
                self.unsubscribe(topic)
            self.connected = False
            return True
        else:
            try:
                self.paho_client.loop_stop()
                self.paho_client.disconnect()
            except Exception:
                pass
            self.connected = False
            return True

    def publish(self, topic, payload, qos=0, retain=False):
        if not self.connected:
            raise ConnectionError("Client is not connected to broker.")
        
        # Serialize payload if it's a dict
        if isinstance(payload, dict):
            payload_str = json.dumps(payload)
        else:
            payload_str = str(payload)

        if self.use_mock:
            self.broker.publish(self, topic, payload_str)
        else:
            self.paho_client.publish(topic, payload_str, qos=qos, retain=retain)
        return True

    def subscribe(self, topic, qos=0):
        if not self.connected:
            raise ConnectionError("Client is not connected to broker.")
        
        if self.use_mock:
            self.broker.subscribe(self, topic)
        else:
            self.paho_client.subscribe(topic, qos=qos)
            
        if topic not in self.subscribed_topics:
            self.subscribed_topics.append(topic)
        return True

    def unsubscribe(self, topic):
        if self.use_mock:
            self.broker.unsubscribe(self, topic)
        else:
            self.paho_client.unsubscribe(topic)
            
        if topic in self.subscribed_topics:
            self.subscribed_topics.remove(topic)
        return True

    def set_on_message(self, callback):
        """
        Sets the callback for message reception. 
        Callback signature: callback(topic, payload_dict)
        """
        self.message_callback = callback

    def _on_message_received(self, topic, payload_str):
        if self.message_callback:
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                payload = payload_str
            self.message_callback(topic, payload)

