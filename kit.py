"""kit.py - all shared code. Every example starts with: from kit import *
Flags for any example: --sim (no drone, uses webcam), --dronecam (use the drone camera).
"""
import math
import os
import subprocess
import sys
import threading
import time

# Plain "python3 file.py" works: switch to this project's .venv if it isn't active.
_venv = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")
_python = os.path.join(_venv, "Scripts", "python.exe") if os.name == "nt" else os.path.join(_venv, "bin", "python")
if os.path.exists(_python) and os.path.isfile(sys.argv[0]) and os.path.realpath(sys.prefix) != os.path.realpath(_venv):
    if os.name == "nt":
        sys.exit(subprocess.call([_python] + sys.argv))
    os.execv(_python, [_python] + sys.argv)

import cv2
import numpy as np

SIM = "--sim" in sys.argv
DEFAULT_CAM = "drone" if "--dronecam" in sys.argv else "webcam"

# ---- Settings you may need to change ---------------------------------------
SWAP_LR_ARROWS = False  # True if left/right arrows look backwards on the drone
MIN_TAKEOFF_BATTERY = 20
LAND_BATTERY = 15
RC_TIMEOUT = 0.5  # seconds with no d.rc() before the drone is told to hover

# ---- Top LED colours (r, g, b) ----------------------------------------------
RED, GREEN, BLUE = (255, 0, 0), (0, 255, 0), (0, 0, 255)
YELLOW, PURPLE, WHITE, OFF = (255, 255, 0), (255, 0, 255), (255, 255, 255), (0, 0, 0)


# ---- 8x8 matrix pictures: r=red b=blue p=purple 0=off -----------------------
def pic(text):
    """Turn a drawn 8x8 picture into the 64-character string the module wants."""
    return "".join(text.split())


def recolor(pattern, color):
    """recolor(ARROW_UP, "r") -> same picture in red."""
    return "".join("0" if c == "0" else color for c in pattern)


def bar(n, color="b"):
    """Level display: n rows lit from the bottom, 0-8."""
    n = max(0, min(8, int(n)))
    return "0" * 8 * (8 - n) + color * 8 * n


ARROW_UP = pic("""
000bb000
00bbbb00
0bbbbbb0
000bb000
000bb000
000bb000
000bb000
00000000""")

ARROW_DOWN = pic("""
000bb000
000bb000
000bb000
000bb000
0bbbbbb0
00bbbb00
000bb000
00000000""")

# Drawn for someone FACING the drone, so
# when the drone moves to ITS right, the arrow points to YOUR left.
ARROW_RIGHT = pic("""
000b0000
00bb0000
0bbbbbbb
bbbbbbbb
0bbbbbbb
00bb0000
000b0000
00000000""")

ARROW_LEFT = pic("""
0000b000
0000bb00
bbbbbbb0
bbbbbbbb
bbbbbbb0
0000bb00
0000b000
00000000""")

if SWAP_LR_ARROWS:
    ARROW_LEFT, ARROW_RIGHT = ARROW_RIGHT, ARROW_LEFT

RED_X = pic("""
r000000r
0r0000r0
00r00r00
000rr000
000rr000
00r00r00
0r0000r0
r000000r""")

CHECK = pic("""
00000000
0000000b
000000bb
b0000bb0
bb00bb00
0bbbb000
00bb0000
00000000""")

SMILE = pic("""
00pppp00
0p0000p0
p0p00p0p
p000000p
p0p00p0p
p00pp00p
0p0000p0
00pppp00""")

BLANK = "0" * 64


# ---- Drone ------------------------------------------------------------------
class FakeTello:
    """Stands in for the drone under --sim: prints commands, fakes a wall ahead."""

    def __init__(self):
        self.wall = 1500  # mm to the fake wall; drops as you fly forward
        self.last_rc = (0, 0, 0, 0)

    def __getattr__(self, name):
        def call(*args, **kwargs):
            if not name.startswith("get_"):
                print(f"[SIM] {name}{args}", flush=True)
            if name == "move_forward":
                self.wall -= args[0] * 10
            elif name.startswith("rotate"):
                self.wall = 1500
            return 0 if name.startswith("get_") else None
        return call

    def get_battery(self):
        return 100

    def send_rc_control(self, lr, fb, ud, yaw):
        if (lr, fb, ud, yaw) != self.last_rc:
            print(f"[SIM] rc lr={lr} fb={fb} ud={ud} yaw={yaw}", flush=True)
            self.last_rc = (lr, fb, ud, yaw)
        self.wall = max(100, min(3000, self.wall - fb * 0.5))
        if yaw:
            self.wall = 1500

    def send_command_with_return(self, cmd, timeout=1):
        if cmd == "EXT tof?":
            return f"tof {int(self.wall)}"
        print(f"[SIM] {cmd}", flush=True)
        return "ok"


