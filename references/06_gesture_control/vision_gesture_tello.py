"""Webcam hand gestures control a real DJI Tello; only --simulate is simulated.

Adapted from vision_hand_detection.py, keeping the MediaPipe skeleton, mirroring and FPS.
Merges the Tello connection, battery, RC commands and landing flow from vision_face_tracking.py,
replacing the face/PID logic with webcam gesture control. Does not use the Tello video stream.
Based on the RC format in fly_keyboard.py, the path display in fly_keyboard_map.py and
the colour conversion in vision_drone_stream.py. No other script is changed, imported or run.

Python 3.10-3.12:
    python -m pip install mediapipe==0.10.21 opencv-contrib-python==4.11.0.86 opencv-python==4.11.0.86 djitellopy==2.5.0
    python vision_gesture_tello.py                 # computer camera 0 + real Tello
    python vision_gesture_tello.py --camera 1      # other computer camera + real Tello
    python vision_gesture_tello.py --self-test     # no camera, no third-party packages
    python vision_gesture_tello.py --drone         # same as default; join Tello Wi-Fi first
    python vision_gesture_tello.py --simulate      # computer camera + simulator only

Gestures (four fingers are judged, the thumb is ignored, directions follow the mirrored image):
  Index finger only: point up/down/left/right -> climb/descend/move left/move right.
  Index + middle finger (V): point left/right -> circle left/right (forward + yaw).
  Four fingers straight: hover. Four fingers closed (fist): stop.
  No hand, two hands, unclear or any other gesture: hover immediately.
  Movement gestures must be held 0.25 s; hover first when switching.
  Space pause/resume, r reset estimated path, q / Esc land and quit.
  Real drone: open palm + t to take off, l to land. There is no automatic takeoff.
  Battery must be at least 20% for takeoff; lands at <=15% in flight.
  Commands update at 20 Hz; hover after 0.5 s frame timeout, land after 3 s tracking loss.
  Closing the window, camera errors, Ctrl+C or exceptions stop and try to land.

Circling is a simulated arc relative to the current heading, not orbiting a locked object.
The top-down path is integrated from commands, not real positioning. Real flights recognize
gestures with the computer camera, not the Tello camera. If the network drops, hover/land cannot be guaranteed.
"""

import argparse
from collections import deque
from dataclasses import dataclass
import math
import sys
import threading
import time

ZERO = (0, 0, 0, 0)
COMMANDS = {
    'HOVER': ZERO, 'STOP': ZERO,
    'UP': (0, 0, 25, 0), 'DOWN': (0, 0, -25, 0),
    'LEFT': (-25, 0, 0, 0), 'RIGHT': (25, 0, 0, 0),
    'ORBIT_LEFT': (0, 20, 0, -30), 'ORBIT_RIGHT': (0, 20, 0, 30),
}
HOLD_SECONDS = 0.25


