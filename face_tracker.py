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
)


class FaceTracker:
    def __init__(self):

        print("🔄 Cargando modelo de detección facial...")
        self.model = get_model(model_id=ROBOFLOW_CONFIG["model_id"])
        print("✅ Modelo cargado")

        self.frame_center = (CAMERA_CONFIG["width"] // 2, CAMERA_CONFIG["height"] // 2)

        self.pid_pan = PIDController(**PID_CONFIG["pan"])
        self.pid_tilt = PIDController(**PID_CONFIG["tilt"])

        self.current_pan = SERVO_CONFIG["pan_center"]
        self.current_tilt = SERVO_CONFIG["tilt_center"]
        self.face_detected = False
        self.last_face_center = None

        self.smoothing_factor = TRACKING_CONFIG["smoothing_factor"]

        self.box_annotator = sv.BoxAnnotator()
        self.label_annotator = sv.LabelAnnotator()

    def detect_face(self, frame):
        """Detectar rostro usando el modelo de Roboflow"""
        try:

            results = self.model.infer(frame)[0]

            detections = sv.Detections.from_inference(results)

            mask = detections.confidence >= ROBOFLOW_CONFIG["confidence"]
            detections = detections[mask]

            if len(detections) == 0:
                return None, None

            areas = (detections.xyxy[:, 2] - detections.xyxy[:, 0]) * (
                detections.xyxy[:, 3] - detections.xyxy[:, 1]
            )
            largest_idx = np.argmax(areas)

            x1, y1, x2, y2 = detections.xyxy[largest_idx]

            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)

            face_info = {
                "bbox": (int(x1), int(y1), int(x2 - x1), int(y2 - y1)),
                "center": (center_x, center_y),
                "area": areas[largest_idx],
                "confidence": detections.confidence[largest_idx],
            }

            return face_info, detections

        except Exception as e:
            print(f"Error en detección: {e}")
            return None, None

    def calculate_servo_angles(self, face_center):
        """Calcular ángulos de servos basado en posición del rostro"""
        error_x = face_center[0] - self.frame_center[0]
        error_y = face_center[1] - self.frame_center[1]

        if abs(error_x) < DEADZONE["x"]:
            error_x = 0
        if abs(error_y) < DEADZONE["y"]:
            error_y = 0

        pan_adjustment = self.pid_pan.update(error_x)
        tilt_adjustment = self.pid_tilt.update(error_y)

        pan_adjustment = np.clip(
            pan_adjustment, -SERVO_CONFIG["max_speed"], SERVO_CONFIG["max_speed"]
        )
        tilt_adjustment = np.clip(
            tilt_adjustment, -SERVO_CONFIG["max_speed"], SERVO_CONFIG["max_speed"]
        )

        new_pan = self.current_pan - pan_adjustment
        new_tilt = self.current_tilt + tilt_adjustment

        new_pan = np.clip(new_pan, *SERVO_CONFIG["pan_range"])
        new_tilt = np.clip(new_tilt, *SERVO_CONFIG["tilt_range"])

        new_pan = (
            self.current_pan + (new_pan - self.current_pan) * self.smoothing_factor
        )
        new_tilt = (
            self.current_tilt + (new_tilt - self.current_tilt) * self.smoothing_factor
        )

        return new_pan, new_tilt

    def process_frame(self, frame, frame_count):
        """Procesar frame y retornar información de seguimiento"""
        result = {
            "face_detected": False,
            "face_info": None,
            "detections": None,
            "pan_angle": self.current_pan,
            "tilt_angle": self.current_tilt,
            "error": (0, 0),
        }

        if frame_count % TRACKING_CONFIG["detection_interval"] == 0:
            face_info, detections = self.detect_face(frame)

            if face_info:
                self.face_detected = True
                self.last_face_center = face_info["center"]
                result["face_detected"] = True
                result["face_info"] = face_info
                result["detections"] = detections

                pan, tilt = self.calculate_servo_angles(face_info["center"])

                self.current_pan = pan
                self.current_tilt = tilt

                result["pan_angle"] = pan
                result["tilt_angle"] = tilt

                error_x = face_info["center"][0] - self.frame_center[0]
                error_y = face_info["center"][1] - self.frame_center[1]
                result["error"] = (error_x, error_y)
            else:
                self.face_detected = False

        return result

    def draw_annotations(self, frame, result, fps):
        """Dibujar anotaciones en el frame"""
        annotated = frame.copy()

        if result["face_detected"] and result["detections"] is not None:

            annotated = self.box_annotator.annotate(
                scene=annotated, detections=result["detections"]
            )

            labels = [f"Face {conf:.2f}" for conf in result["detections"].confidence]
            annotated = self.label_annotator.annotate(
                scene=annotated, detections=result["detections"], labels=labels
            )

            if result["face_info"]:
                cv2.circle(annotated, result["face_info"]["center"], 5, (0, 0, 255), -1)

                cv2.line(
                    annotated,
                    self.frame_center,
                    result["face_info"]["center"],
                    (0, 255, 0),
                    2,
                )

                error_x, error_y = result["error"]
                confidence = result["face_info"]["confidence"]
                cv2.putText(
                    annotated,
                    f"Error: X={error_x:.0f} Y={error_y:.0f} | Conf: {confidence:.2f}",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )

        cv2.drawMarker(
            annotated, self.frame_center, (0, 255, 255), cv2.MARKER_CROSS, 20, 2
        )

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

        status = "TRACKING" if result["face_detected"] else "SEARCHING"
        color = (0, 255, 0) if result["face_detected"] else (0, 0, 255)
        cv2.putText(
            annotated, status, (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
        )

        return annotated

    def reset(self):
        """Resetear tracking"""
        self.pid_pan.reset()
        self.pid_tilt.reset()
        self.last_face_center = None
