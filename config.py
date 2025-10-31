# cSpell: disable
# pylint: disable=all
# ruff: noqa

CAMERA_CONFIG = {
    "index": 0,
    "width": 640,
    "height": 480,
    "fps": 30,
}


ESP32_CONFIG = {
    "port": "/dev/ttyUSB0",
    "baudrate": 115200,
    "timeout": 1,
}


SERVO_CONFIG = {
    "pan_center": 90,
    "tilt_center": 90,
    "pan_range": (0, 180),
    "tilt_range": (30, 150),
    "max_speed": 5,
}


TRACKING_CONFIG = {
    "detection_interval": 1,
    "smoothing_factor": 0.3,
}


PID_CONFIG = {
    "pan": {"kp": 0.15, "ki": 0.01, "kd": 0.08},
    "tilt": {"kp": 0.15, "ki": 0.01, "kd": 0.08},
}


DEADZONE = {"x": 20, "y": 20}
