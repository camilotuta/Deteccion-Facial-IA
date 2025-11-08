# cSpell: disable
# pylint: disable=all
# ruff: noqa

import cv2
import time
from camera_handler import CameraHandler
from face_tracker import FaceTracker
from esp32_controller import ESP32Controller
from servo_file_manager import ServoFileManager
from detection_logger import DetectionLogger
from mqtt_sender import MQTTSender


def print_controls():
    """Mostrar controles disponibles"""
    print("\n" + "=" * 60)
    print("🎮 CONTROLES DEL SISTEMA")
    print("=" * 60)
    print("  q - Salir del programa")
    print("  c - Centrar servos")
    print("  r - Reset tracking")
    print("  t - Seguir a TUTA")
    print("  l - Seguir a LAURA")
    print("  n - No seguir a nadie")
    print("  h - Mostrar esta ayuda")
    print("=" * 60 + "\n")


def main():
    print("🎯 Iniciando sistema de seguimiento facial - TIEMPO REAL")

    # Inicializar componentes
    camera = CameraHandler()
    tracker = FaceTracker()
    esp32 = ESP32Controller()
    file_manager = ServoFileManager()
    logger = DetectionLogger()
    mqtt = MQTTSender()  # NUEVO - MQTT para tiempo real

    if not camera.start():
        print("❌ Error: No se pudo iniciar la cámara")
        return

    # Conectar ESP32 (opcional)
    if not esp32.connect():
        print("⚠️  ESP32 no conectado (usando solo MQTT)")

    # Conectar MQTT (CRÍTICO para tiempo real)
    if not mqtt.connect():
        print("❌ Error: No se pudo conectar a MQTT")
        print("💡 Verifica tu conexión a Internet")
        return

    print("✅ Sistema iniciado correctamente")
    print(f"📄 Archivo de servos: {file_manager.filename}")
    print("🌐 MQTT: ACTIVO (Tiempo Real)")
    print_controls()

    # Centrar servos
    mqtt.send_position(90, 90, tracking=False)
    if esp32.connected:
        esp32.center_servos()
    time.sleep(0.5)

    frame_count = 0
    fps_samples = []

    try:
        while True:
            loop_start = time.time()

            # Capturar frame
            frame = camera.read()
            if frame is None:
                continue

            # Procesar tracking
            result = tracker.process_frame(frame, frame_count)

            # MQTT - Enviar en TIEMPO REAL (sin delay)
            if result["target_locked"]:
                mqtt.send_position(
                    result["pan_angle"],
                    result["tilt_angle"],
                    tracking=True,
                    confidence=result["target_face"]["confidence"],
                    target=tracker.target_person,
                )
            else:
                # Enviar posición centrada cuando no hay target
                mqtt.send_position(90, 90, tracking=False)

            # Actualizar archivo JSON (backup)
            file_manager.update_from_tracking(result, tracker.target_person)

            # Enviar a ESP32 si está conectado (legacy)
            if result["target_locked"] and esp32.connected:
                esp32.update_position(result["pan_angle"], result["tilt_angle"])

            # Log de detecciones
            if result["all_faces"] and frame_count % 30 == 0:
                logger.log_detections(
                    result["all_faces"], result["target_face"], tracker.target_person
                )

            # Calcular FPS
            frame_count += 1
            fps_samples.append(1.0 / (time.time() - loop_start + 0.001))
            if len(fps_samples) > 30:
                fps_samples.pop(0)
            fps = sum(fps_samples) / len(fps_samples)

            # Dibujar anotaciones
            annotated_frame = tracker.draw_annotations(frame, result, fps)

            # Agregar indicador MQTT
            mqtt_status = "🌐 MQTT: ACTIVO" if mqtt.connected else "🌐 MQTT: INACTIVO"
            cv2.putText(
                annotated_frame,
                mqtt_status,
                (10, 210),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0) if mqtt.connected else (0, 0, 255),
                2,
            )

            # Mostrar
            cv2.imshow("Face Tracking System - TIEMPO REAL", annotated_frame)

            # Controles
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                print("\n👋 Saliendo...")
                break

            elif key == ord("c"):
                mqtt.send_position(90, 90, tracking=False)
                if esp32.connected:
                    esp32.center_servos()
                tracker.reset()
                file_manager.write_position(
                    {
                        "pan": 90,
                        "tilt": 90,
                        "tracking": False,
                        "target": None,
                        "error": {"x": 0, "y": 0},
                        "distance": 0,
                        "confidence": 0,
                    }
                )
                print("🎯 Servos centrados")

            elif key == ord("r"):
                tracker.reset()
                print("🔄 Tracking reseteado")

            elif key == ord("t"):
                tracker.set_target_person("tuta")
                logger.log_target_change("tuta")
                print("🎯 Siguiendo a TUTA")

            elif key == ord("l"):
                tracker.set_target_person("laura")
                logger.log_target_change("laura")
                print("🎯 Siguiendo a LAURA")

            elif key == ord("n"):
                tracker.set_target_person(None)
                logger.log_target_change(None)
                mqtt.send_position(90, 90, tracking=False)
                print("⏸️ Sin objetivo")

            elif key == ord("h"):
                print_controls()

            # Mostrar stats cada 100 frames
            if frame_count % 100 == 0:
                print(
                    f"\n📊 FPS: {fps:.1f} | Frames: {frame_count} | MQTT: {mqtt.message_count} msgs"
                )
                if result["target_locked"]:
                    print(
                        f"🎯 Tracking: {tracker.target_person.upper()} "
                        f"({result['target_face']['confidence']*100:.1f}%) "
                        f"Dist: {result['distance_to_center']:.0f}px"
                    )

    except KeyboardInterrupt:
        print("\n⚠️ Interrumpido por usuario")

    finally:
        print("🛑 Cerrando sistema...")
        camera.stop()
        mqtt.send_position(90, 90, tracking=False)  # Centrar antes de cerrar
        mqtt.close()
        if esp32.connected:
            esp32.center_servos()
            esp32.close()
        cv2.destroyAllWindows()
        print("✅ Sistema cerrado correctamente")


if __name__ == "__main__":
    main()
