from machine import Pin, PWM
import network
import time
from umqtt.simple import MQTTClient
import ujson

# Configuracion
WIFI_SSID = "PETRA"
WIFI_PASSWORD = "PETRA2021"

MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = b"facetracking/tuta/servo"  # Debe coincidir con el publisher
CLIENT_ID = b"esp32_servo_tuta"

SERVO_CONFIG = {
    "pan_pin": 26,
    "tilt_pin": 25,
    "pan_center": 90,
    "tilt_center": 90,
}


class ServoController:
    def __init__(self):
        self.pan = PWM(Pin(SERVO_CONFIG["pan_pin"]), freq=50)
        self.tilt = PWM(Pin(SERVO_CONFIG["tilt_pin"]), freq=50)
        self.current_pan = SERVO_CONFIG["pan_center"]
        self.current_tilt = SERVO_CONFIG["tilt_center"]
        self.pan.duty(self.angle_to_duty(self.current_pan))
        self.tilt.duty(self.angle_to_duty(self.current_tilt))

    def angle_to_duty(self, angle):
        min_duty = 26
        max_duty = 128
        duty = int(min_duty + (angle / 180.0) * (max_duty - min_duty))
        return duty

    def move_to(self, pan_angle, tilt_angle):
        pan_angle = max(0, min(180, pan_angle))
        tilt_angle = max(30, min(150, tilt_angle))

        smoothing = 0.3
        self.current_pan = self.current_pan + (pan_angle - self.current_pan) * smoothing
        self.current_tilt = (
            self.current_tilt + (tilt_angle - self.current_tilt) * smoothing
        )

        self.pan.duty(self.angle_to_duty(self.current_pan))
        self.tilt.duty(self.angle_to_duty(self.current_tilt))

    def center(self):
        self.move_to(SERVO_CONFIG["pan_center"], SERVO_CONFIG["tilt_center"])


def connect_wifi():
    print("Conectando a WiFi...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            print(".", end="")
            time.sleep(1)
            timeout -= 1

    if wlan.isconnected():
        print("")
        print("WiFi conectado!")
        print("IP:", wlan.ifconfig()[0])
        return True
    else:
        print("")
        print("No se pudo conectar a WiFi")
        return False


# Variable global para el servo
servo = None
message_count = 0


def mqtt_callback(topic, msg):
    global servo, message_count
    try:
        data = ujson.loads(msg)
        pan = data.get("pan", 90)
        tilt = data.get("tilt", 90)
        tracking = data.get("tracking", False)
        confidence = data.get("confidence", 0)

        servo.move_to(pan, tilt)

        message_count += 1
        status = "TRACKING" if tracking else "IDLE"

        if message_count % 10 == 0:  # Imprimir cada 10 mensajes
            print(
                "#" + str(message_count),
                status,
                "| Pan:",
                round(pan, 1),
                "Tilt:",
                round(tilt, 1),
                "| Conf:",
                round(confidence * 100, 1),
                "%",
            )

    except Exception as e:
        print("Error procesando mensaje:", str(e))


print("=" * 50)
print("ESP32 Face Tracking - MQTT TIEMPO REAL")
print("=" * 50)

if not connect_wifi():
    print("Sistema detenido - No hay conexion WiFi")
    while True:
        time.sleep(1)

servo = ServoController()
print("Servos inicializados")
servo.center()
time.sleep(1)

print("Conectando a MQTT broker:", MQTT_BROKER)

try:
    client = MQTTClient(CLIENT_ID, MQTT_BROKER)
    client.set_callback(mqtt_callback)
    client.connect()
    client.subscribe(MQTT_TOPIC)
    print("Suscrito a:", MQTT_TOPIC)
    print("=" * 50)
    print("Sistema ACTIVO - Recibiendo en tiempo real...")
    print("")

    while True:
        client.check_msg()  # No bloqueante
        time.sleep(0.01)  # 10ms delay

except KeyboardInterrupt:
    print("")
    print("Deteniendo...")
    servo.center()
    client.disconnect()
    print("Desconectado")
except Exception as e:
    print("Error:", str(e))
    servo.center()
    try:
        client.disconnect()
    except:
        pass
