# cSpell: disable
# pylint: disable=all
# ruff: noqa

import json
import os
from datetime import datetime
from config import SERVO_DATA_FILE


class ServoFileManager:
    """Maneja la escritura y lectura del archivo JSON de posición de servos"""

    def __init__(self, filename=SERVO_DATA_FILE):
        self.filename = filename
        self.initialize_file()

    def initialize_file(self):
        """Inicializar archivo con valores por defecto"""
        default_data = {
            "pan": 90,
            "tilt": 90,
            "tracking": False,
            "target": None,
            "timestamp": datetime.now().isoformat(),
            "error": {"x": 0, "y": 0},
            "distance": 0,
            "confidence": 0,
        }

        # Crear archivo si no existe
        if not os.path.exists(self.filename):
            self.write_position(default_data)
            print(f"✅ Archivo {self.filename} creado")

    def write_position(self, data):
        """Escribir posición de servos al archivo JSON"""
        try:
            # Agregar timestamp
            data["timestamp"] = datetime.now().isoformat()

            # Escribir con formato legible
            with open(self.filename, "w") as f:
                json.dump(data, f, indent=2)

            return True

        except Exception as e:
            print(f"❌ Error escribiendo archivo: {e}")
            return False

    def update_from_tracking(self, result, target_person=None):
        """Actualizar archivo desde resultado de tracking"""
        data = {
            "pan": float(result["pan_angle"]),
            "tilt": float(result["tilt_angle"]),
            "tracking": result["target_locked"],
            "target": target_person,
            "error": {
                "x": int(result["error"][0]),
                "y": int(result["error"][1]),
            },
            "distance": float(result.get("distance_to_center", 0)),
            "confidence": (
                float(result["target_face"]["confidence"])
                if result["target_face"]
                else 0
            ),
        }

        return self.write_position(data)

    def read_position(self):
        """Leer posición de servos desde archivo JSON"""
        try:
            with open(self.filename, "r") as f:
                data = json.load(f)
            return data

        except FileNotFoundError:
            print(f"⚠️ Archivo {self.filename} no encontrado")
            return None
        except json.JSONDecodeError:
            print(f"⚠️ Error decodificando JSON en {self.filename}")
            return None
        except Exception as e:
            print(f"❌ Error leyendo archivo: {e}")
            return None

    def get_servo_angles(self):
        """Obtener solo los ángulos de pan y tilt"""
        data = self.read_position()
        if data:
            return data.get("pan", 90), data.get("tilt", 90)
        return 90, 90

    def is_tracking(self):
        """Verificar si está en modo tracking"""
        data = self.read_position()
        if data:
            return data.get("tracking", False)
        return False