class TelloFlight:
    """Real drone output plus a separate watchdog; a fake SDK can be injected for offline tests."""
    FRAME_TIMEOUT = 0.5
    TRACKING_TIMEOUT = 3.0

    def __init__(self, drone, clock=time.monotonic):
        self.drone, self.clock = drone, clock
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.thread = None
        self.connected = self.airborne = self.may_be_airborne = False
        self.command = ZERO
        self.updated = self.tracked = float('-inf')
        self.telemetry_at = float('-inf')
        self.battery, self.height, self.yaw = 0, 0, 0
        self.error = None
        self.status = 'GROUNDED'

    def connect(self):
        self.drone.connect()
        self.connected = True
        self.battery = self.drone.get_battery()
        if self.battery < 20:
            raise RuntimeError(f'Tello battery {self.battery}%: at least 20% required.')
        self.thread = threading.Thread(target=self._worker, name='tello-watchdog', daemon=True)
        self.thread.start()
        print(f'[TELLO] Connected; battery {self.battery}%. Open palm + T to take off.')

    def publish(self, command, tracked, frame_time):
        with self.lock:
            if len(command) != 4 or any(not isinstance(v, int) or abs(v) > 100 for v in command):
                raise ValueError('RC commands must contain four integers in [-100, 100].')
            self.command = tuple(command) if tracked else ZERO
            self.updated = frame_time
            if tracked:
                self.tracked = frame_time

    def takeoff(self):
        with self.lock:
            if self.error:
                raise RuntimeError(self.error)
            if self.airborne:
                return
            if not self.connected:
                raise RuntimeError('Tello is not connected.')
            if self.clock() - self.tracked > self.FRAME_TIMEOUT:
                raise RuntimeError('A fresh recognized hand is required for takeoff.')
            self.battery = self.drone.get_battery()
            if self.battery < 20:
                raise RuntimeError(f'Tello battery {self.battery}%: takeoff refused.')
            self.command = ZERO
            self.may_be_airborne = True  # Try to land even if the takeoff ACK is lost.
            try:
                self.drone.takeoff()
            except Exception:
                self.land('Takeoff failed; attempting landing')
                raise
            self.airborne = True
            self.updated = self.tracked = self.clock()
            self.status = 'FLYING'

    def land(self, reason='LANDED'):
        with self.lock:
            self.command = ZERO
            self.airborne = False  # Stop all movement updates so they cannot fight the landing.
            if not self.may_be_airborne:
                return
            try:
                self.drone.send_rc_control(*ZERO)
            except Exception as exc:
                print(f'[TELLO] Hover command failed: {exc}', file=sys.stderr)
            last_error = None
            for _ in range(2):
                try:
                    self.drone.land()
                    self.may_be_airborne = False
                    self.status = reason
                    return
                except Exception as exc:
                    last_error = exc
            self.error = f'Landing not confirmed: {last_error}'
            raise RuntimeError(self.error)

    def tick(self):
        with self.lock:
            if not self.airborne:
                return
            now = self.clock()
            if now - self.tracked >= self.TRACKING_TIMEOUT:
                self.land('Tracking lost: landed')
                return
            command = self.command if now - self.updated <= self.FRAME_TIMEOUT else ZERO
            self.drone.send_rc_control(*command)
            if now - self.telemetry_at >= 1.0:
                self.battery = self.drone.get_battery()
                self.height, self.yaw = self.drone.get_height(), self.drone.get_yaw()
                self.telemetry_at = now
                if self.battery <= 15:
                    self.land('Low battery: landed')

    def _worker(self):
        while not self.stop_event.wait(0.05):
            try:
                self.tick()
            except Exception as exc:
                self.error = f'Tello control failed: {exc}'
                try:
                    self.land('Control failure: landed')
                except Exception as landing_exc:
                    self.error += f'; {landing_exc}'
                print(f'[TELLO] {self.error}', file=sys.stderr)
                return

    def snapshot(self):
        with self.lock:
            return self.status, self.battery, self.height, self.yaw, self.airborne

    def close(self):
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join()  # Do not close the connection while an SDK command is running.
        try:
            self.land('Exit: landed')
        finally:
            self.drone.end()


def joint_angle(a, b, c):
    """Joint angle from pixel-scaled coordinates, avoiding errors from image aspect ratio."""
    u, v = (a[0] - b[0], a[1] - b[1]), (c[0] - b[0], c[1] - b[1])
    length = math.hypot(*u) * math.hypot(*v)
    if length < 1e-8:
        return 0.0
    cosine = max(-1.0, min(1.0, (u[0]*v[0] + u[1]*v[1]) / length))
    return math.degrees(math.acos(cosine))


