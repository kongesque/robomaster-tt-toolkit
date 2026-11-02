"""Steer by moving your hand around the screen.

Hand in the centre box = hover. Outside it = move that way. Fist = hover.
Keys: t takeoff, l land, q quit.
"""
from kit import *

# ======== CHANGE HERE ========
CAM = DEFAULT_CAM  # webcam, or run with --dronecam
S = 30             # speed
BOX = 0.3          # centre box size, 0-1 of the screen
# ==============================

with Drone() as d:
    cam = Camera(CAM, d)
    hands = Hands()
    while True:
        frame = cam.read()
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (int(w * (1 - BOX) / 2), int(h * (1 - BOX) / 2)),
                      (int(w * (1 + BOX) / 2), int(h * (1 + BOX) / 2)), (255, 255, 255), 1)
        hand = hands.read(frame)

        rc, picture, color = (0, 0, 0, 0), BLANK, OFF
        if hand and hand.gesture != "FIST":
            # Distance from the screen centre: -1 to 1 (image y = 0 is the top)
            dx = (hand.cx - w / 2) / (w / 2)
            dy = (h / 2 - hand.cy) / (h / 2)
            if max(abs(dx), abs(dy)) > BOX:  # outside the box: use the bigger direction
                color = GREEN
                if abs(dx) > abs(dy):
                    rc, picture = ((S, 0, 0, 0), ARROW_RIGHT) if dx > 0 else ((-S, 0, 0, 0), ARROW_LEFT)
                else:
                    rc, picture = ((0, 0, S, 0), ARROW_UP) if dy > 0 else ((0, 0, -S, 0), ARROW_DOWN)

        if CAM == "drone":
            rc, picture = swap_lr(rc, picture)
        d.rc(*rc)
        d.show(picture)
        d.led(color)
        if screen(frame, d, f"rc {rc}") == "q":
            break
