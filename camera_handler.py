# cSpell: disable
# pylint: disable=all
# ruff: noqa

import cv2
from config import CAMERA_CONFIG


class CameraHandler:
    def __init__(self):
        self.cap = None
        self.is_running = False

    def start(self):
        """Iniciar captura de cámara"""
        try:
            self.cap = cv2.VideoCapture(CAMERA_CONFIG["index"])

            # Configurar resolución
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_CONFIG["width"])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_CONFIG["height"])
            self.cap.set(cv2.CAP_PROP_FPS, CAMERA_CONFIG["fps"])

            # Verificar si abrió correctamente
            if not self.cap.isOpened():
                return False

            self.is_running = True
            print(
                f"✅ Cámara iniciada: {CAMERA_CONFIG['width']}x{CAMERA_CONFIG['height']} @ {CAMERA_CONFIG['fps']}fps"
            )
            return True

        except Exception as e:
            print(f"❌ Error iniciando cámara: {e}")
            return False

    def read(self):
        """Leer frame de la cámara"""
        if not self.is_running or self.cap is None:
            return None

        ret, frame = self.cap.read()
        return frame if ret else None

    def stop(self):
        """Detener cámara"""
        if self.cap is not None:
            self.cap.release()
            self.is_running = False
            print("📷 Cámara detenida")

    def get_frame_center(self):
        """Obtener centro del frame"""
        return (CAMERA_CONFIG["width"] // 2, CAMERA_CONFIG["height"] // 2)
