"""Two hands at once: each side of the screen has its own controls.

Point with each hand. Both fists = land.
Keys: t takeoff, l land, q quit.
"""
from kit import *

# ======== CHANGE HERE ========
CAM = DEFAULT_CAM  # webcam, or run with --dronecam
S = 30
#                   (lr, fb, ud, yaw)
LEFT_HAND = {"UP":    (0, 0, S, 0),     # height
             "DOWN":  (0, 0, -S, 0),
             "LEFT":  (0, 0, 0, -40),   # rotate
             "RIGHT": (0, 0, 0, 40)}
RIGHT_HAND = {"UP":    (0, S, 0, 0),    # forward / back
              "DOWN":  (0, -S, 0, 0),
              "LEFT":  (-S, 0, 0, 0),   # left / right
              "RIGHT": (S, 0, 0, 0)}
PICTURES = {"UP": ARROW_UP, "DOWN": ARROW_DOWN, "LEFT": ARROW_LEFT, "RIGHT": ARROW_RIGHT}
# ==============================

with Drone() as d:
    cam = Camera(CAM, d)
    hands = Hands()
    hold_left, hold_right = Hold(), Hold()
    while True:
        frame = cam.read()
        w = frame.shape[1]
        seen = hands.read_all(frame)
        left = [q.gesture for q in seen if q.cx < w / 2]
        right = [q.gesture for q in seen if q.cx >= w / 2]
        g1 = hold_left(left[0] if left else None)
        g2 = hold_right(right[0] if right else None)

        if g1 == "FIST" and g2 == "FIST":
            d.land()

        # Add both hands, so moving and turning work together
        a, b = LEFT_HAND.get(g1, (0, 0, 0, 0)), RIGHT_HAND.get(g2, (0, 0, 0, 0))
        rc = tuple(x + y for x, y in zip(a, b))
        picture = PICTURES.get(g2) or PICTURES.get(g1) or BLANK
        if CAM == "drone":
            rc, picture = swap_lr(rc, picture)
        d.rc(*rc)
        d.show(picture)
        d.led(GREEN if any(rc) else OFF)
        if screen(frame, d, f"left {g1}  right {g2}") == "q":
            break