def classify_gesture(landmarks, width, height):
    """Takes the 21 MediaPipe landmarks of one hand; returns the gesture and a display reason."""
    if len(landmarks) != 21:
        return 'HOVER', 'Invalid landmarks'
    points = [(p.x * width, p.y * height) for p in landmarks]
    if not all(math.isfinite(v) for p in points for v in p):
        return 'HOVER', 'Invalid landmarks'
    palm_size = math.dist(points[0], points[9])
    if palm_size < min(width, height) * 0.04:
        return 'HOVER', 'Move hand closer'
    extended = []
    for mcp, pip, dip, tip in ((5, 6, 7, 8), (9, 10, 11, 12),
                               (13, 14, 15, 16), (17, 18, 19, 20)):
        straight = (joint_angle(points[mcp], points[pip], points[dip]) > 155
                    and joint_angle(points[pip], points[dip], points[tip]) > 155)
        reaches_out = math.dist(points[tip], points[0]) > 1.15 * math.dist(points[pip], points[0])
        extended.append(straight and reaches_out)
    if all(extended):
        return 'HOVER', 'Open palm'
    if not any(extended):
        return 'STOP', 'Fist / closed fingers'
    if extended not in ([True, False, False, False], [True, True, False, False]):
        return 'HOVER', 'Unknown gesture'
    tips = (8, 12) if extended[1] else (8,)
    bases = (5, 9) if extended[1] else (5,)
    dx = sum(points[t][0] - points[b][0] for t, b in zip(tips, bases)) / len(tips)
    dy = sum(points[t][1] - points[b][1] for t, b in zip(tips, bases)) / len(tips)
    if math.hypot(dx, dy) < palm_size * 0.4:
        return 'HOVER', 'Point toward camera plane'
    # Keep a dead zone on diagonals so commands do not jump between axes at the boundary.
    if abs(dx) > 1.35 * abs(dy):
        direction = 'LEFT' if dx < 0 else 'RIGHT'
        return ('ORBIT_' + direction if extended[1] else direction), 'V sign' if extended[1] else 'Index finger'
    if not extended[1] and abs(dy) > 1.35 * abs(dx):
        return ('UP' if dy < 0 else 'DOWN'), 'Index finger'
    return 'HOVER', 'Point clearly along one axis'


class GestureController:
    """Time debounce. Stop acts at once; a changed gesture never continues the old command."""
    def __init__(self):
        self.candidate = 'HOVER'
        self.since = None

    def update(self, raw, now):
        if raw not in COMMANDS:
            raw = 'HOVER'
        if self.since is None or raw != self.candidate:
            self.candidate, self.since = raw, now
        if raw in ('HOVER', 'STOP'):
            return raw, ZERO
        if now - self.since < HOLD_SECONDS:
            return 'HOVER', ZERO
        return raw, COMMANDS[raw]


@dataclass
class DroneSimulator:
    """Updates position in memory only. Units: cm, s, degrees. Positive yaw turns right."""
    x: float = 0.0
    y: float = 0.0
    altitude: float = 100.0
    heading: float = 0.0

    def step(self, command, dt):
        dt = max(0.0, min(dt, 0.1))  # Stop the position jumping after a stall
        lr, fb, ud, yaw = command
        theta = math.radians(self.heading)
        omega = math.radians(yaw)
        end = theta + omega * dt
        if abs(omega) < 1e-8:
            self.x += (lr * math.cos(theta) + fb * math.sin(theta)) * dt
            self.y += (lr * math.sin(theta) - fb * math.cos(theta)) * dt
        else:
            # Integrate local velocity: constant forward + yaw draws an arc.
            self.x += (lr * (math.sin(end) - math.sin(theta))
                       + fb * (math.cos(theta) - math.cos(end))) / omega
            self.y += (lr * (math.cos(theta) - math.cos(end))
                       - fb * (math.sin(end) - math.sin(theta))) / omega
        self.altitude = max(0.0, min(300.0, self.altitude + ud * dt))
        self.heading = (self.heading + yaw * dt) % 360


