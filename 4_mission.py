"""Autonomous flight: takes off, runs STEPS in order, lands.

Starts by itself, so clear the space first.
Distances 20-500 cm. Degrees 1-360.
"""
from kit import *

# ======== CHANGE HERE ========
SIDE = 60  # square side in cm
STEPS = [
    ("up", 30),
    ("forward", SIDE), ("cw", 90),
    ("forward", SIDE), ("cw", 90),
    ("forward", SIDE), ("cw", 90),
    ("forward", SIDE), ("cw", 90),
    # also: ("back", 50) ("left", 50) ("right", 50) ("down", 30) ("ccw", 90)
    #       ("flip", "f")  f/b/l/r    ("wait", 2)
]
# ==============================

# Picture for each action. Others show CHECK.
PICTURES = {"up": ARROW_UP, "forward": ARROW_UP, "down": ARROW_DOWN, "back": ARROW_DOWN,
            "left": ARROW_LEFT, "right": ARROW_RIGHT}

with Drone() as d:  # lands automatically at the end
    d.takeoff()
    for action, value in STEPS:
        print("STEP", action, value)
        d.show(PICTURES.get(action, CHECK))
        d.led(GREEN)
        # Each command waits until the drone finishes
        if action == "cw":
            d.t.rotate_clockwise(value)
        elif action == "ccw":
            d.t.rotate_counter_clockwise(value)
        elif action == "flip":
            d.t.flip(value)
        elif action == "wait":
            time.sleep(value)
        else:
            d.t.move(action, value)
    d.show(SMILE)
