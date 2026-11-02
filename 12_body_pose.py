"""Control with your whole body: raise or stretch your arms.

Stand back so your shoulders and arms are in view. Arms down = hover.
Keys: t takeoff, l land, q quit.
"""
from kit import *

# ======== CHANGE HERE ========
CAM = DEFAULT_CAM  # webcam, or run with --dronecam
S = 30

ACTIONS = {
    # pose        (lr, fb, ud, yaw)   matrix       top LED
    "BOTH_UP":    ((0, 0, S, 0),      ARROW_UP,    GREEN),
    "BOTH_OUT":   ((0, 0, -S, 0),     ARROW_DOWN,  GREEN),
    "LEFT_UP":    ((-S, 0, 0, 0),     ARROW_LEFT,  GREEN),
    "RIGHT_UP":   ((S, 0, 0, 0),      ARROW_RIGHT, GREEN),
    "LEFT_OUT":   ((0, 0, 0, -40),    "L",         GREEN),
    "RIGHT_OUT":  ((0, 0, 0, 40),     "R",         GREEN),
    "DOWN":       ((0, 0, 0, 0),      BLANK,       OFF),
}
# ==============================

with Drone() as d:
    cam = Camera(CAM, d)
    bodies = Body()
    hold = Hold(0.4)
    while True:
        frame = cam.read()
        body = bodies.read(frame)
        pose = hold(body.pose if body else None)
        rc, picture, color = ACTIONS.get(pose, ACTIONS["DOWN"])  # no person = hover
        if CAM == "drone":
            rc, picture = swap_lr(rc, picture)
        d.rc(*rc)
        d.show(picture)
        d.led(color)
        if screen(frame, d, pose or "no pose") == "q":
            break
