# cSpell: disable
# pylint: disable=all
# ruff: noqa

import serial
import time
from config import ESP32_CONFIG, SERVO_CONFIG


class ESP32Controller:
    def __init__(self):
        self.serial = None
        self.connected = False
        self.last_send_time = 0
        self.send_interval = 0.05  # 20 Hz máximo

    def connect(self):
        """Conectar con ESP32 vía Serial"""
        try:
            self.serial = serial.Serial(
                port=ESP32_CONFIG["port"],
                baudrate=ESP32_CONFIG["baudrate"],
                timeout=ESP32_CONFIG["timeout"],
            )
            time.sleep(2)  # Esperar a que ESP32 se inicialice
            self.connected = True
            print(f"✅ Conectado a ESP32 en {ESP32_CONFIG['port']}")
            return True
        except Exception as e:
            print(f"❌ Error conectando ESP32: {e}")
            print(f"💡 Verifica que el puerto {ESP32_CONFIG['port']} sea correcto")
            return False

    def send_command(self, pan_angle, tilt_angle):
        """Enviar comando en formato CSV simple"""
        if not self.connected:
            return False

        # Limitar frecuencia de envío
        current_time = time.time()
        if current_time - self.last_send_time < self.send_interval:
            return True

        try:
            # Formato CSV simple: "95.3,87.2\n"
            command = f"{pan_angle:.1f},{tilt_angle:.1f}\n"
            self.serial.write(command.encode())
            self.serial.flush()  # Asegurar envío inmediato

            self.last_send_time = current_time
            return True

        except Exception as e:
            print(f"❌ Error enviando comando: {e}")
            return False

    def update_position(self, pan_angle, tilt_angle):
        """Actualizar posición de servos"""
        return self.send_command(pan_angle, tilt_angle)

    def center_servos(self):
        """Centrar servos"""
        return self.send_command(
            SERVO_CONFIG["pan_center"], SERVO_CONFIG["tilt_center"]
        )

    def close(self):
        """Cerrar conexión"""
        if self.serial and self.connected:
            # Centrar antes de cerrar
            self.center_servos()
            time.sleep(0.5)
            self.serial.close()
            self.connected = False
            print("🔌 Desconectado de ESP32")
