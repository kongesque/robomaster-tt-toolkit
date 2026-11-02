"""Follow a target with the drone camera.

Target left/right of centre -> rotate. Above/below -> climb/descend.
Smaller/bigger than at first -> forward/back. Lost -> hover.
PID turns "how far off" into a speed: further off = faster.
Keys: t takeoff, l land, q quit.
"""
from kit import *

# ======== CHANGE HERE ========
finder = Faces()          # Faces()  Hands()  Body()  Markers()  or  Color("red")
TAKEOFF_UP = 50           # cm climb after takeoff so the camera sees you (0 = none)
FOLLOW_DISTANCE = True    # False = only turn and climb, no forward/back
# ==============================

with Drone() as d:
    cam = Camera("drone", d, mirror=False, size=(640, 480))
    yaw_pid, ud_pid, fb_pid = PID(0.4, 0.4), PID(0.5, 0.3), PID(0.8, 0.3)  # shaking? lower the first number
    keep = None         # target size to hold
    was_flying = False
    while True:
        frame = cam.read()
        h, w = frame.shape[:2]
        target = finder.read(frame)

        # Climb once, right after takeoff
        if d.flying and not was_flying and TAKEOFF_UP:
            d.t.move_up(TAKEOFF_UP)
        was_flying = d.flying

        yaw = ud = fb = 0  # stays 0 = hover if target is lost
        if target:
            cv2.circle(frame, (target.cx, target.cy), 6, (0, 255, 0), -1)
            if d.flying and keep is None:
                keep = target.size
            yaw = yaw_pid(target.cx - w // 2)  # right of centre = turn right
            ud = ud_pid(h // 2 - target.cy)    # image y = 0 is the top; above centre = climb
            if FOLLOW_DISTANCE and keep:
                fb = fb_pid(keep - target.size)  # looks smaller = too far = go forward
            d.show(CHECK)
            d.led(GREEN)
        else:
            for pid in (yaw_pid, ud_pid, fb_pid):
                pid.reset()
            d.show(BLANK)
            d.led(RED)
        d.rc(0, fb, ud, yaw)

        if screen(frame, d, f"yaw {yaw} ud {ud} fb {fb}" if target else "searching") == "q":
            break
