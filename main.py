# cSpell: disable
# pylint: disable=all
# ruff: noqa

import cv2
import time
from camera_handler import CameraHandler
from face_tracker import FaceTracker
from esp32_controller import ESP32Controller
from config import CAMERA_CONFIG


def main():
    print("🎯 Iniciando sistema de seguimiento facial...")

    # Inicializar componentes
    camera = CameraHandler()
    tracker = FaceTracker()
    esp32 = ESP32Controller()

    if not camera.start():
        print("❌ Error: No se pudo iniciar la cámara")
        return

    if not esp32.connect():
        print("❌ Error: No se pudo conectar con ESP32")
        print("💡 Verifica el puerto serial en config.py")
        return

    print("✅ Sistema iniciado correctamente")
    print("Presiona 'q' para salir, 'c' para centrar servos, 'r' para reset tracking")

    # Centrar servos al inicio
    esp32.center_servos()
    time.sleep(1)

    frame_count = 0
    fps_start_time = time.time()
    fps = 0

    try:
        while True:
            # Capturar frame
            frame = camera.read()
            if frame is None:
                continue

            # Procesar seguimiento
            result = tracker.process_frame(frame, frame_count)

            if result["face_detected"]:
                # Enviar comandos a ESP32
                esp32.update_position(result["pan_angle"], result["tilt_angle"])

            # Calcular FPS
            frame_count += 1
            if frame_count % 30 == 0:
                fps = 30 / (time.time() - fps_start_time)
                fps_start_time = time.time()

            # Dibujar información en pantalla
            annotated_frame = tracker.draw_annotations(frame, result, fps)

            # Mostrar
            cv2.imshow("Face Tracking System", annotated_frame)

            # Controles de teclado
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("c"):
                esp32.center_servos()
                tracker.reset()
                print("🎯 Servos centrados")
            elif key == ord("r"):
                tracker.reset()
                print("🔄 Tracking reseteado")

    except KeyboardInterrupt:
        print("\n⚠️  Interrumpido por usuario")

    finally:
        print("🛑 Cerrando sistema...")
        camera.stop()
        esp32.center_servos()
        esp32.close()
        cv2.destroyAllWindows()
        print("✅ Sistema cerrado correctamente")


if __name__ == "__main__":
    main()