class Drone:
    """with Drone() as d:  connects, and always lands + cleans up when the block ends."""

    def __init__(self):
        self.flying = False
        self.matrix, self.color = BLANK, OFF
        self._sent = {}
        self._ext_fails = 0
        self._tof, self._tof_at = 8192, 0
        self._rc_at = None
        self._stream = False
        if SIM:
            self._t = FakeTello()
        else:
            from djitellopy import Tello
            self._t = Tello()
            self._t.connect()
        print(f"Connected. Battery {self.battery()}%")
        self.ext("mled sl 255")
        threading.Thread(target=self._watchdog, daemon=True).start()

    @property
    def t(self):
        """The full djitellopy object, for blocking moves: d.t.move_up(50), d.t.flip("f").
        Using it pauses the hover watchdog so it can't interrupt the move."""
        self._rc_at = None
        self._flush()
        return self._t

    def _flush(self):
        # A late reply left in the queue would be read as the next command's answer.
        if not SIM:
            self._t.get_own_udp_object()["responses"].clear()

    def __enter__(self):
        return self

    def __exit__(self, kind, *rest):
        self.land()
        try:
            self.show(BLANK)
            self.led(OFF)
            self.t.end()
        except Exception as e:
            print("Cleanup problem:", e)
        cv2.destroyAllWindows()
        return kind is KeyboardInterrupt  # Ctrl+C is a normal way to stop

    def battery(self):
        return self._t.get_battery()

    def height(self):
        return self._t.get_height()

    def takeoff(self):
        if self.flying:
            return
        if self.battery() < MIN_TAKEOFF_BATTERY:
            print(f"Battery {self.battery()}%: too low, not taking off")
            return
        self.t.takeoff()
        self.flying = True

    def land(self):
        if not self.flying:
            return
        self.flying, self._rc_at = False, None
        for _ in range(2):
            try:
                self.t.send_rc_control(0, 0, 0, 0)
                self.t.land()
                return
            except Exception as e:
                print("Land failed, trying again:", e)

    def rc(self, lr=0, fb=0, ud=0, yaw=0):
        """Velocity control, -100..100. Call it every loop while flying."""
        if not self.flying:
            return
        self._t.send_rc_control(*(max(-100, min(100, int(v))) for v in (lr, fb, ud, yaw)))
        self._rc_at = time.time()
        if self.battery() <= LAND_BATTERY:
            print("Low battery: landing")
            self.land()

    def _watchdog(self):
        # If the main loop stalls, the drone must not keep the last speed.
        while True:
            time.sleep(0.1)
            at = self._rc_at
            if self.flying and at and time.time() - at > RC_TIMEOUT:
                self._t.send_rc_control(0, 0, 0, 0)
                self._rc_at = None

    # ---- Expansion module ---------------------------------------------------
    def ext(self, cmd):
        """Send a raw expansion command, e.g. d.ext("led 255 0 0"). Returns the reply.
        Gives up after 2 timeouts so a missing module can't freeze the flight."""
        if self._ext_fails >= 2:
            return ""
        self._flush()
        reply = str(self._t.send_command_with_return("EXT " + cmd, timeout=1))
        if "Aborting" in reply:
            self._ext_fails += 1
            if self._ext_fails == 2:
                print("Expansion module not answering: display and ToF are now off")
        else:
            self._ext_fails = 0
        return reply

    def show(self, what, color="b"):
        """d.show(ARROW_UP) picture | d.show("A") or d.show("3", "r") one character."""
        if self._sent.get("show") == (what, color):
            return
        self._sent["show"] = (what, color)
        self.matrix = what
        self.ext("mled g " + what if len(what) == 64 else f"mled s {color} {what}")

    def scroll(self, text, color="b", direction="l", speed=1.5):
        """Scroll text across the matrix (max 70 characters)."""
        self._sent.pop("show", None)
        self.matrix = text[:1]
        self.ext(f"mled {direction} {color} {speed} {text}")

    def led(self, rgb):
        """d.led(GREEN) or d.led((255, 128, 0))"""
        if self._sent.get("led") != rgb:
            self._sent["led"] = rgb
            self.color = rgb
            self.ext("led {} {} {}".format(*rgb))

    def tof(self):
        """Front distance in mm. 8192 = nothing in range. Safe to call every loop."""
        if time.time() - self._tof_at >= 0.15:
            self._tof_at = time.time()
            self._tof = 8192
            for _ in range(3):  # a late reply from an older command can arrive first
                reply = self.ext("tof?").lower()
                value = reply.replace("tof", "").strip()
                if reply.startswith("tof") and value.isdigit():
                    self._tof = int(value)
                    break
        return self._tof

    def wall(self, mm=500):
        """True when something is closer than mm in front."""
        return 0 < self.tof() < mm


