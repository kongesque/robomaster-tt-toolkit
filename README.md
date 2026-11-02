# RoboMaster TT Toolkit

Python examples for the DJI RoboMaster TT and its expansion module. Pick an example, run it, edit the `CHANGE HERE` block at the top.

## Setup

Once, with internet. Needs Python 3.10-3.12.

```bash
git clone https://github.com/Kongesque/robomaster-tt-toolkit.git
cd robomaster-tt-toolkit
sh setup.sh
```

## Run

Turn on the drone and join its Wi-Fi (`RMTT-xxxx`). It has no internet.

```bash
python3 0_check.py                # hardware check, motors stay off
python3 1_gesture.py              # run an example
python3 1_gesture.py --sim        # no drone needed
python3 1_gesture.py --dronecam   # use the drone camera
```

Windows: run `setup.bat` once, then use `python` instead of `python3`.

## Examples

| File | What it does | Edit |
|---|---|---|
| `0_check.py` | Hardware check | - |
| **`1_gesture.py`** | **Hand gestures move the drone, arrows on the matrix** | `ACTIONS`, `WALL` |
| `2_keyboard.py` | Keyboard flying, arrows, red X at walls | `S`, `WALL` |
| `3_fingers.py` | Count fingers, show the number, run an action | `on_count()` |
| `4_mission.py` | Fly a set route, such as a square | `STEPS` |
| `5_track.py` | Follow a face, hand, body, colour or marker | `finder` |
| `6_avoid.py` | Fly alone and turn at walls | `WALL`, `TURN` |
| `7_color.py` | Recognise colours and react | `RULES` |
| `8_map.py` | Keyboard flying with a live path map | `S`, `SCALE` |
| `9_sdk.py` | Type raw SDK commands | - |
| `10_hand_position.py` | Steer by moving your hand around the screen | `BOX` |
| `11_two_hands.py` | Two hands at once | `LEFT_HAND`, `RIGHT_HAND` |
| `12_body_pose.py` | Whole-body control with your arms | `ACTIONS` |
| `13_search.py` | Search for a target, fly to it, land | `finder`, `NEAR` |
| `14_distance.py` | Show distance on the matrix, hold a distance | `FLY`, `GOAL` |
| `15_markers.py` | ArUco or QR code triggers an action | `ACTIONS` |
| `16_photo.py` | Gesture starts a countdown photo | `TRIGGER` |

## Controls

**Video window:** `t` takeoff, `l` land, `q` quit.

**Keyboard (`2_keyboard.py`, `8_map.py`):** `W S` forward/back, `A D` left/right, `↑ ↓` height, `← →` rotate, `E` takeoff, `Q` land, `Esc` quit.

**Gestures (`1_gesture.py`):** show one hand and hold for 0.25 s.

| Hand | Name in `ACTIONS` | Does |
|---|---|---|
| Point index finger | `UP` `DOWN` `LEFT` `RIGHT` | Move that way |
| Point two fingers | `V_UP` `V_DOWN` | Forward, back |
| Point two fingers | `V_LEFT` `V_RIGHT` | Rotate |
| Open palm | `PALM` | Hover |
| Fist | `FIST` | Stop, red X |
| No hand or unclear | - | Hover |

## Common changes

| Want | Change |
|---|---|
| Gestures + wall stop | `WALL = 500` in `1_gesture.py` |
| Takeoff and land by thumb | Uncomment the `THUMB_UP` and `THUMB_DOWN` rows |
| Flip by gesture | Add `"V_LEFT": lambda d: d.t.flip_left(),` to `ACTIONS` |
| Follow a colour | `finder = Color("red")` |
| Arrows look backwards | `SWAP_LR_ARROWS = True` in `kit.py` |
| Everything in one file | Paste `kit.py` at the top, delete `from kit import *` |

## Problems

| Problem | Fix |
|---|---|
| Can't see drone Wi-Fi | Set the expansion module switch to direct connection |
| Can't reach drone on Mac | Allow your terminal in Local Network privacy settings |
| Camera won't open | Allow your terminal in Camera privacy settings |
| Drone camera black | Allow Python through the firewall |
| Matrix or LED dead | Reseat the module, then run `9_sdk.py` and type `EXT version?` |
| `No module named cv2` | Run `sh setup.sh` first |
| `mediapipe` has no `solutions` | Wrong Python: delete `.venv`, run setup again |
| Gestures unreliable | Keep your hand 30-80 cm away, in good light |

## More

- [Reference](docs/reference.md): kit functions, code snippets, drone commands
- [SDK samples](references/README.md): standalone samples, one folder per task
- [Drone specs](docs/drone-spec.md)
- [SDK guide](docs/user-guide.pdf)
