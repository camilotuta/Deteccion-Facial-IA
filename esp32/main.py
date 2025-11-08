# cSpell: disable
# pylint: disable=all
# ruff: noqa

"""
Código MicroPython para ESP32
Lee el archivo servo_position.json y mueve los servos
"""

from machine import Pin, PWM
import time
import ujson as json

SERVO_CONFIG = {
    "pan_pin": 26,
    "tilt_pin": 25,
    "pan_center": 90,
    "tilt_center": 90,
}

# Archivo JSON (debe estar en la raíz del ESP32)
JSON_FILE = "servo_position.json"


class ServoController:
    def __init__(self):
        self.pan = PWM(Pin(SERVO_CONFIG["pan_pin"]), freq=50)
        self.tilt = PWM(Pin(SERVO_CONFIG["tilt_pin"]), freq=50)
        self.current_pan = SERVO_CONFIG["pan_center"]
        self.current_tilt = SERVO_CONFIG["tilt_center"]

    def _angle_to_duty(self, angle):
        """Convertir ángulo (0-180) a duty cycle"""
        # Para servos SG90:
        # 0° = ~26 duty (1ms pulso)
        # 90° = ~77 duty (1.5ms pulso)
        # 180° = ~128 duty (2ms pulso)
        min_duty = 26
        max_duty = 128
        duty = int(min_duty + (angle / 180.0) * (max_duty - min_duty))
        return duty

    def move_to(self, pan_angle, tilt_angle):
        """Mover servos con suavizado"""
        # Limitar rangos
        pan_angle = max(0, min(180, pan_angle))
        tilt_angle = max(30, min(150, tilt_angle))

        # Suavizado simple
        smoothing = 0.3
        self.current_pan = self.current_pan + (pan_angle - self.current_pan) * smoothing
        self.current_tilt = (
            self.current_tilt + (tilt_angle - self.current_tilt) * smoothing
        )

        # Aplicar
        self.pan.duty(self._angle_to_duty(self.current_pan))
        self.tilt.duty(self._angle_to_duty(self.current_tilt))

    def center(self):
        """Centrar servos"""
        self.move_to(SERVO_CONFIG["pan_center"], SERVO_CONFIG["tilt_center"])


class JSONFileReader:
    """Lee el archivo JSON desde el sistema de archivos del ESP32"""

    def __init__(self, filename):
        self.filename = filename
        self.last_read_time = 0
        self.read_interval = 0.05  # Leer cada 50ms (20 Hz)

    def read_servo_data(self):
        """Leer datos del archivo JSON"""
        try:
            # Leer archivo
            with open(self.filename, "r") as f:
                data = json.load(f)

            # Extraer ángulos
            pan = data.get("pan", 90)
            tilt = data.get("tilt", 90)
            tracking = data.get("tracking", False)

            return pan, tilt, tracking

        except OSError:
            # Archivo no existe
            return None, None, False
        except ValueError:
            # Error de JSON
            return None, None, False
        except Exception as e:
            print(f"Error leyendo JSON: {e}")
            return None, None, False

    def should_read(self):
        """Verificar si es momento de leer el archivo"""
        current_time = time.ticks_ms()
        if (
            time.ticks_diff(current_time, self.last_read_time)
            >= self.read_interval * 1000
        ):
            self.last_read_time = current_time
            return True
        return False


# ========== PROGRAMA PRINCIPAL ==========

print("=" * 50)
print("ESP32 Face Tracking - JSON File Mode")
print("=" * 50)

# Inicializar
servo = ServoController()
json_reader = JSONFileReader(JSON_FILE)

print(f"📄 Leyendo desde: {JSON_FILE}")
print("🎯 Centrando servos...")
servo.center()
time.sleep(1)
print("✅ Sistema listo")

# Variables de estado
last_pan = 90
last_tilt = 90
error_count = 0
max_errors = 50

print("\n🔄 Iniciando lectura de archivo...\n")

# Loop principal
while True:
    try:
        # Leer archivo JSON a 20 Hz
        if json_reader.should_read():
            pan, tilt, tracking = json_reader.read_servo_data()

            if pan is not None and tilt is not None:
                # Reset contador de errores
                if error_count > 0:
                    print("✅ Conexión restaurada")
                    error_count = 0

                # Solo mover si hay cambio significativo (>0.5°)
                if abs(pan - last_pan) > 0.5 or abs(tilt - last_tilt) > 0.5:
                    servo.move_to(pan, tilt)
                    last_pan = pan
                    last_tilt = tilt

                    # Imprimir cada 20 actualizaciones (~1 segundo)
                    if int(time.ticks_ms() / 1000) % 1 == 0:
                        status = "🎯 TRACKING" if tracking else "⏸️  IDLE"
                        print(f"{status} | Pan: {pan:6.1f}° Tilt: {tilt:6.1f}°")

            else:
                # Error leyendo archivo
                error_count += 1
                if error_count == 1:
                    print("⚠️  Esperando archivo JSON...")

                # Si hay muchos errores, centrar servos
                if error_count >= max_errors:
                    print("❌ Archivo no disponible, centrando servos...")
                    servo.center()
                    error_count = 0

        # Pequeña pausa para no saturar
        time.sleep_ms(10)

    except KeyboardInterrupt:
        print("\n\n👋 Deteniendo sistema...")
        servo.center()
        break

    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(1)

print("✅ Sistema detenido")
