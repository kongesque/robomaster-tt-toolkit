"""Keyboard flying with a live map of the path.

The map is an estimate from speed x time, not a real position.
W/S forward/back  A/D left/right  UP/DOWN height  LEFT/RIGHT rotate
E takeoff  Q land  ESC quit
"""
from kit import *

# ======== CHANGE HERE ========
S = 30                 # move speed; RC value is roughly cm/s
UD = 30
YAW = 40               # RC value is roughly degrees/s
SCALE = 1.5            # map pixels per cm
# ==============================

with Drone() as d:
    k = Keys()
    x, y, heading = 0.0, 0.0, 0.0  # cm from takeoff point, degrees
    trail = [(0, 0)]               # all past positions
    last = time.time()
    while not k("ESCAPE"):
        # Held key = 1, released = 0
        lr = (k("d") - k("a")) * S
        fb = (k("w") - k("s")) * S
        ud = (k("UP") - k("DOWN")) * UD
        yaw = (k("RIGHT") - k("LEFT")) * YAW
        d.rc(lr, fb, ud, yaw)
        if k.tap("e"):
            d.takeoff()
        if k.tap("q"):
            d.land()

        now = time.time()
        dt, last = now - last, now  # seconds since the last loop
        if d.flying:
            # sin/cos turn "forward" into map x/y for the current heading
            a = math.radians(heading)
            x += (fb * math.sin(a) + lr * math.cos(a)) * dt
            y += (lr * math.sin(a) - fb * math.cos(a)) * dt
            heading = (heading + yaw * dt) % 360
            trail.append((x, y))

        # Draw: start point at the image centre, red path, green dot = drone
        img = np.zeros((700, 700, 3), np.uint8)
        pts = [(int(350 + px * SCALE), int(350 + py * SCALE)) for px, py in trail[-3000:]]
        cv2.polylines(img, [np.array(pts, np.int32)], False, (0, 0, 255), 2)
        cv2.circle(img, pts[-1], 7, (0, 255, 0), -1)
        cv2.putText(img, f"x {x:.0f} cm  y {-y:.0f} cm  heading {heading:.0f}", (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.imshow("Map", img)
        cv2.waitKey(1)
        k.pause()
