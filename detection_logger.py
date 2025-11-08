# cSpell: disable
# pylint: disable=all
# ruff: noqa

import time
from datetime import datetime


class DetectionLogger:
    """Logger para registrar detecciones en tiempo real"""

    def __init__(self, log_file="detections_log.txt"):
        self.log_file = log_file
        self.last_log_time = time.time()
        self.log_interval = 1.0  # Segundos entre logs

        # Inicializar archivo de log
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write(
                f"LOG DE DETECCIONES - Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            f.write("=" * 80 + "\n\n")

    def log_detections(self, detected_faces, target_face=None, target_person=None):
        """Registrar detecciones en el archivo de log"""
        current_time = time.time()

        # Solo registrar cada X segundos para no saturar
        if current_time - self.last_log_time < self.log_interval:
            return

        self.last_log_time = current_time
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"\n[{timestamp}] {'='*60}\n")

            if detected_faces:
                f.write(f"📸 Personas detectadas: {len(detected_faces)}\n")
                f.write("-" * 60 + "\n")

                for i, face in enumerate(detected_faces, 1):
                    person_name = (
                        face["class_name"] if face["class_name"] else "desconocido"
                    )
                    confidence_percent = face["confidence"] * 100

                    status = ""
                    if target_face and face == target_face:
                        status = " ← SIGUIENDO"

                    f.write(
                        f"  Persona #{i}: {person_name.upper()} - {confidence_percent:.2f}%{status}\n"
                    )
                    f.write(f"    Posición: {face['center']}\n")

                if target_face:
                    f.write(f"\n🎯 Objetivo actual: {target_person.upper()}\n")
                    f.write(f"   Confianza: {target_face['confidence']*100:.2f}%\n")
                else:
                    if target_person:
                        f.write(
                            f"\n🔍 Buscando: {target_person.upper()} (ninguno con >90%)\n"
                        )
                    else:
                        f.write(f"\n⏸️  Sin objetivo seleccionado\n")
            else:
                f.write("❌ No se detectaron personas\n")

    def log_target_change(self, new_target):
        """Registrar cambio de objetivo"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"\n[{timestamp}] ⚡ CAMBIO DE OBJETIVO\n")
            if new_target:
                f.write(f"    Nuevo objetivo: {new_target.upper()}\n")
            else:
                f.write(f"    Sin objetivo (modo observación)\n")
