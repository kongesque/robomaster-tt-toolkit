"""Keyboard flying with arrows, LED, and a stop at walls.

W/S forward/back  A/D left/right  UP/DOWN height  LEFT/RIGHT rotate
E takeoff  Q land  SPACE hover  ESC quit
"""
from kit import *

# ======== CHANGE HERE ========
S = 50         # move speed
UD = 30        # up/down speed
YAW = 40       # rotate speed
WALL = 500     # mm: stop forward and show red X
# ==============================

with Drone() as d:
    k = Keys()
    while not k("ESCAPE"):
        # Held key = 1, released = 0. D gives +S (right), A gives -S (left).
        lr = (k("d") - k("a")) * S
        fb = (k("w") - k("s")) * S
        ud = (k("UP") - k("DOWN")) * UD
        yaw = (k("RIGHT") - k("LEFT")) * YAW
        if k("SPACE"):
            lr = fb = ud = yaw = 0

        # Wall ahead: block forward only, so you can still back away
        close = d.wall(WALL)
        if close and fb > 0:
            fb = 0
        d.rc(lr, fb, ud, yaw)

        # tap = once per press
        if k.tap("e"):
            d.takeoff()
        if k.tap("q"):
            d.land()

        # Red X first, otherwise an arrow for the movement
        if close:
            d.show(RED_X)
            d.led(RED)
        elif fb > 0 or ud > 0:
            d.show(ARROW_UP)
            d.led(GREEN)
        elif fb < 0 or ud < 0:
            d.show(ARROW_DOWN)
            d.led(GREEN)
        elif lr < 0:
            d.show(ARROW_LEFT)
            d.led(GREEN)
        elif lr > 0:
            d.show(ARROW_RIGHT)
            d.led(GREEN)
        k.pause()
