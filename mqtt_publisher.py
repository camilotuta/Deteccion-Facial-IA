import paho.mqtt.client as mqtt
import json
import time
import os

# Configuracion MQTT
MQTT_BROKER = "broker.hivemq.com"  # Broker publico gratuito
MQTT_PORT = 1883
MQTT_TOPIC = "facetracking/tuta/servo"  # Cambia 'tuta' por tu nombre para hacerlo unico

JSON_FILE = "servo_position.json"
UPDATE_RATE = 0.05  # 20 veces por segundo - TIEMPO REAL

print("=" * 60)
print("MQTT Publisher - Face Tracking (TIEMPO REAL)")
print("=" * 60)
print("Broker:", MQTT_BROKER)
print("Topic:", MQTT_TOPIC)
print("Tasa:", int(1 / UPDATE_RATE), "Hz")
print("=" * 60)

# Conectar a MQTT
client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✓ Conectado a MQTT broker")
    else:
        print("✗ Error conectando:", rc)


client.on_connect = on_connect

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    time.sleep(1)
except Exception as e:
    print("Error conectando al broker:", e)
    exit(1)

print("✓ Publicando datos en tiempo real... (Ctrl+C para detener)\n")

last_timestamp = None
count = 0

try:
    while True:
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    print("⚠️ Invalid JSON in servo_position.json - skipping this read")
                    time.sleep(UPDATE_RATE)
                    continue

            current_timestamp = data.get("timestamp")

            if current_timestamp != last_timestamp:
                # Enviar datos compactos
                payload = {
                    "pan": data.get("pan", 90),
                    "tilt": data.get("tilt", 90),
                    "tracking": data.get("tracking", False),
                    "confidence": data.get("confidence", 0),
                }

                client.publish(MQTT_TOPIC, json.dumps(payload))

                count += 1
                status = "🎯" if payload["tracking"] else "⏸️"
                print(
                    f"#{count} {status} Pan: {payload['pan']:.1f}° Tilt: {payload['tilt']:.1f}° | Conf: {payload['confidence']*100:.1f}%"
                )

                last_timestamp = current_timestamp

        else:
            print("⚠️ servo_position.json not found - waiting...")

        time.sleep(UPDATE_RATE)

except KeyboardInterrupt:
    print("\n\nDeteniendo...")
    client.loop_stop()
    client.disconnect()
    print("✓ Desconectado")
    print(f"Total mensajes: {count}")
