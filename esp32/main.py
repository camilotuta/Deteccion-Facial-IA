# cSpell: disable
# pylint: disable=all
# ruff: noqa

import sys
import json
from servo_control import ServoController

servo = ServoController()

print("ESP32 Face Tracking - Ready")
servo.center()

while True:
    try:

        if sys.stdin in sys.stdin:
            line = input()

            if line:

                data = json.loads(line)
                pan = data.get("pan", 90)
                tilt = data.get("tilt", 90)

                servo.move_to(pan, tilt)

    except Exception as e:
        print(f"Error: {e}")
