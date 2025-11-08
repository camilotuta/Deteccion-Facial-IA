# cSpell: disable
# pylint: disable=all
# ruff: noqa

"""
Script para visualizar estadísticas del log de detecciones
Ejecutar: python view_stats.py
"""

import re
from collections import defaultdict
from datetime import datetime


def analyze_log(log_file="detections_log.txt"):
    """Analizar el archivo de log y mostrar estadísticas"""

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo {log_file}")
        print("💡 Ejecuta el sistema primero para generar el log")
        return

    # Extraer todas las detecciones
    tuta_detections = re.findall(r"TUTA - (\d+\.\d+)%", content)
    laura_detections = re.findall(r"LAURA - (\d+\.\d+)%", content)

    # Convertir a float
    tuta_confidences = [float(x) for x in tuta_detections]
    laura_confidences = [float(x) for x in laura_detections]

    print("\n" + "=" * 70)
    print("📊 ESTADÍSTICAS DE DETECCIÓN")
    print("=" * 70)

    # Estadísticas de TUTA
    if tuta_confidences:
        print(f"\n👤 TUTA:")
        print(f"   Total detecciones: {len(tuta_confidences)}")
        print(
            f"   Confianza promedio: {sum(tuta_confidences)/len(tuta_confidences):.2f}%"
        )
        print(f"   Confianza máxima: {max(tuta_confidences):.2f}%")
        print(f"   Confianza mínima: {min(tuta_confidences):.2f}%")

        # Contar detecciones por rango de confianza
        high_conf = sum(1 for x in tuta_confidences if x >= 90)
        med_conf = sum(1 for x in tuta_confidences if 70 <= x < 90)
        low_conf = sum(1 for x in tuta_confidences if x < 70)

        print(f"\n   Distribución:")
        print(
            f"   ✅ Alta (≥90%): {high_conf} ({high_conf/len(tuta_confidences)*100:.1f}%)"
        )
        print(
            f"   ⚠️  Media (70-89%): {med_conf} ({med_conf/len(tuta_confidences)*100:.1f}%)"
        )
        print(
            f"   ❌ Baja (<70%): {low_conf} ({low_conf/len(tuta_confidences)*100:.1f}%)"
        )
    else:
        print(f"\n👤 TUTA: No detectado")

    # Estadísticas de LAURA
    if laura_confidences:
        print(f"\n👤 LAURA:")
        print(f"   Total detecciones: {len(laura_confidences)}")
        print(
            f"   Confianza promedio: {sum(laura_confidences)/len(laura_confidences):.2f}%"
        )
        print(f"   Confianza máxima: {max(laura_confidences):.2f}%")
        print(f"   Confianza mínima: {min(laura_confidences):.2f}%")

        high_conf = sum(1 for x in laura_confidences if x >= 90)
        med_conf = sum(1 for x in laura_confidences if 70 <= x < 90)
        low_conf = sum(1 for x in laura_confidences if x < 70)

        print(f"\n   Distribución:")
        print(
            f"   ✅ Alta (≥90%): {high_conf} ({high_conf/len(laura_confidences)*100:.1f}%)"
        )
        print(
            f"   ⚠️  Media (70-89%): {med_conf} ({med_conf/len(laura_confidences)*100:.1f}%)"
        )
        print(
            f"   ❌ Baja (<70%): {low_conf} ({low_conf/len(laura_confidences)*100:.1f}%)"
        )
    else:
        print(f"\n👤 LAURA: No detectado")

    # Cambios de objetivo
    target_changes = re.findall(r"CAMBIO DE OBJETIVO.*?Nuevo objetivo: (\w+)", content)
    if target_changes:
        print(f"\n🎯 Cambios de objetivo: {len(target_changes)}")
        for i, target in enumerate(target_changes, 1):
            print(f"   {i}. {target}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    analyze_log()
