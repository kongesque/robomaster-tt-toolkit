# SDK Samples

Standalone samples using the raw Tello SDK, DJITelloPy and MediaPipe, one folder per task. Run a sample from inside its folder. The numbered examples in the [main project](../README.md) are the simpler starting point.

| Folder | Task | Related example |
|---|---|---|
| [01_sdk_basics](01_sdk_basics) | Send SDK commands | `9_sdk.py` |
| [02_keyboard_flight](02_keyboard_flight) | Fixed route and keyboard flight | `2_keyboard.py`, `4_mission.py` |
| [03_path_mapping](03_path_mapping) | Draw the flight path | `8_map.py` |
| [04_camera_vision](04_camera_vision) | Drone camera, hands, face tracking | `5_track.py` |
| [05_keyboard_matrix_tof](05_keyboard_matrix_tof) | **Keyboard, matrix arrows, LED, red X at wall** | `2_keyboard.py` |
| [06_gesture_control](06_gesture_control) | **Webcam gestures fly the drone** | `1_gesture.py` |

## Files

| File | Shows | Watch out |
|---|---|---|
| `01_sdk_basics/sdk_socket_console.py` | Type SDK commands over raw UDP | - |
| `01_sdk_basics/sdk_socket_keys.py` | Keys send raw UDP commands | Needs `pip install keyboard`. Needs `sudo` on Mac |
| `01_sdk_basics/sdk_easytello_console.py` | Short commands with easytello | Needs `pip install easytello` |
| `02_keyboard_flight/fly_auto_route.py` | Fixed route with djitellopy | Moves must be 20+ cm |
| `02_keyboard_flight/fly_keyboard.py` | Basic keyboard RC loop | Arrows move, `W` `S` height, `A` `D` rotate |
| `03_path_mapping/fly_keyboard_map.py` | Keyboard flight + path map | Measure your real speed for `fSpeed`. `z` saves a photo |
| `04_camera_vision/vision_drone_stream.py` | Show the drone camera | - |
| `04_camera_vision/vision_hand_detection.py` | MediaPipe hand skeleton, FPS | Webcam only, no drone |
| `04_camera_vision/vision_face_tracking.py` | Face tracking with PID | Takes off as soon as it runs |
| `05_keyboard_matrix_tof/fly_keyboard_matrix_tof.py` | Keyboard, arrows, LED, red X | `W` `S` move, arrows height and rotate |
| `06_gesture_control/vision_gesture_tello.py` | Webcam gesture flight | Has `--simulate` and `--self-test`. No matrix display |

`KeyPressModule.py` is the pygame key helper, copied into each folder that needs it.