# ---- Camera -----------------------------------------------------------------
class Camera:
    """cam = Camera("webcam") or Camera("drone", d).  frame = cam.read()  (BGR)
    mirror=True flips the image so your right hand side is the screen's right."""

    def __init__(self, source="webcam", drone=None, mirror=True, index=0, size=(960, 720)):
        self.mirror, self.size = mirror, size
        self.source = "webcam" if SIM else source
        if self.source == "drone":
            drone.t.streamon()
            self.reader = drone.t.get_frame_read()
        else:
            self.cap = cv2.VideoCapture(index)
            if not self.cap.isOpened():
                raise RuntimeError(f"Cannot open camera {index}. Allow camera access or try index=1")

    def read(self):
        if self.source == "drone":
            # djitellopy 2.5 gives RGB; everything else here expects BGR.
            frame = cv2.cvtColor(self.reader.frame, cv2.COLOR_RGB2BGR)
        else:
            ok, frame = self.cap.read()
            if not ok:
                raise RuntimeError("Camera stopped giving frames")
        frame = cv2.resize(frame, self.size)
        return cv2.flip(frame, 1) if self.mirror else frame


# ---- Finders: all return an object with .cx .cy .size, or None ----------------
class Target:
    def __init__(self, cx, cy, size):
        self.cx, self.cy, self.size = int(cx), int(cy), float(size)


def _angle(a, b, c):
    ux, uy, vx, vy = a[0] - b[0], a[1] - b[1], c[0] - b[0], c[1] - b[1]
    length = math.hypot(ux, uy) * math.hypot(vx, vy)
    if length < 1e-8:
        return 0.0
    return math.degrees(math.acos(max(-1, min(1, (ux * vx + uy * vy) / length))))


def classify(p):
    """21 hand points in pixels -> (gesture, fingers).
    gesture: UP DOWN LEFT RIGHT (index finger) | V_UP V_DOWN V_LEFT V_RIGHT (two fingers)
             PALM FIST THUMB_UP THUMB_DOWN OTHER.    fingers: 0-5 raised, thumb included."""
    palm = math.dist(p[0], p[9])
    out = []
    for mcp, pip, dip, tip in ((5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20)):
        straight = _angle(p[mcp], p[pip], p[dip]) > 155 and _angle(p[pip], p[dip], p[tip]) > 155
        out.append(straight and math.dist(p[tip], p[0]) > 1.15 * math.dist(p[pip], p[0]))
    thumb = math.dist(p[4], p[9]) > 0.8 * palm and _angle(p[2], p[3], p[4]) > 140
    fingers = sum(out) + thumb

    if all(out):
        return "PALM", fingers
    if not any(out):
        dx, dy = p[4][0] - p[2][0], p[4][1] - p[2][1]
        if thumb and abs(dy) > 1.35 * abs(dx):
            return ("THUMB_UP" if dy < 0 else "THUMB_DOWN"), fingers
        return "FIST", fingers
    if out not in ([True, False, False, False], [True, True, False, False]):
        return "OTHER", fingers

    two = out[1]
    tips, bases = ((8, 12), (5, 9)) if two else ((8,), (5,))
    dx = sum(p[t][0] - p[b][0] for t, b in zip(tips, bases)) / len(tips)
    dy = sum(p[t][1] - p[b][1] for t, b in zip(tips, bases)) / len(tips)
    if math.hypot(dx, dy) < palm * 0.4:
        return "OTHER", fingers
    if abs(dx) > 1.35 * abs(dy):
        way = "LEFT" if dx < 0 else "RIGHT"
    elif abs(dy) > 1.35 * abs(dx):
        way = "UP" if dy < 0 else "DOWN"
    else:
        return "OTHER", fingers  # diagonal: don't guess
    return ("V_" + way if two else way), fingers


