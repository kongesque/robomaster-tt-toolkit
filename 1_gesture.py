"""Hand gesture control.

Camera -> find hand -> name the gesture -> look it up in ACTIONS -> move, show, light.
No hand or unclear gesture = hover.
Keys: t takeoff, l land, q quit.
"""
from kit import *

# ======== CHANGE HERE ========
CAM = DEFAULT_CAM  # webcam, or run with --dronecam
S = 30            # speed, 10-100
WALL = 0          # 500 = stop forward at 500 mm and show red X. 0 = off

ACTIONS = {
    # gesture    (lr, fb, ud, yaw)  matrix        top LED
    "UP":        ((0, 0, S, 0),     ARROW_UP,     GREEN),
    "DOWN":      ((0, 0, -S, 0),    ARROW_DOWN,   GREEN),
    "LEFT":      ((-S, 0, 0, 0),    ARROW_LEFT,   GREEN),
    "RIGHT":     ((S, 0, 0, 0),     ARROW_RIGHT,  GREEN),
    "V_UP":      ((0, S, 0, 0),     "F",          GREEN),  # two fingers up = forward
    "V_DOWN":    ((0, -S, 0, 0),    "B",          GREEN),  # two fingers down = back
    "V_LEFT":    ((0, 0, 0, -40),   "L",          GREEN),  # two fingers left = rotate
    "V_RIGHT":   ((0, 0, 0, 40),    "R",          GREEN),
    "PALM":      ((0, 0, 0, 0),     BLANK,        OFF),    # hover
    "FIST":      ((0, 0, 0, 0),     RED_X,        RED),    # stop
    # "THUMB_UP": "TAKEOFF",   # uncomment to take off / land by gesture
    # "THUMB_DOWN": "LAND",
    # "V_LEFT": lambda d: d.t.flip_left(),   # a function runs once per gesture
}
# ==============================

with Drone() as d:  # lands automatically when this block ends
    cam = Camera(CAM, d)
    hands = Hands()
    hold = Hold()  # gesture must stay 0.25 s, stops misreads
    last = None    # previous gesture, so a function runs once
    while True:
        frame = cam.read()
        hand = hands.read(frame)
        g = hold(hand.gesture if hand else None)
        action = ACTIONS.get(g, ACTIONS["PALM"])  # no hand / unknown = hover

        if action == "TAKEOFF":
            d.takeoff()
        elif action == "LAND":
            d.land()
        elif callable(action):
            if g != last:
                action(d)
        else:
            rc, picture, color = action
            if CAM == "drone":  # it faces you: swap so it moves to YOUR left/right
                rc, picture = swap_lr(rc, picture)
            if WALL and d.wall(WALL):  # block forward only, you can still back away
                rc = (rc[0], min(rc[1], 0), rc[2], rc[3])
                picture, color = RED_X, RED
            d.rc(*rc)
            d.show(picture)
            d.led(color)

        last = g
        if screen(frame, d, g or "no gesture") == "q":  # show video, read keys
            break
