"""Distance display and hold, using the front ToF sensor.

Matrix bar: taller = closer. LED: green safe, yellow close, red too close.
FLY = False only shows the distance. FLY = True takes off and holds GOAL.
Ctrl+C lands and quits.
"""
from kit import *

# ======== CHANGE HERE ========
FLY = False       # True = take off and keep GOAL from the wall
GOAL = 600        # mm. The sensor reaches about 1200
CLOSE = 800       # below this = yellow
DANGER = 400      # below this = red
MAX_SPEED = 25
# ==============================

with Drone() as d:
    pid = PID(0.2, 0.1)
    if FLY:
        d.takeoff()
    while True:
        mm = d.tof()
        in_range = mm < 1300  # 8192 = nothing seen

        d.show(bar((1300 - mm) / 150) if in_range else BLANK)
        d.led(RED if mm < DANGER else YELLOW if mm < CLOSE else GREEN)

        # Too far = forward, too close = back. Nothing seen = hover.
        fb = pid(mm - GOAL) if in_range else 0
        d.rc(fb=max(-MAX_SPEED, min(MAX_SPEED, fb)))
        print(f"{mm} mm  fb {fb}   ", end="\r", flush=True)
        time.sleep(0.05)
