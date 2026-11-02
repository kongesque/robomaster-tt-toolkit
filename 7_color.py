"""See a colour: show its letter, set the LED, run its speeds.

Several colours visible = the biggest wins. None = hover.
Keys: t takeoff, l land, q quit.
"""
from kit import *

# ======== CHANGE HERE ========
CAM = "webcam"  # "webcam" or "drone"
#          finder          letter  LED      rc while seen (lr, fb, ud, yaw)
RULES = [(Color("red"),    "R",    RED,     (0, 0, 0, 0)),
         (Color("green"),  "G",    GREEN,   (0, 0, 20, 0)),
         (Color("blue"),   "B",    BLUE,    (0, 0, -20, 0))]
# ==============================

with Drone() as d:
    cam = Camera(CAM, d)
    while True:
        frame = cam.read()
        # Search for every colour, keep the ones found
        seen = [(r, r[0].read(frame)) for r in RULES]
        seen = [(r, t) for r, t in seen if t]
        if seen:
            # Take the row of the biggest one
            (_, letter, led, rc), _ = max(seen, key=lambda s: s[1].size)
            d.show(letter)
            d.led(led)
            d.rc(*rc)
        else:
            letter = "none"
            d.show(BLANK)
            d.led(OFF)
            d.rc()
        if screen(frame, d, letter) == "q":
            break
