"""Count fingers, show the number on the matrix, run an action for it.

Hold a number for 0.8 s. Each number runs once, so show a different one to repeat.
Keys: t takeoff, l land, q quit.
"""
from kit import *

# ======== CHANGE HERE ========
CAM = DEFAULT_CAM  # webcam, or run with --dronecam


def on_count(d, n):
    """Action for each number. d.t = full djitellopy, see README."""
    if n == 5:
        d.takeoff()
    elif n == 0:
        d.land()
    elif d.flying and n == 1:
        d.t.move_up(30)
    elif d.flying and n == 2:
        d.t.rotate_clockwise(90)
    elif d.flying and n == 3:
        d.t.flip_forward()
# ==============================

with Drone() as d:
    cam = Camera(CAM, d)
    hands = Hands()
    hold = Hold(0.8)  # hold the count this long before it acts
    done = None       # last number that ran
    while True:
        frame = cam.read()
        hand = hands.read(frame)
        n = hold(hand.fingers if hand else None)
        d.rc()  # keeps the drone hovering while waiting
        if n is not None and n != done:  # new steady number (0 counts too)
            done = n
            d.show(str(n))
            on_count(d, n)
        if screen(frame, d, f"fingers: {n}") == "q":
            break
