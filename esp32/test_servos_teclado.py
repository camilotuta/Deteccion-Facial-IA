"""
Test de control de servos con teclado via MQTT
Controla los servos usando las flechas del teclado
"""

import paho.mqtt.client as mqtt
import json
import time
import keyboard  # pip install keyboard si no lo tienes

# ======================= CONFIGURACION =======================
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "facetracking/tuta/servo"

# Configuración de servos
TILT_CENTER = 130
TILT_MIN = 60
TILT_MAX = 160
TILT_STEP = 5  # Cuánto se mueve el tilt por cada tecla


# ======================= CLASE MQTT =======================
class MQTTController:
    def __init__(self, broker, port, topic):
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

            print(f"Conectando a {self.broker}...")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()

            # Esperar conexion
            timeout = 5
            while not self.connected and timeout > 0:
                time.sleep(0.1)
                timeout -= 0.1

            if self.connected:
                print(f"✓ MQTT conectado")
                print(f"  Topic: {self.topic}")
                return True
            else:
                print(f"✗ MQTT timeout")
                return False

        except Exception as e:
            print(f"✗ Error MQTT: {e}")
            return False

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
        else:
            self.connected = False

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False

    def send_command(self, pan_direction, tilt, duration=0.3, update_tilt=True):
        """Enviar comando a los servos
        duration: tiempo en segundos para el movimiento del servo 360
        update_tilt: si False, no envía el tilt (para movimientos solo de pan)
        """
        if not self.connected:
            print("✗ No conectado a MQTT")
            return False

        try:
            payload = {
                "pan_direction": str(pan_direction),
                "tilt": round(float(tilt), 2),
                "duration": round(float(duration), 2),
                "update_tilt": bool(update_tilt),
                "tracking": True,
                "confidence": 1.0,
                "target": "manual",
            }

            self.client.publish(self.topic, json.dumps(payload))
            self.message_count += 1
            return True

        except Exception as e:
            print(f"Error enviando MQTT: {e}")
            return False

    def close(self):
        """Cerrar conexion MQTT"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            print(f"✓ MQTT cerrado")


# ======================= MAIN =======================
def main():
    print("\n" + "=" * 70)
    print("🎮 CONTROL DE SERVOS CON TECLADO (MQTT)")
    print("=" * 70)
    print("\nControles:")
    print("  ← Flecha IZQUIERDA : Girar cámara a la IZQUIERDA (95°, 0.3s)")
    print("  → Flecha DERECHA   : Girar cámara a la DERECHA (80°, 0.1s)")
    print("  ↑ Flecha ARRIBA    : Inclinar cámara ARRIBA (menor ángulo)")
    print("  ↓ Flecha ABAJO     : Inclinar cámara ABAJO (mayor ángulo)")
    print("  ESPACIO            : DETENER servo 360 (90°)")
    print("  C                  : CENTRAR ambos servos")
    print("  Q o ESC            : SALIR")
    print("=" * 70 + "\n")

    # Conectar MQTT
    mqtt_ctrl = MQTTController(MQTT_BROKER, MQTT_PORT, MQTT_TOPIC)
    if not mqtt_ctrl.connect():
        print("✗ Error: No se pudo conectar a MQTT")
        print("💡 Verifica tu conexión a Internet")
        return

    # Estado actual
    current_tilt = TILT_CENTER
    last_pan_direction = "stop"

    # Centrar al inicio
    print("\n⚙️  Centrando servos...")
    mqtt_ctrl.send_command("stop", current_tilt)
    time.sleep(0.5)
    print("✓ Servos centrados\n")
    print("🎮 Sistema listo - Usa las flechas del teclado\n")

    try:
        while True:
            pan_direction = "stop"  # Por defecto, detener
            tilt_changed = False

            # Detectar teclas
            if keyboard.is_pressed("left"):
                pan_direction = "left"
                print("← IZQUIERDA (95°, 0.3s)")
                mqtt_ctrl.send_command(
                    pan_direction, current_tilt, duration=0.3, update_tilt=False
                )
                last_pan_direction = pan_direction
                time.sleep(0.1)
                continue

            elif keyboard.is_pressed("right"):
                pan_direction = "right"
                print("→ DERECHA (80°, 0.1s)")
                mqtt_ctrl.send_command(
                    pan_direction, current_tilt, duration=0.1, update_tilt=False
                )
                last_pan_direction = pan_direction
                time.sleep(0.1)
                continue

            elif keyboard.is_pressed("up"):
                current_tilt = max(TILT_MIN, current_tilt - TILT_STEP)
                tilt_changed = True
                print(f"↑ ARRIBA - Tilt: {current_tilt}°")
                mqtt_ctrl.send_command(
                    "stop", current_tilt, duration=0.0, update_tilt=True
                )
                time.sleep(0.1)
                continue

            elif keyboard.is_pressed("down"):
                current_tilt = min(TILT_MAX, current_tilt + TILT_STEP)
                tilt_changed = True
                print(f"↓ ABAJO - Tilt: {current_tilt}°")
                mqtt_ctrl.send_command(
                    "stop", current_tilt, duration=0.0, update_tilt=True
                )
                time.sleep(0.1)
                continue

            elif keyboard.is_pressed("space"):
                pan_direction = "stop"
                print("⏹️  STOP - Deteniendo servo 360")
                mqtt_ctrl.send_command(
                    "stop", current_tilt, duration=0.0, update_tilt=False
                )
                time.sleep(0.1)
                continue

            elif keyboard.is_pressed("c"):
                pan_direction = "stop"
                current_tilt = TILT_CENTER
                tilt_changed = True
                print("🎯 CENTRAR - Pan: stop, Tilt: 130°")
                mqtt_ctrl.send_command(
                    "stop", current_tilt, duration=0.0, update_tilt=True
                )
                time.sleep(0.1)
                continue

            elif keyboard.is_pressed("q") or keyboard.is_pressed("esc"):
                print("\n⚠️  Saliendo...")
                break

            # Pequeña pausa para no saturar
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n⚠️  Interrumpido por usuario")

    finally:
        print("\n🛑 Cerrando sistema...")
        # Centrar antes de salir
        mqtt_ctrl.send_command("stop", TILT_CENTER)
        time.sleep(0.3)
        mqtt_ctrl.close()
        print("✓ Sistema cerrado correctamente\n")


if __name__ == "__main__":
    # Verificar si keyboard está instalado
    try:
        import keyboard
    except ImportError:
        print("\n✗ Error: Módulo 'keyboard' no encontrado")
        print("📦 Instala con: pip install keyboard")
        print("\n⚠️  IMPORTANTE: Ejecuta como administrador en Windows\n")
        exit(1)

    main()
