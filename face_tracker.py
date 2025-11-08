# cSpell: disable
# pylint: disable=all
# ruff: noqa

import cv2
import numpy as np
from inference import get_model
import supervision as sv
from pid_controller import PIDController
from config import (
    CAMERA_CONFIG,
    TRACKING_CONFIG,
    PID_CONFIG,
    DEADZONE,
    SERVO_CONFIG,
    ROBOFLOW_CONFIG,
    PERSON_COLORS,
)


class FaceTracker:
    def __init__(self):
        print("🔄 Cargando modelo de detección facial...")
        self.model = get_model(
            model_id=ROBOFLOW_CONFIG["model_id"], api_key=ROBOFLOW_CONFIG["api_key"]
        )
        print("✅ Modelo cargado")

        self.frame_center = (CAMERA_CONFIG["width"] // 2, CAMERA_CONFIG["height"] // 2)

        self.pid_pan = PIDController(**PID_CONFIG["pan"])
        self.pid_tilt = PIDController(**PID_CONFIG["tilt"])

        self.current_pan = SERVO_CONFIG["pan_center"]
        self.current_tilt = SERVO_CONFIG["tilt_center"]
        self.face_detected = False
        self.last_face_center = None

        self.smoothing_factor = TRACKING_CONFIG["smoothing_factor"]
        self.target_person = TRACKING_CONFIG["target_person"]
        self.tracking_confidence_threshold = ROBOFLOW_CONFIG["tracking_confidence"]

        self.box_annotator = sv.BoxAnnotator()
        self.label_annotator = sv.LabelAnnotator()

        # Para optimización
        self.frame_counter = 0
        self.frame_skip = TRACKING_CONFIG["frame_skip"]

    def set_target_person(self, person_name):
        """Establecer la persona objetivo a seguir"""
        if person_name in ["tuta", "laura", None]:
            self.target_person = person_name
            print(
                f"🎯 Objetivo establecido: {person_name if person_name else 'Ninguno'}"
            )
            return True
        return False

    def detect_faces(self, frame):
        """Detectar rostros con optimización"""
        try:
            # Reducir resolución para inferencia más rápida
            scale = 0.5
            small_frame = cv2.resize(frame, None, fx=scale, fy=scale)

            results = self.model.infer(small_frame)[0]
            detections = sv.Detections.from_inference(results)

            # Escalar detecciones de vuelta al tamaño original
            if len(detections) > 0:
                detections.xyxy = detections.xyxy / scale

            # Filtrar por confianza mínima
            mask = detections.confidence >= ROBOFLOW_CONFIG["confidence"]
            detections = detections[mask]

            if len(detections) == 0:
                return [], None

            # Procesar detecciones
            detected_faces = []
            for i in range(len(detections)):
                x1, y1, x2, y2 = detections.xyxy[i]
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                area = (x2 - x1) * (y2 - y1)

                class_name = (
                    detections.data.get("class_name", [None])[i]
                    if "class_name" in detections.data
                    else None
                )
                confidence = detections.confidence[i]

                face_info = {
                    "bbox": (int(x1), int(y1), int(x2 - x1), int(y2 - y1)),
                    "center": (center_x, center_y),
                    "area": area,
                    "confidence": confidence,
                    "class_name": class_name,
                    "index": i,
                }

                detected_faces.append(face_info)

            return detected_faces, detections

        except Exception as e:
            print(f"Error en detección: {e}")
            return [], None

    def select_target_face(self, detected_faces):
        """Seleccionar rostro objetivo con prioridad por confianza y tamaño"""
        if not detected_faces:
            return None

        if self.target_person is None:
            return None

        matching_faces = []
        for face in detected_faces:
            if (
                face["class_name"]
                and face["class_name"].lower() == self.target_person.lower()
            ):
                if face["confidence"] >= self.tracking_confidence_threshold:
                    matching_faces.append(face)

        if not matching_faces:
            return None

        # Ordenar por confianza primero, luego por tamaño
        matching_faces.sort(key=lambda x: (x["confidence"], x["area"]), reverse=True)

        return matching_faces[0]

    def calculate_servo_angles(self, face_center):
        """Calcular ángulos con mejor centrado"""
        error_x = face_center[0] - self.frame_center[0]
        error_y = face_center[1] - self.frame_center[1]

        # Aplicar zona muerta más pequeña
        if abs(error_x) < DEADZONE["x"]:
            error_x = 0
        if abs(error_y) < DEADZONE["y"]:
            error_y = 0

        # PID mejorado
        pan_adjustment = self.pid_pan.update(error_x)
        tilt_adjustment = self.pid_tilt.update(error_y)

        # Limitar velocidad máxima
        pan_adjustment = np.clip(
            pan_adjustment, -SERVO_CONFIG["max_speed"], SERVO_CONFIG["max_speed"]
        )
        tilt_adjustment = np.clip(
            tilt_adjustment, -SERVO_CONFIG["max_speed"], SERVO_CONFIG["max_speed"]
        )

        # Calcular nuevos ángulos
        new_pan = self.current_pan - pan_adjustment
        new_tilt = self.current_tilt + tilt_adjustment

        # Limitar rangos
        new_pan = np.clip(new_pan, *SERVO_CONFIG["pan_range"])
        new_tilt = np.clip(new_tilt, *SERVO_CONFIG["tilt_range"])

        # Suavizado mejorado
        new_pan = (
            self.current_pan + (new_pan - self.current_pan) * self.smoothing_factor
        )
        new_tilt = (
            self.current_tilt + (new_tilt - self.current_tilt) * self.smoothing_factor
        )

        return new_pan, new_tilt

    def process_frame(self, frame, frame_count):
        """Procesar frame optimizado"""
        result = {
            "target_locked": False,
            "target_face": None,
            "all_faces": [],
            "detections": None,
            "pan_angle": self.current_pan,
            "tilt_angle": self.current_tilt,
            "error": (0, 0),
            "distance_to_center": 0,
        }

        # Detectar en cada frame para mejor seguimiento
        if frame_count % TRACKING_CONFIG["detection_interval"] == 0:
            detected_faces, detections = self.detect_faces(frame)

            result["all_faces"] = detected_faces
            result["detections"] = detections

            if detected_faces:
                # Seleccionar objetivo
                target_face = self.select_target_face(detected_faces)

                if target_face:
                    self.face_detected = True
                    self.last_face_center = target_face["center"]
                    result["target_locked"] = True
                    result["target_face"] = target_face

                    # Calcular distancia al centro
                    error_x = target_face["center"][0] - self.frame_center[0]
                    error_y = target_face["center"][1] - self.frame_center[1]
                    distance = np.sqrt(error_x**2 + error_y**2)
                    result["distance_to_center"] = distance
                    result["error"] = (error_x, error_y)

                    # Calcular ángulos
                    pan, tilt = self.calculate_servo_angles(target_face["center"])

                    self.current_pan = pan
                    self.current_tilt = tilt

                    result["pan_angle"] = pan
                    result["tilt_angle"] = tilt

                else:
                    self.face_detected = False
            else:
                self.face_detected = False

        return result

    def draw_annotations(self, frame, result, fps):
        """Dibujar anotaciones optimizadas"""
        annotated = frame.copy()

        # Dibujar todas las caras
        if result["all_faces"]:
            for face in result["all_faces"]:
                x, y, w, h = face["bbox"]
                class_name = face["class_name"] if face["class_name"] else "unknown"
                confidence = face["confidence"]
                confidence_percent = confidence * 100

                color = PERSON_COLORS.get(class_name.lower(), PERSON_COLORS["unknown"])
                thickness = (
                    3
                    if (result["target_locked"] and face == result["target_face"])
                    else 2
                )

                # Rectángulo
                cv2.rectangle(annotated, (x, y), (x + w, y + h), color, thickness)

                # Etiqueta
                label = f"{class_name.upper()}: {confidence_percent:.1f}%"
                if result["target_locked"] and face == result["target_face"]:
                    label = f">>> {label} <<<"

                (text_w, text_h), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                )
                cv2.rectangle(
                    annotated, (x, y - text_h - 10), (x + text_w, y), color, -1
                )
                cv2.putText(
                    annotated,
                    label,
                    (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )

                # Barra de confianza
                bar_width = w
                bar_height = 8
                filled_width = int((bar_width * confidence))

                cv2.rectangle(
                    annotated,
                    (x, y + h + 5),
                    (x + bar_width, y + h + 5 + bar_height),
                    (50, 50, 50),
                    -1,
                )

                if confidence_percent >= 85:
                    bar_color = (0, 255, 0)
                elif confidence_percent >= 70:
                    bar_color = (0, 255, 255)
                else:
                    bar_color = (0, 0, 255)

                cv2.rectangle(
                    annotated,
                    (x, y + h + 5),
                    (x + filled_width, y + h + 5 + bar_height),
                    bar_color,
                    -1,
                )

                # Centro
                cv2.circle(annotated, face["center"], 5, color, -1)

        # Línea de seguimiento
        if result["target_locked"] and result["target_face"]:
            cv2.line(
                annotated,
                self.frame_center,
                result["target_face"]["center"],
                (0, 255, 255),
                2,
            )

            # Distancia al centro
            cv2.putText(
                annotated,
                f"Dist: {result['distance_to_center']:.0f}px",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

        # Centro del frame
        cv2.drawMarker(
            annotated, self.frame_center, (0, 255, 255), cv2.MARKER_CROSS, 20, 2
        )

        # Zona muerta
        cv2.rectangle(
            annotated,
            (
                self.frame_center[0] - DEADZONE["x"],
                self.frame_center[1] - DEADZONE["y"],
            ),
            (
                self.frame_center[0] + DEADZONE["x"],
                self.frame_center[1] + DEADZONE["y"],
            ),
            (255, 255, 0),
            1,
        )

        # Info del sistema
        cv2.putText(
            annotated,
            f"FPS: {fps:.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

        cv2.putText(
            annotated,
            f"Pan: {result['pan_angle']:.1f}° Tilt: {result['tilt_angle']:.1f}°",
            (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        target_text = (
            f"Target: {self.target_person.upper()}"
            if self.target_person
            else "No Target"
        )
        cv2.putText(
            annotated,
            target_text,
            (10, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        status = "🎯 TRACKING" if result["target_locked"] else "🔍 SEARCHING"
        color = (0, 255, 0) if result["target_locked"] else (0, 165, 255)
        cv2.putText(
            annotated, status, (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
        )

        cv2.putText(
            annotated,
            f"Faces: {len(result['all_faces'])}",
            (10, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        return annotated

    def reset(self):
        """Reset tracking"""
        self.pid_pan.reset()
        self.pid_tilt.reset()
        self.last_face_center = None
