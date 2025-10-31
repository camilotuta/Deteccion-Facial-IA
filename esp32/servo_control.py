# cSpell: disable
# pylint: disable=all
# ruff: noqa

from machine import Pin, PWM
from config import SERVO_CONFIG


class ServoController:
    def __init__(self):
        self.pan = PWM(Pin(SERVO_CONFIG["pan_pin"]), freq=50)
        self.tilt = PWM(Pin(SERVO_CONFIG["tilt_pin"]), freq=50)

    def _angle_to_duty(self, angle):
        """Convertir ángulo a duty cycle"""

        min_duty = 26
        max_duty = 128
        duty = int(min_duty + (angle / 180.0) * (max_duty - min_duty))
        return duty

    def move_to(self, pan_angle, tilt_angle):
        """Mover servos"""
        self.pan.duty(self._angle_to_duty(pan_angle))
        self.tilt.duty(self._angle_to_duty(tilt_angle))

    def center(self):
        """Centrar servos"""
        self.move_to(SERVO_CONFIG["pan_center"], SERVO_CONFIG["tilt_center"])