class Hands:
    """hand = Hands().read(frame) -> None unless exactly one hand is visible.
    hand.gesture, hand.fingers, hand.points, hand.side, hand.cx, hand.cy, hand.size"""

    def __init__(self, confidence=0.7):
        import mediapipe as mp
        self.mp = mp.solutions
        self.model = self.mp.hands.Hands(max_num_hands=2, min_detection_confidence=confidence,
                                         min_tracking_confidence=confidence)

    def read(self, frame):
        hands = self.read_all(frame)
        return hands[0] if len(hands) == 1 else None

    def read_all(self, frame):
        """Every visible hand (up to 2), sorted left to right on screen."""
        h, w = frame.shape[:2]
        result = self.model.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        hands = []
        for one, info in zip(result.multi_hand_landmarks or [], result.multi_handedness or []):
            self.mp.drawing_utils.draw_landmarks(frame, one, self.mp.hands.HAND_CONNECTIONS)
            p = [(q.x * w, q.y * h) for q in one.landmark]
            hand = Target(p[9][0], p[9][1], math.dist(p[0], p[9]))
            hand.points = p
            hand.gesture, hand.fingers = classify(p)
            hand.side = info.classification[0].label
            hands.append(hand)
        return sorted(hands, key=lambda q: q.cx)


def classify_body(p):
    """33 body points in pixels -> pose name. LEFT/RIGHT mean sides of the screen.
    BOTH_UP BOTH_OUT LEFT_UP RIGHT_UP LEFT_OUT RIGHT_OUT DOWN OTHER"""
    width = max(math.dist(p[11], p[12]), 1)

    def arm(shoulder, wrist):
        dx, dy = abs(wrist[0] - shoulder[0]), wrist[1] - shoulder[1]
        if dy < -0.4 * width:
            return "UP"
        if dx > 0.8 * width and abs(dy) < 0.6 * width:
            return "OUT"
        return "DOWN"

    left, right = (arm(*a) for a in sorted([(p[11], p[15]), (p[12], p[16])], key=lambda a: a[0][0]))
    if left == right:
        return "DOWN" if left == "DOWN" else "BOTH_" + left
    if right == "DOWN":
        return "LEFT_" + left
    return "RIGHT_" + right if left == "DOWN" else "OTHER"


class Body:
    """body = Body().read(frame) -> None if no person. body.pose, body.points, .cx .cy .size
    Keep your shoulders and arms in view."""

    def __init__(self, confidence=0.6):
        import mediapipe as mp
        self.mp = mp.solutions
        self.model = self.mp.pose.Pose(model_complexity=1, min_detection_confidence=confidence,
                                       min_tracking_confidence=confidence)

    def read(self, frame):
        h, w = frame.shape[:2]
        found = self.model.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).pose_landmarks
        if not found:
            return None
        self.mp.drawing_utils.draw_landmarks(frame, found, self.mp.pose.POSE_CONNECTIONS)
        if min(found.landmark[11].visibility, found.landmark[12].visibility) < 0.5:
            return None
        p = [(q.x * w, q.y * h) for q in found.landmark]
        body = Target((p[11][0] + p[12][0]) / 2, (p[11][1] + p[12][1]) / 2, math.dist(p[11], p[12]))
        body.points = p
        body.pose = classify_body(p)
        return body