def draw_panel(cv2, np, sim, trail, command, active, raw, reason, fps, count, paused, flight=None):
    panel = np.full((720, 400, 3), (24, 24, 24), dtype=np.uint8)
    def label(text, y, color=(230, 230, 230), scale=0.55):
        cv2.putText(panel, text, (14, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)
    label('LIVE TELLO - WEBCAM GESTURES' if flight else 'WEBCAM ONLY - DRONE SIMULATOR',
          28, (80, 230, 160))
    label(f"{'PAUSED' if paused else active} | raw: {raw}", 58, scale=0.48)
    label(reason, 84)
    state = flight.snapshot() if flight else None
    label(f'{state[0]} | Battery {state[1]}%' if state else f'FPS {fps:.0f} | Hands {count}', 110, scale=0.48)
    label(f'RC (lr, fb, ud, yaw): {command}', 138, (80, 230, 160), 0.48)
    height, yaw = (state[2], state[3]) if state else (sim.altitude, sim.heading)
    label(f'Height {height:.0f} cm | Yaw {yaw:.0f} deg', 164)
    label('COMMAND PATH ESTIMATE' if flight else 'TOP VIEW (auto scale)', 192)
    cv2.rectangle(panel, (15, 205), (385, 445), (75, 75, 75), 1)
    extent = max(100.0, *(max(abs(x), abs(y)) for x, y in trail))
    scale = 100.0 / extent
    def pixel(x, y):
        return int(200 + x * scale), int(325 + y * scale)
    cv2.line(panel, (200, 210), (200, 440), (50, 50, 50), 1)
    cv2.line(panel, (20, 325), (380, 325), (50, 50, 50), 1)
    for a, b in zip(trail, list(trail)[1:]):
        cv2.line(panel, pixel(*a), pixel(*b), (70, 160, 255), 2)
    position = pixel(sim.x, sim.y)
    theta = math.radians(sim.heading)
    nose = (position[0] + int(18 * math.sin(theta)), position[1] - int(18 * math.cos(theta)))
    cv2.circle(panel, position, 5, (80, 230, 160), -1)
    cv2.arrowedLine(panel, position, nose, (80, 230, 160), 2)
    label(f'X {sim.x:.0f} cm | Y {sim.y:.0f} cm', 468)
    cv2.rectangle(panel, (340, 490), (360, 610), (95, 95, 95), 1)
    level = 610 - int(max(0, min(300, height)) / 300 * 120)
    cv2.rectangle(panel, (341, min(level, 609)), (359, 609), (80, 230, 160), -1)
    label('Index: UP / DOWN / LEFT / RIGHT', 502, scale=0.46)
    label('V left / right: circle left / right', 526, scale=0.46)
    label('Open palm: hover | Fist: stop', 550, scale=0.46)
    label('No hand / two hands: hover', 574, scale=0.46)
    label('Hold movement gesture for 0.25 s', 598, scale=0.46)
    label('Space: hover | Q / Esc: land + quit' if flight else 'Space: pause | R: reset | Q / Esc: quit', 645, scale=0.46)
    label('Open palm + T: takeoff | L: land' if flight else 'Virtual height limited to 0-300 cm', 673, scale=0.46)
    label('Tracking lost 3 s: attempt landing' if flight else 'Illustration only; no flight connection', 700, scale=0.46)
    return panel


def run_camera(camera, drone_mode=False):
    # Import late so --help / --self-test need no camera or third-party packages.
    try:
        import cv2
        import mediapipe as mp
        import numpy as np
    except ImportError as exc:
        raise RuntimeError('Install: python -m pip install mediapipe==0.10.21 opencv-contrib-python==4.11.0.86') from exc
    if not hasattr(mp, 'solutions'):
        raise RuntimeError('Install mediapipe==0.10.21 on Python 3.10-3.12; this script uses MediaPipe Hands.')
    mp_hands, drawing, styles = mp.solutions.hands, mp.solutions.drawing_utils, mp.solutions.drawing_styles
    cap = cv2.VideoCapture(camera)
    hands = None
    flight = None
    window = 'Tello Gesture Control - LIVE' if drone_mode else 'Hand Gesture Prototype - NO DRONE'
    try:
        if not cap.isOpened():
            raise RuntimeError(f'Cannot open camera {camera}. Check permissions or use --camera 1.')
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7,
                               min_tracking_confidence=0.7)
        if drone_mode:
            try:
                from djitellopy import Tello
            except ImportError as exc:
                raise RuntimeError('Drone mode requires: python -m pip install djitellopy==2.5.0 opencv-python==4.11.0.86') from exc
            flight = TelloFlight(Tello())
            flight.connect()
        controller, sim = GestureController(), DroneSimulator()
        trail = deque([(0.0, 0.0)], maxlen=2000)
        paused, previous_command = False, None
        previous_time = time.monotonic()
        print('Real drone: open palm + t takes off; l lands; q / Esc lands and quits.' if flight
              else 'Gesture simulation started: no drone connected. Space pause; r reset; q / Esc quit.')
        while True:
            if flight and flight.error:
                raise RuntimeError(flight.error)
            frame_time = time.monotonic()  # Taken before read/process so an old frame cannot refresh the watchdog.
            success, image = cap.read()
            if not success or image is None:
                controller.update('HOVER', time.monotonic())
                if flight:
                    flight.publish(ZERO, False, frame_time)
                raise RuntimeError('Cannot read camera frame. Stopping and attempting landing in drone mode.')
            image = cv2.flip(image, 1)
            h, w = image.shape[:2]
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = hands.process(rgb)
            now = time.monotonic()
            dt, previous_time = now - previous_time, now
            detected = results.multi_hand_landmarks or []
            raw, reason = 'HOVER', 'No hand'
            if len(detected) == 1:
                raw, reason = classify_gesture(detected[0].landmark, w, h)
            elif len(detected) > 1:
                reason = 'Show only one hand'
            for index, hand in enumerate(detected):
                drawing.draw_landmarks(image, hand, mp_hands.HAND_CONNECTIONS,
                                       styles.get_default_hand_landmarks_style(),
                                       styles.get_default_hand_connections_style())
                if results.multi_handedness:
                    info = results.multi_handedness[index].classification[0]
                    wrist = hand.landmark[0]
                    cv2.putText(image, f'{info.label} ({info.score:.2f})',
                                (max(0, int(wrist.x*w)-50), max(25, int(wrist.y*h)-20)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
            active, command = controller.update('HOVER' if paused else raw, now)
            fresh = now - frame_time <= TelloFlight.FRAME_TIMEOUT
            if not fresh:
                active, command = controller.update('HOVER', now)
                reason = 'Frame too slow: hover'
            tracked = fresh and len(detected) == 1 and reason in (
                'Index finger', 'V sign', 'Open palm', 'Fist / closed fingers')
            if flight:
                flight.publish(command, tracked, frame_time)
                if not flight.snapshot()[4]:
                    active, command = 'GROUNDED', ZERO
            sim.step(command, dt)
            if (sim.x, sim.y) != trail[-1]:
                trail.append((sim.x, sim.y))
            if command != previous_command:
                print(f"[{'TELLO' if flight else 'SIM'}] {active} RC={command}", flush=True)
                previous_command = command
            panel = draw_panel(cv2, np, sim, trail, command, active, raw, reason,
                               1.0 / max(dt, 1e-6), len(detected), paused, flight)
            cv2.imshow(window,
                       np.hstack((cv2.resize(image, (960, 720)), panel)))
            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), 27):
                break
            if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                break
            if key == ord(' '):
                paused = not paused
                controller = GestureController()
                if flight:
                    flight.publish(ZERO, tracked, frame_time)
            elif key == ord('t') and flight:
                if paused or raw != 'HOVER' or reason != 'Open palm' or not tracked:
                    print('[TELLO] Takeoff requires a fresh open palm and unpaused controls.')
                else:
                    flight.takeoff()
                    controller = GestureController()
                    previous_time = time.monotonic()
            elif key == ord('l') and flight:
                flight.land()
                controller = GestureController()
            elif key == ord('r'):
                sim, controller = DroneSimulator(), GestureController()
                trail.clear()
                trail.append((0.0, 0.0))
    finally:
        try:
            if flight:
                flight.close()
        finally:
            cap.release()
            if hands is not None:
                hands.close()
            cv2.destroyAllWindows()
            print('STOP RC=(0, 0, 0, 0); resources released', flush=True)


