import paho.mqtt.client as mqtt
import json
import time


class MQTTSender:
    """Envía datos de tracking a MQTT para control en tiempo real"""

    def __init__(
        self, broker="broker.hivemq.com", port=1883, topic="facetracking/tuta/servo"
    ):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client = None
        self.connected = False
        self.message_count = 0

    def connect(self):
        """Conectar al broker MQTT"""
        try:
            self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect

            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()

            # Esperar conexión
            timeout = 5
            while not self.connected and timeout > 0:
                time.sleep(0.1)
                timeout -= 0.1

            if self.connected:
                print(f"✓ MQTT conectado a {self.broker}")
                print(f"  Topic: {self.topic}")
                return True
            else:
                print(f"✗ MQTT timeout conectando a {self.broker}")
                return False

        except Exception as e:
            print(f"✗ Error MQTT: {e}")
            return False

    def _on_connect(self, client, userdata, flags, rc):
        """Callback de conexión"""
        if rc == 0:
            self.connected = True
        else:
            self.connected = False
            print(f"Error MQTT: código {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback de desconexión"""
        self.connected = False
        if rc != 0:
            print("MQTT desconectado inesperadamente")

    def send_position(self, pan, tilt, tracking=False, confidence=0.0, target=None):
        """Enviar posición de servos por MQTT"""
        if not self.connected:
            return False

        try:
            payload = {
                "pan": round(pan, 2),
                "tilt": round(tilt, 2),
                "tracking": tracking,
                "confidence": round(confidence, 4),
                "target": target,
            }

            self.client.publish(self.topic, json.dumps(payload))
            self.message_count += 1
            return True

        except Exception as e:
            print(f"Error enviando MQTT: {e}")
            return False

    def close(self):
        """Cerrar conexión MQTT"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            print(f"✓ MQTT cerrado ({self.message_count} mensajes enviados)")
