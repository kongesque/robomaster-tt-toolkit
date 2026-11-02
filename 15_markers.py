"""Show an ArUco marker or QR code: the drone runs the action for it, once.

Keys are ArUco ids ("7") or QR text ("left"). Unknown ones scroll on the matrix.
Keys: t takeoff, l land, q quit.
"""
from kit import *

# ======== CHANGE HERE ========
CAM = DEFAULT_CAM  # webcam, or run with --dronecam
DIST = 40          # cm

ACTIONS = {
    # marker     move                                picture
    "0":     (lambda d: d.t.move_up(DIST),           ARROW_UP),
    "1":     (lambda d: d.t.move_down(DIST),         ARROW_DOWN),
    "2":     (lambda d: d.t.move_left(DIST),         ARROW_LEFT),
    "3":     (lambda d: d.t.move_right(DIST),        ARROW_RIGHT),
    "turn":  (lambda d: d.t.rotate_clockwise(90),    "T"),
    "land":  (lambda d: d.land(),                    RED_X),
}
# ==============================

with Drone() as d:
    cam = Camera(CAM, d, mirror=False)  # a mirrored code can't be read
    markers = Markers()
    hold = Hold(0.3)
    done = None  # last marker that ran. Hide it to use the same one again
    while True:
        frame = cam.read()
        found = markers.read(frame)
        value = hold(found.value if found else None)
        d.rc()  # hover while waiting

        if value is None:
            done = None
        elif value != done:
            done = value
            if value in ACTIONS:
                move, picture = ACTIONS[value]
                d.show(picture)
                if d.flying:
                    move(d)
            else:
                d.scroll(value)
        if screen(frame, d, f"marker {value}") == "q":
            break
