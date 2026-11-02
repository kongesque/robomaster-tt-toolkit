"""Take a photo by gesture: 3-2-1 on the matrix, then save to photos/.

Show TRIGGER to start the countdown, or press p.
Keys: t takeoff, l land, q quit.
"""
import os

from kit import *

# ======== CHANGE HERE ========
CAM = DEFAULT_CAM  # webcam, or run with --dronecam
TRIGGER = "V_UP"   # two fingers up
COUNT = 3          # seconds
# ==============================

os.makedirs("photos", exist_ok=True)

with Drone() as d:
    cam = Camera(CAM, d)
    hands = Hands()
    hold = Hold()
    shoot_at = None  # time the photo will be taken
    while True:
        frame = cam.read()
        clean = frame.copy()  # saved photo has no drawings on it
        hand = hands.read(frame)
        g = hold(hand.gesture if hand else None)
        d.rc()  # hover while waiting

        if g == TRIGGER and shoot_at is None:
            shoot_at = time.time() + COUNT
            d.led(YELLOW)

        if shoot_at:
            left = shoot_at - time.time()
            if left > 0:
                d.show(str(math.ceil(left)))
            else:
                name = f"photos/{int(time.time())}.jpg"
                cv2.imwrite(name, clean)
                print("Saved", name)
                d.show(CHECK)
                d.led(GREEN)
                shoot_at = None

        key = screen(frame, d, g or "")
        if key == "p" and shoot_at is None:
            shoot_at = time.time() + COUNT
            d.led(YELLOW)
        if key == "q":
            break
