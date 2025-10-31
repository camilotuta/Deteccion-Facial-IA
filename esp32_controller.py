# cSpell: disable
# pylint: disable=all
# ruff: noqa

import serial
import time
import json
from config import ESP32_CONFIG, SERVO_CONFIG


class ESP32Controller:
    def __init__(self):
        self.serial = None
        self.connected = False

    def connect(self):
        """Conectar con ESP32 vía Serial"""
        try:
            self.serial = serial.Serial(
                port=ESP32_CONFIG["port"],
                baudrate=ESP32_CONFIG["baudrate"],
                timeout=ESP32_CONFIG["timeout"],
            )
            time.sleep(2)
            self.connected = True
            print(f"✅ Conectado a ESP32 en {ESP32_CONFIG['port']}")
            return True
        except Exception as e:
            print(f"❌ Error conectando ESP32: {e}")
            return False

    def send_command(self, pan_angle, tilt_angle):
        """Enviar comando de posición a ESP32"""
        if not self.connected:
            return False

        try:
            command = {"pan": int(pan_angle), "tilt": int(tilt_angle)}

            self.serial.write(json.dumps(command).encode() + b"\n")
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
            self.serial.close()
            self.connected = False
            print("🔌 Desconectado de ESP32")
