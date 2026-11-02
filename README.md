# RoboMaster TT Toolkit

A small Python toolkit and example collection for the DJI RoboMaster TT (Tello Talent) and its expansion module. Built on [DJITelloPy](https://github.com/damiafuentes/DJITelloPy), [MediaPipe](https://github.com/google-ai-edge/mediapipe) and OpenCV.

## Features

- Hand gesture, keyboard and autonomous flight
- Face, hand and colour tracking with PID
- LED matrix, top LED and ToF sensor helpers
- Webcam or drone camera input
- Simulation mode: add `--sim` to run any example without a drone
- Automatic landing on exit, errors and low battery

## Contents

[Installation](#installation) · [Quick start](#quick-start) · [Examples](#examples) · [Controls](#controls) · [Configuration](#configuration) · [Snippets](#snippets) · [API](#api) · [Troubleshooting](#troubleshooting) · [Notes](#notes) · [Hardware](#hardware) · [SDK samples](references/README.md)

## Installation

Requires Python 3.10-3.12.

```bash
git clone https://github.com/Kongesque/robomaster-tt-toolkit.git
cd robomaster-tt-toolkit
sh setup.sh
```

Windows: `setup.bat`

The drone's Wi-Fi has no internet, so install before connecting.

## Quick start

Power on the drone and join its Wi-Fi (`RMTT-xxxx` or `TELLO-xxxx`).

```bash
source .venv/bin/activate
python 0_check.py
python 1_gesture.py
```

Windows: `.venv\Scripts\activate`

`0_check.py` tests the hardware with the motors off. Try without a drone:

```bash
python 1_gesture.py --sim
```

## Examples

Each example has a `CHANGE HERE` block at the top.

| Example | Description | Settings |
|---|---|---|
| `1_gesture.py` | **Hand gesture control with matrix arrows** | `CAM`, `ACTIONS` |
| `2_keyboard.py` | Keyboard control, arrows, stop at walls with a red X | `S`, `WALL` |
| `3_fingers.py` | Count fingers, show the number, run an action | `on_count()` |
| `4_mission.py` | Autonomous route, such as a square | `STEPS` |
| `5_track.py` | Follow a face, hand or colour | `finder` |
| `6_avoid.py` | Fly alone and turn at walls | `WALL`, `TURN` |
| `7_color.py` | Recognise colours and react | `RULES` |
| `8_map.py` | Live map of the flight path | `S`, `SCALE` |
| `9_sdk.py` | Interactive SDK console | - |

## Controls

**Camera examples (`1 3 5 7`):** click the video window. `t` takeoff, `l` land, `q` land and quit.

**Gestures (`1_gesture.py`):** one hand only, held for 0.25 s.

| Hand | Name | Default |
|---|---|---|
| Index points up/down/left/right | `UP` `DOWN` `LEFT` `RIGHT` | Move that way, arrow, green LED |
| Two fingers up/down | `V_UP` `V_DOWN` | Forward / back |
| Two fingers left/right | `V_LEFT` `V_RIGHT` | Rotate |
| Open palm | `PALM` | Hover, clear matrix |
| Fist | `FIST` | Stop, red X, red LED |
| Thumb up/down | `THUMB_UP` `THUMB_DOWN` | Unused: uncomment to take off / land |
| No hand, two hands, unclear | - | Hover |

**Keyboard (`2 8`):** click the small window.

| `W` `S` | `A` `D` | `↑` `↓` | `←` `→` | `E` | `Q` | `Space` | `Esc` |
|---|---|---|---|---|---|---|---|
| Forward, back | Left, right | Up, down | Rotate | Takeoff | Land | Hover (`2` only) | Quit |

## Configuration

| Goal | Change |
|---|---|
| Use another webcam | `Camera(CAM, d, index=1)` |
| Red arrow | `recolor(ARROW_UP, "r")` |
| Custom picture | `MY = pic("""8 rows of 8 chars""")`, chars `r b p 0` |
| Arrows look backwards | `SWAP_LR_ARROWS = True` in `kit.py` |
| Left/right feel swapped on webcam | Stand **behind** the drone, or swap `S` and `-S` in `ACTIONS` |
| Follow a colour | `finder = Color("red")`: red orange yellow green blue purple |
| Single-file script | Paste `kit.py` at the top, delete `from kit import *` |

## Snippets

These go inside the main `while` loop unless noted. `d.t` is the underlying djitellopy drone.

```python
# Save a photo on key p (use key = screen(frame, d))
if key == "p":
    cv2.imwrite(f"photo_{int(time.time())}.jpg", frame)

# Smile when a face is seen (before the loop: faces = Faces())
d.show(SMILE if faces.read(frame) else BLANK)

# Different action for left / right hand
if hand and hand.side == "Left":
    d.led(BLUE)

# Pinch thumb + index (hand.points: 21 pixel positions)
if hand and math.dist(hand.points[4], hand.points[8]) < hand.size * 0.3:
    d.show("P")

# QR code (before the loop: qr = cv2.QRCodeDetector())
text, _, _ = qr.detectAndDecode(frame)
if text:
    d.scroll(text)

# ArUco marker (before the loop:)
# aruco = cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50))
corners, ids, _ = aruco.detectMarkers(frame)
if ids is not None:
    d.show(str(ids[0][0]))

# Mission pad (before takeoff: d.t.enable_mission_pads(); d.t.set_mission_pad_detection_direction(0))
pad = d.t.get_mission_pad_id()     # -1 = none seen
```

```python
# Flip once, not every frame. Needs battery above 50%.
if g == "THUMB_UP" and not flipped:
    d.t.flip_forward()    # flip_back flip_left flip_right
    flipped = True

# Blink / breathe the top LED
d.ext("led bl 2 255 0 0 0 0 255")  # 2 Hz, red then blue
d.ext("led br 1 0 255 0")          # 1 Hz green pulse

# Scroll text, show a heart
d.scroll("HELLO", "r")
d.show("heart", "r")

# Stop motors immediately (the drone falls)
d.t.emergency()
```

## API

**`kit.py`**

| Code | Description |
|---|---|
| `with Drone() as d:` | Connect. Always lands when the block ends, even on a crash |
| `d.rc(lr, fb, ud, yaw)` | Speed -100 to 100. `d.rc(fb=30)`. `d.rc()` = hover |
| `d.show(ARROW_UP)` `d.show("3", "r")` | Matrix |
| `d.tof()` `d.wall(500)` | Front distance in mm, wall closer than 500? |
| `d.ext("...")` | Raw expansion command |
| `Camera("webcam")` `Camera("drone", d)` | `.read()` gives a BGR frame |
| `Hands()` `Faces()` `Color("red")` | `.read(frame)` gives `.cx .cy .size`, or `None` |
| `hand.gesture` `hand.fingers` `hand.points` `hand.side` | Extra hand info |
| `Hold(0.25)` `PID(0.4, 0.4)` | Debounce, smooth tracking |
| `screen(frame, d, "text")` | Show window, returns key |
| Pictures | `ARROW_UP ARROW_DOWN ARROW_LEFT ARROW_RIGHT RED_X CHECK SMILE BLANK` |
| Colours | `RED GREEN BLUE YELLOW PURPLE WHITE OFF` |

**`rc` signs**

| `lr` | `fb` | `ud` | `yaw` |
|---|---|---|---|
| + right, - left | + forward, - back | + up, - down | + clockwise, - counter |

**Blocking moves** (20-500 cm, the next line runs after the move)

```python
d.t.move_forward(50)     # move_back move_left move_right move_up move_down
d.t.rotate_clockwise(90) # rotate_counter_clockwise
d.t.go_xyz_speed(50, 0, 30, 30)   # x y z speed
d.t.send_control_command("stop")  # hover now, works any time
d.t.send_control_command("throwfly")  # throw it flat within 5 s to start
d.t.turn_motor_on()      # slow spin to cool it on the ground; turn_motor_off()
d.t.get_height()         # also get_yaw() get_temperature() get_flight_time()
```

**Expansion commands**

| Command | Description |
|---|---|
| `mled g <64 chars>` | Picture, chars `r b p 0` |
| `mled s r A` | One character, colour `r b p`. Also `mled s r heart` |
| `mled l r 1.5 HELLO` | Scroll text. Direction `l r u d`, speed 0.1-2.5, max 70 chars |
| `mled sl 255` | Brightness 0-255 |
| `led 0 255 0` | Top LED r g b |
| `led br 1 0 255 0` | Pulse: Hz r g b |
| `led bl 2 255 0 0 0 0 255` | Flash two colours: Hz then two rgb |
| `tof?` | Reply `tof 481` in mm, `8192` = out of range |

## Troubleshooting

| Problem | Fix |
|---|---|
| No drone Wi-Fi | Set the switch on the expansion module to direct connection |
| Wi-Fi password lost | Hold power 5 s until the light flashes yellow: resets to no password |
| `mediapipe` has no `solutions` | Wrong Python. Delete `.venv`, run setup again (3.10-3.12) |
| Camera won't open | Allow Terminal / VS Code in camera privacy settings, or `index=1` |
| Mac: can't reach drone | Allow Terminal / VS Code in Local Network privacy settings |
| Drone camera black or frozen | Allow Python through the firewall (UDP 11111), or turn it off |
| Matrix blank, LED dead | Reseat the module, then `9_sdk.py` → `EXT version?`. Needs factory ESP32 firmware |
| Gestures unreliable | Hand 30-80 cm from camera, plain background, good light |

## Notes

- Don't name a file `mediapipe.py`, `cv2.py` or `djitellopy.py`. It hides the real library.
- `move_*` under 20 cm is rejected.
- `mled sc` clears the boot animation, **not** the screen. Use `d.show(BLANK)`.
- `get_distance_tof()` is the **bottom** sensor in cm. `d.tof()` is the **front** sensor in mm.
- Don't mix `d.rc()` and `move_*` at the same moment. `d.rc()` is for loops, `move_*` is for steps.
- Tello lands by itself after 15 s with no commands. Keep calling `d.rc()` in loops.
- Front ToF reaches about 1.2 m, so keep `WALL` under 1200.
- Expect about 8 minutes per battery with the expansion kit.

## Hardware

| Item | Value |
|---|---|
| Model | DJI RoboMaster TT (Tello Talent), TLW004 |
| Weight, size | 87 g with guards, 98 × 92.5 × 41 mm |
| Flight time | 13 min, about 8 min with expansion kit |
| Max speed, height, distance | 8 m/s, 30 m, 100 m |
| Battery | 1,100 mAh 3.8 V LiPo, Micro-USB charging |
| Camera, video | 5 MP, 720p 30 FPS, electronic stabilization |
| Connection | 2.4 GHz Wi-Fi, UDP, Tello SDK 3.0 |
| Ports | Commands 8889, state 8890, video 11111, drone IP `192.168.10.1` |
| Expansion | ESP32-D2WD, 8×8 red/blue LED matrix, ToF up to 1.2 m |
| Positioning | Downward vision + infrared, no GPS |

Full command list: [docs/user-guide.pdf](docs/user-guide.pdf). More specs: [docs/drone-spec.md](docs/drone-spec.md).
