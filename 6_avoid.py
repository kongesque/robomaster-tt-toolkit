"""Fly forward alone. Wall ahead: stop, red X, turn, carry on.

Starts by itself. Ctrl+C lands early.
ToF reaches about 1.2 m, so keep WALL under 1200.
"""
from kit import *

# ======== CHANGE HERE ========
SPEED = 25
WALL = 500        # mm
TURN = 90         # degrees to turn at a wall
MAX_TURNS = 4     # land after this many walls
# ==============================

with Drone() as d:
    d.takeoff()
    turns = 0
    while turns < MAX_TURNS:
        if d.wall(WALL):
            d.rc()  # hover
            d.show(RED_X)
            d.led(RED)
            time.sleep(0.6)
            d.t.rotate_clockwise(TURN)
            turns += 1
        else:
            d.rc(fb=SPEED)
            d.show(ARROW_UP)
            d.led(GREEN)
            time.sleep(0.05)
