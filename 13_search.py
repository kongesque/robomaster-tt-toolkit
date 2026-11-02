"""Search: take off, spin until the target appears, fly to it, land.

Lost target = spin again. Stops at a wall or after TIME_LIMIT.
Starts by itself, so clear the space first. q lands.
"""
from kit import *

# ======== CHANGE HERE ========
finder = Color("red")   # Faces()  Hands()  Body()  Markers()  or  Color("red")
SPIN = 30               # rotate speed while searching
FORWARD = 20            # speed toward the target
NEAR = 200              # stop when the target is this wide in pixels
WALL = 500              # stop this close to a wall, in mm
TIME_LIMIT = 40         # seconds
# ==============================

with Drone() as d:
    cam = Camera("drone", d, mirror=False, size=(640, 480))
    yaw_pid = PID()
    d.takeoff()
    start = time.time()
    while time.time() - start < TIME_LIMIT:
        frame = cam.read()
        target = finder.read(frame)
        if not target:
            yaw_pid.reset()
            d.rc(yaw=SPIN)
            d.show("?")
            d.led(RED)
        elif target.size >= NEAR or d.wall(WALL):  # arrived
            break
        else:
            d.rc(fb=FORWARD, yaw=yaw_pid(target.cx - frame.shape[1] // 2))  # keep it centred
            d.show(ARROW_UP)
            d.led(GREEN)
        if screen(frame, d, f"size {target.size:.0f}" if target else "searching") == "q":
            break
    d.rc()
    d.show(SMILE)
    d.led(GREEN)
    time.sleep(2)