def self_test():
    """Offline checks: directions, hand shapes, debounce, hand loss and arc motion."""
    from types import SimpleNamespace
    def hand(fingers, rotation=0, aspect=(640, 640)):
        points = [(0.5, 0.8)] * 21
        for finger, base in enumerate((5, 9, 13, 17)):
            x = 0.5 + (finger - 1.5) * 0.08
            ys = (0.6, 0.4, 0.3, 0.2) if finger in fingers else (0.6, 0.4, 0.5, 0.6)
            for offset, y in enumerate(ys):
                points[base+offset] = (x, y)
        theta = math.radians(rotation)
        rotated = [(0.5 + (x-.5)*math.cos(theta) - (y-.5)*math.sin(theta),
                    0.5 + (x-.5)*math.sin(theta) + (y-.5)*math.cos(theta)) for x, y in points]
        width, height = aspect
        return [SimpleNamespace(x=x*640/width, y=y*640/height) for x, y in rotated]
    for dimensions in ((640, 640), (1280, 720)):
        for rotation, direction in ((0, 'UP'), (90, 'RIGHT'), (180, 'DOWN'), (270, 'LEFT')):
            assert classify_gesture(hand({0}, rotation, dimensions), *dimensions)[0] == direction
        for rotation, direction in ((90, 'ORBIT_RIGHT'), (270, 'ORBIT_LEFT')):
            assert classify_gesture(hand({0, 1}, rotation, dimensions), *dimensions)[0] == direction
        for fingers, rotation, expected in ((set(), 0, 'STOP'), ({0, 1, 2, 3}, 0, 'HOVER'),
                                            ({0, 1}, 0, 'HOVER'), ({0}, 45, 'HOVER'), ({2}, 0, 'HOVER')):
            assert classify_gesture(hand(fingers, rotation, dimensions), *dimensions)[0] == expected
    assert classify_gesture([], 640, 480)[0] == 'HOVER'
    invalid = hand({0}); invalid[0].x = float('nan')
    assert classify_gesture(invalid, 640, 480)[0] == 'HOVER'
    controller = GestureController()
    assert controller.update('UP', 0)[1] == ZERO
    assert controller.update('UP', 0.24)[1] == ZERO
    assert controller.update('UP', 0.26)[1] == COMMANDS['UP']
    assert controller.update('LEFT', 0.27)[1] == ZERO
    assert controller.update('HOVER', 0.28)[1] == ZERO
    assert controller.update('LEFT', 1)[1] == ZERO
    assert controller.update('LEFT', 1.26)[1] == COMMANDS['LEFT']
    assert controller.update('STOP', 1.27)[1] == ZERO
    assert controller.update('UNKNOWN', 1.28)[1] == ZERO
    sim = DroneSimulator()
    for _ in range(10):
        sim.step(COMMANDS['UP'], 0.1)
    assert abs(sim.altitude - 125) < 1e-6
    for direction, sign in (('ORBIT_LEFT', -1), ('ORBIT_RIGHT', 1)):
        sim = DroneSimulator()
        for _ in range(30):
            sim.step(COMMANDS[direction], 0.1)
        assert sim.x * sign > 0 and sim.y < 0
        assert abs(sim.heading - (sign*90 % 360)) < 1e-6
        for _ in range(90):
            sim.step(COMMANDS[direction], 0.1)
        assert math.hypot(sim.x, sim.y) < 1e-6
        before = (sim.x, sim.y, sim.altitude, sim.heading)
        sim.step(ZERO, 0.1)
        assert before == (sim.x, sim.y, sim.altitude, sim.heading)
    sim.altitude = 299
    sim.step(COMMANDS['UP'], 100)
    assert sim.altitude == 300
    sim.altitude = 1
    sim.step(COMMANDS['DOWN'], 0.1)
    assert sim.altitude == 0
    print('PASS: gesture directions, aspect ratios, hover/stop, debounce, loss reset, circle simulation and limits')
    flight_self_test()


