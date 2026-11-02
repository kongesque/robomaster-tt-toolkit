"""Hand gesture control.

Camera -> find hand -> name the gesture -> look it up in ACTIONS -> move, show, light.
No hand or unclear gesture = hover.
Keys: t takeoff, l land, q quit.
"""
from kit import *

# ======== CHANGE HERE ========
CAM = "webcam"  # "webcam" or "drone"
S = 30          # speed, 10-100

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
}
# ==============================

with Drone() as d:  # lands automatically when this block ends
    cam = Camera(CAM, d)
    hands = Hands()
    hold = Hold()  # gesture must stay 0.25 s, stops misreads
    while True:
        frame = cam.read()
        hand = hands.read(frame)
        g = hold(hand.gesture if hand else None)
        action = ACTIONS.get(g, ACTIONS["PALM"])  # no hand / unknown = hover

        if action == "TAKEOFF":
            d.takeoff()
        elif action == "LAND":
            d.land()
        else:
            rc, picture, color = action
            if CAM == "drone":  # it faces you: swap so it moves to YOUR left/right
                rc = (-rc[0], *rc[1:])
                picture = {ARROW_LEFT: ARROW_RIGHT, ARROW_RIGHT: ARROW_LEFT}.get(picture, picture)
            d.rc(*rc)
            d.show(picture)
            d.led(color)

        if screen(frame, d, g or "no gesture") == "q":  # show video, read keys
            break
