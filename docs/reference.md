# Reference

[Kit](#kit) · [Speeds and moves](#speeds-and-moves) · [Snippets](#snippets) · [Expansion commands](#expansion-commands) · [Body poses](#body-poses) · [Notes](#notes)

## Kit

| Code | Does |
|---|---|
| `with Drone() as d:` | Connect. Always lands when the block ends |
| `d.takeoff()` `d.land()` | Take off, land |
| `d.rc(lr, fb, ud, yaw)` | Set speeds. `d.rc(fb=30)`. `d.rc()` = hover |
| `d.show(ARROW_UP)` `d.show("3", "r")` | Picture or one character on the matrix |
| `d.scroll("HELLO", "r")` | Scroll text |
| `d.led(GREEN)` | Top LED |
| `d.tof()` `d.wall(500)` | Front distance in mm, wall closer than 500? |
| `d.height()` `d.battery()` | Height in cm, battery percent |
| `d.ext("...")` | Raw expansion command |
| `d.t` | The full djitellopy drone |
| `Camera("webcam")` `Camera("drone", d)` | `.read()` gives a frame |
| `Hands()` `Faces()` `Body()` `Markers()` `Color("red")` | `.read(frame)` gives `.cx .cy .size`, or `None` |
| `hands.read_all(frame)` `faces.read_all(frame)` | Every hand or face, as a list |
| `hand.gesture` `hand.fingers` `hand.points` `hand.side` | Hand details |
| `body.pose` `marker.value` | Body and marker details |
| `Hold(0.25)` | A value must stay this long before it counts |
| `PID(0.4, 0.4)` | Turns an error into a speed |
| `screen(frame, d, "text")` | Show the window, returns the key |
| `pic("""8 rows of 8 chars""")` | Custom picture, chars `r b p 0` |
| `recolor(ARROW_UP, "r")` `bar(5)` | Red arrow, level display |
| `swap_lr(rc, picture)` | Drone camera: match left/right to your side |

Pictures: `ARROW_UP ARROW_DOWN ARROW_LEFT ARROW_RIGHT RED_X CHECK SMILE BLANK`

LED colours: `RED GREEN BLUE YELLOW PURPLE WHITE OFF`

Colour names: `red orange yellow green blue purple`

## Speeds and moves

`d.rc()` speeds run from -100 to 100.

| `lr` | `fb` | `ud` | `yaw` |
|---|---|---|---|
| + right, - left | + forward, - back | + up, - down | + clockwise, - counter |

Moves finish before the next line runs. Distances are 20-500 cm.

```python
d.t.move_forward(50)     # move_back move_left move_right move_up move_down
d.t.rotate_clockwise(90) # rotate_counter_clockwise
d.t.flip_forward()       # flip_back flip_left flip_right. Needs battery above 50%
d.t.go_xyz_speed(50, 0, 30, 30)       # x y z speed
d.t.send_control_command("stop")      # hover now
d.t.send_control_command("throwfly")  # throw it flat within 5 s to start
d.t.turn_motor_on()      # slow spin to cool on the ground; turn_motor_off()
d.t.get_height()         # also get_yaw() get_temperature() get_flight_time()
d.t.emergency()          # stop motors now, the drone falls
```

## Snippets

Put these inside the main `while` loop.

```python
# Save a photo on key p
key = screen(frame, d)
if key == "p":
    cv2.imwrite(f"photo_{int(time.time())}.jpg", frame)

# Smile when a face is seen (before the loop: faces = Faces())
d.show(SMILE if faces.read(frame) else BLANK)

# Count people (before the loop: faces = Faces())
d.show(str(len(faces.read_all(frame))))

# Battery level on the matrix
d.show(bar(d.battery() / 12.5))

# Record video
# Before the loop: video = cv2.VideoWriter("flight.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 20, (960, 720))
# After the loop:  video.release()
video.write(frame)

# Left or right hand
if hand and hand.side == "Left":
    d.led(BLUE)

# Pinch thumb and index
if hand and math.dist(hand.points[4], hand.points[8]) < hand.size * 0.3:
    d.show("P")

# Flip once, not every frame (before the loop: flipped = False)
if g == "THUMB_UP" and not flipped:
    d.t.flip_forward()
    flipped = True

# Blink or pulse the top LED
d.ext("led bl 2 255 0 0 0 0 255")  # 2 Hz, red then blue
d.ext("led br 1 0 255 0")          # 1 Hz green pulse

# Mission pad
# Before takeoff: d.t.enable_mission_pads(); d.t.set_mission_pad_detection_direction(0)
pad = d.t.get_mission_pad_id()     # -1 = none seen
```

## Expansion commands

Use with `d.ext("...")`, or type `EXT` first in `9_sdk.py`.

| Command | Does |
|---|---|
| `mled g <64 chars>` | Picture, chars `r b p 0` |
| `mled s r A` | One character. Also `mled s r heart` |
| `mled l r 1.5 HELLO` | Scroll text. Direction `l r u d`, speed 0.1-2.5, max 70 chars |
| `mled sl 255` | Brightness 0-255 |
| `led 0 255 0` | Top LED: r g b |
| `led br 1 0 255 0` | Pulse: Hz, r g b |
| `led bl 2 255 0 0 0 0 255` | Flash two colours: Hz, then two r g b |
| `tof?` | Replies `tof 481` in mm. `8192` = out of range |

## Body poses

For `12_body_pose.py`. Left and right mean sides of the screen. Keep your shoulders and arms in view.

| Arms | Name in `ACTIONS` | Does |
|---|---|---|
| Both up | `BOTH_UP` | Up |
| Both out | `BOTH_OUT` | Down |
| One up | `LEFT_UP` `RIGHT_UP` | Left, right |
| One out | `LEFT_OUT` `RIGHT_OUT` | Rotate |
| Down, or nobody seen | `DOWN` | Hover |

## Notes

**Common mistakes**

- Don't name a file `mediapipe.py`, `cv2.py` or `djitellopy.py`. It hides the real library.
- `mled sc` clears the boot animation, not the screen. Use `d.show(BLANK)`.
- `get_distance_tof()` is the bottom sensor in cm. `d.tof()` is the front sensor in mm.
- Use `d.rc()` in loops and `move_*` for single steps. Don't mix them at the same moment.
- Markers need `mirror=False`. A mirrored code can't be read.

**Limits**

- The drone lands after 15 s with no commands, so keep calling `d.rc()` in loops.
- The front sensor reaches about 1.2 m, so keep `WALL` under 1200.
- Expect about 8 minutes per battery with the expansion kit.
- Lost the Wi-Fi password? Hold power for 5 s until the light flashes yellow.

**Network:** drone IP `192.168.10.1`. Commands use UDP 8889, state 8890, video 11111.
