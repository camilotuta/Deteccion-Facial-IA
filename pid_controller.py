# cSpell: disable
# pylint: disable=all
# ruff: noqa
import time


class PIDController:
    def __init__(self, kp=1.0, ki=0.0, kd=0.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd

        self.last_error = 0
        self.integral = 0
        self.last_time = time.time()

    def update(self, error):
        """Actualizar PID y retornar corrección"""
        current_time = time.time()
        dt = current_time - self.last_time

        if dt <= 0:
            dt = 0.001

        p = self.kp * error

        self.integral += error * dt
        self.integral = max(-50, min(50, self.integral))
        i = self.ki * self.integral

        derivative = (error - self.last_error) / dt
        d = self.kd * derivative

        self.last_error = error
        self.last_time = current_time

        return p + i + d

    def reset(self):
        """Resetear PID"""
        self.last_error = 0
        self.integral = 0
        self.last_time = time.time()