class Faces:
    """face = Faces().read(frame) -> the biggest face, or None.
    Faces().read_all(frame) -> every face, biggest first. len() counts people."""

    def __init__(self):
        self.model = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    def read(self, frame):
        faces = self.read_all(frame)
        return faces[0] if faces else None

    def read_all(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = []
        for x, y, w, h in self.model.detectMultiScale(gray, 1.1, 5, minSize=(60, 60)):
            cv2.rectangle(frame, (int(x), int(y)), (int(x + w), int(y + h)), (0, 255, 0), 2)
            faces.append(Target(x + w / 2, y + h / 2, w))
        return sorted(faces, key=lambda q: -q.size)


class Color:
    """thing = Color("red").read(frame) -> the biggest blob of that colour, or None."""
    RANGES = {  # OpenCV HSV: H 0-179, S 0-255, V 0-255
        "red": [((0, 120, 70), (10, 255, 255)), ((170, 120, 70), (179, 255, 255))],
        "orange": [((11, 120, 90), (24, 255, 255))],
        "yellow": [((25, 100, 100), (34, 255, 255))],
        "green": [((35, 80, 60), (85, 255, 255))],
        "blue": [((95, 100, 60), (130, 255, 255))],
        "purple": [((131, 60, 60), (160, 255, 255))],
    }

    def __init__(self, name, min_area=1500):
        self.name, self.min_area = name, min_area

    def read(self, frame):
        hsv = cv2.cvtColor(cv2.GaussianBlur(frame, (7, 7), 0), cv2.COLOR_BGR2HSV)
        mask = sum(cv2.inRange(hsv, lo, hi) for lo, hi in self.RANGES[self.name])
        mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        blobs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not blobs:
            return None
        blob = max(blobs, key=cv2.contourArea)
        if cv2.contourArea(blob) < self.min_area:
            return None
        x, y, w, h = cv2.boundingRect(blob)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
        return Target(x + w / 2, y + h / 2, w)


class Markers:
    """m = Markers().read(frame) -> an ArUco marker or QR code, or None.
    m.value is text: "7" for ArUco id 7, or the words in the QR code."""

    def __init__(self):
        words = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.aruco = cv2.aruco.ArucoDetector(words)
        self.qr = cv2.QRCodeDetector()

    def read(self, frame):
        corners, ids, _ = self.aruco.detectMarkers(frame)
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            box, value = corners[0][0], str(ids[0][0])
        else:
            value, box, _ = self.qr.detectAndDecode(frame)
            if not value or box is None:
                return None
            box = box[0]
        found = Target(box[:, 0].mean(), box[:, 1].mean(), box[:, 0].max() - box[:, 0].min())
        found.value = value
        return found


# ---- Small helpers --------------------------------------------------------------
def swap_lr(rc, picture):
    """Drone camera: it faces you, so its left is your right. Swaps both to YOUR side."""
    swapped = {ARROW_LEFT: ARROW_RIGHT, ARROW_RIGHT: ARROW_LEFT}
    return (-rc[0], *rc[1:]), swapped.get(picture, picture)


class Hold:
    """g = hold(value): movement only counts after it stays the same for `seconds`.
    Stops a one-frame misread from moving the drone. PALM/FIST/None act at once."""

    def __init__(self, seconds=0.25):
        self.seconds, self.value, self.since = seconds, None, 0

    def __call__(self, value):
        now = time.time()
        if value != self.value:
            self.value, self.since = value, now
        if value in (None, "PALM", "FIST") or now - self.since >= self.seconds:
            return value
        return None


class PID:
    """speed = pid(error). Defaults: P=0.4, D=0.4."""

    def __init__(self, p=0.4, d=0.4, i=0.0):
        self.p, self.d, self.i = p, d, i
        self.last, self.total = 0, 0

    def __call__(self, error):
        self.total += error
        out = self.p * error + self.d * (error - self.last) + self.i * self.total
        self.last = error
        return int(max(-100, min(100, out)))

    def reset(self):
        self.last, self.total = 0, 0


class Keys:
    """Keyboard through a small pygame window (click it first).
    k = Keys()   k("w") is held?   k.tap("e") pressed just now?  Names: a-z, UP, SPACE..."""

    def __init__(self):
        import pygame
        self.pygame = pygame
        pygame.init()
        pygame.display.set_mode((300, 150))
        pygame.display.set_caption("Click here, then use keys")
        self.was = {}

    def __call__(self, name):
        self.pygame.event.pump()
        return bool(self.pygame.key.get_pressed()[getattr(self.pygame, "K_" + name)])

    def tap(self, name):
        now, before = self(name), self.was.get(name, False)
        self.was[name] = now
        return now and not before

    def pause(self, seconds=0.05):
        self.pygame.time.wait(int(seconds * 1000))


def screen(frame, d, text="", title="UAV"):
    """Show the frame with status and a preview of the matrix + top LED. Returns the key.
    Built in: t = takeoff, l = land. Returns "q" for q, Esc, or closing the window."""
    state = "FLYING" if d.flying else "GROUND"
    cv2.putText(frame, f"{'SIM ' if SIM else ''}{state} BAT {d.battery()}% H {d.height()}cm  t=takeoff l=land q=quit",
                (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    if text:
        cv2.putText(frame, str(text), (10, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    cell, x0, y0 = 12, frame.shape[1] - 110, 12
    cv2.rectangle(frame, (x0 - 4, y0 - 4), (x0 + 8 * cell + 3, y0 + 8 * cell + 3), (40, 40, 40), -1)
    if len(d.matrix) == 64:
        dots = {"r": (0, 0, 255), "b": (255, 80, 0), "p": (255, 0, 255)}
        for i, c in enumerate(d.matrix):
            if c in dots:
                center = (x0 + i % 8 * cell + cell // 2, y0 + i // 8 * cell + cell // 2)
                cv2.circle(frame, center, 5, dots[c], -1)
    else:
        cv2.putText(frame, d.matrix[:5], (x0 + 4, y0 + 66), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (255, 80, 0), 3)
    r, g, b = d.color
    cv2.circle(frame, (x0 + 4 * cell, y0 + 8 * cell + 16), 8, (b, g, r), -1)

    cv2.imshow(title, frame)
    code = cv2.waitKey(1) & 0xFF
    key = chr(code).lower() if code != 255 else ""
    if key == "t":
        d.takeoff()
    elif key == "l":
        d.land()
    elif code == 27 or cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1:
        key = "q"
    return key