def flight_self_test():
    """Fake Tello to test real-drone commands and failure paths. No socket, no motors."""
    class FakeTello:
        def __init__(self):
            self.calls = []
            self.battery = 80
            self.fail_takeoff = self.fail_land = self.fail_rc = False

        def connect(self):
            self.calls.append(('connect',))

        def get_battery(self):
            return self.battery

        def get_height(self):
            return 90

        def get_yaw(self):
            return 0

        def takeoff(self):
            self.calls.append(('takeoff',))
            if self.fail_takeoff:
                raise RuntimeError('takeoff ACK lost')

        def send_rc_control(self, *command):
            self.calls.append(('rc', *command))
            if self.fail_rc:
                raise RuntimeError('RC failed')

        def land(self):
            self.calls.append(('land',))
            if self.fail_land:
                raise RuntimeError('land ACK lost')

        def end(self):
            self.calls.append(('end',))

    now = [10.0]
    def session():
        drone = FakeTello()
        flight = TelloFlight(drone, clock=lambda: now[0])
        flight.connected = True  # No background thread, so test timing stays fully controlled.
        flight.publish(ZERO, True, now[0])
        return drone, flight

    drone, flight = session()
    flight.publish(COMMANDS['UP'], True, now[0])
    flight.tick()
    assert not drone.calls  # Nothing is sent before takeoff
    flight.takeoff()
    assert flight.command == ZERO and flight.airborne
    for command in COMMANDS.values():
        flight.publish(command, True, now[0])
        flight.tick()
        assert drone.calls[-1] == ('rc', *command)
    flight.publish(COMMANDS['RIGHT'], False, now[0])
    flight.tick()
    assert drone.calls[-1] == ('rc', *ZERO)  # No hand / two hands / unknown gesture means zero speed at once
    flight.publish(COMMANDS['UP'], True, now[0])
    now[0] += 0.6
    flight.tick()
    assert drone.calls[-1] == ('rc', *ZERO) and flight.airborne
    now[0] += 2.5
    flight.tick()
    assert drone.calls[-1] == ('land',) and not flight.airborne
    flight.publish(COMMANDS['RIGHT'], True, now[0])
    before = len(drone.calls)
    flight.tick()
    assert len(drone.calls) == before  # A new gesture must not take off again after an automatic landing
    flight.close()
    assert drone.calls[-1] == ('end',)

    drone, flight = session()
    drone.battery = 19
    try:
        flight.takeoff()
        raise AssertionError('low battery takeoff allowed')
    except RuntimeError:
        pass
    assert not drone.calls
    drone.battery = 80
    flight.takeoff()
    drone.battery = 15
    flight.tick()
    assert drone.calls[-1] == ('land',)

    drone, flight = session()
    drone.fail_takeoff = True
    try:
        flight.takeoff()
        raise AssertionError('takeoff failure ignored')
    except RuntimeError:
        pass
    assert ('land',) in drone.calls and not flight.may_be_airborne

    drone, flight = session()
    flight.takeoff()
    flight.close()
    assert drone.calls[-3:] == [('rc', *ZERO), ('land',), ('end',)]

    drone, flight = session()
    flight.takeoff()
    drone.fail_rc = True
    flight.stop_event.wait = lambda timeout: False  # One pass through the worker failure path; no real thread.
    flight._worker()
    assert flight.error and ('land',) in drone.calls and not flight.airborne

    drone, flight = session()
    flight.takeoff()
    drone.fail_land = True
    try:
        flight.close()
        raise AssertionError('landing failure hidden')
    except RuntimeError:
        pass
    assert drone.calls.count(('land',)) == 2 and drone.calls[-1] == ('end',)
    assert flight.may_be_airborne and flight.error
    print('PASS: Tello RC mappings, grounded guard, frame timeout, tracking-loss landing, battery guards, failed ACK and cleanup')


def main():
    parser = argparse.ArgumentParser(description='Computer webcam hand gestures control a real DJI Tello; connect to Tello Wi-Fi first.')
    parser.add_argument('--camera', type=int, default=0, help='Webcam index (default: 0)')
    parser.add_argument('--self-test', action='store_true', help='Run offline checks without a camera or dependencies')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--drone', dest='drone', action='store_true', help='Control real Tello (default); open palm + T to take off, L to land')
    mode.add_argument('--simulate', dest='drone', action='store_false', help='Webcam simulation only; do not connect to Tello')
    parser.set_defaults(drone=True)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    try:
        run_camera(args.camera, args.drone)
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
