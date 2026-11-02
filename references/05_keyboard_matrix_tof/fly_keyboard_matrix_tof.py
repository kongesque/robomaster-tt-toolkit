from djitellopy import tello
import KeyPressModule as kp
from time import sleep, time

kp.init()
me = tello.Tello()
me.connect()

print("Battery:", me.get_battery())

SPEED = 50
VERTICAL_SPEED = 20
YAW_SPEED = 35
WALL_DISTANCE = 500  # mm

flying = False
previous_e = False
previous_q = False
last_display = None
last_tof_check = 0
tof_distance = 8192

# 8x8 matrix patterns
ARROW_UP = (
    "000bb000"
    "00bbbb00"
    "0bbbbbb0"
    "000bb000"
    "000bb000"
    "000bb000"
    "000bb000"
    "00000000"
)

ARROW_DOWN = (
    "000bb000"
    "000bb000"
    "000bb000"
    "000bb000"
    "0bbbbbb0"
    "00bbbb00"
    "000bb000"
    "00000000"
)

ARROW_RIGHT = (
    "000b0000"
    "00bb0000"
    "0bbbbbbb"
    "bbbbbbbb"
    "0bbbbbbb"
    "00bb0000"
    "000b0000"
    "00000000"
)

ARROW_LEFT = (
    "0000b000"
    "0000bb00"
    "bbbbbbb0"
    "bbbbbbbb"
    "bbbbbbb0"
    "0000bb00"
    "0000b000"
    "00000000"
)

RED_X = (
    "r000000r"
    "0r0000r0"
    "00r00r00"
    "000rr000"
    "000rr000"
    "00r00r00"
    "0r0000r0"
    "r000000r"
)

CLEAR = "0" * 64


def set_display(pattern, led):
    global last_display

    state = (pattern, led)
    if state == last_display:
        return

    me.send_expansion_command("mled g " + pattern)

    if led == "green":
        me.send_expansion_command("led 0 255 0")
    elif led == "red":
        me.send_expansion_command("led 255 0 0")
    elif led == "off":
        me.send_expansion_command("led 0 0 0")

    last_display = state


def read_tof():
    try:
        response = me.send_command_with_return("EXT tof?", timeout=1)
        if isinstance(response, str):
            value = response.lower().replace("tof", "").strip()
            return int(value)
    except Exception:
        pass

    return 8192


def get_keyboard_input():
    global flying
    global previous_e, previous_q
    global last_tof_check, tof_distance

    lr, fb, ud, yv = 0, 0, 0, 0
    movement_pattern = None

    # Read ToF at a lower rate than RC control.
    if time() - last_tof_check >= 0.15:
        tof_distance = read_tof()
        last_tof_check = time()

    wall_close = 0 < tof_distance < WALL_DISTANCE

    # W / S = forward / backward
    if kp.getKey("w"):
        if wall_close:
            fb = 0
        else:
            fb = SPEED
            movement_pattern = ARROW_UP
    elif kp.getKey("s"):
        fb = -SPEED
        movement_pattern = ARROW_DOWN

    # A / D = strafe left / right
    if kp.getKey("a"):
        lr = -SPEED
        movement_pattern = ARROW_LEFT
    elif kp.getKey("d"):
        lr = SPEED
        movement_pattern = ARROW_RIGHT

    # Up / Down arrows = altitude
    if kp.getKey("UP"):
        ud = VERTICAL_SPEED
        movement_pattern = ARROW_UP
    elif kp.getKey("DOWN"):
        ud = -VERTICAL_SPEED
        movement_pattern = ARROW_DOWN

    # Left / Right arrows = rotate
    if kp.getKey("LEFT"):
        yv = -YAW_SPEED
    elif kp.getKey("RIGHT"):
        yv = YAW_SPEED

    # SPACE = immediate hover (zero RC movement)
    if kp.getKey("SPACE"):
        lr, fb, ud, yv = 0, 0, 0, 0
        movement_pattern = None

    # E = takeoff, once per press
    e_pressed = kp.getKey("e")
    if e_pressed and not previous_e and not flying:
        print("TAKEOFF")
        movement_pattern = ARROW_UP
        me.takeoff()
        flying = True
    previous_e = e_pressed

    # Q = land, once per press
    q_pressed = kp.getKey("q")
    if q_pressed and not previous_q and flying:
        print("LANDING")
        movement_pattern = ARROW_DOWN
        me.land()
        flying = False
    previous_q = q_pressed

    # Display behavior
    if wall_close:
        set_display(RED_X, "red")
    elif movement_pattern is not None:
        set_display(movement_pattern, "green")

    return lr, fb, ud, yv


print("""
================================
       ROBOMASTER TT CONTROL
================================
W / S       Forward / Backward
A / D       Move Left / Right

UP / DOWN   Ascend / Descend
LEFT/RIGHT  Rotate Left / Right

E           Takeoff
Q           Land
SPACE       Hover / Stop movement

Display:
- Movement: blue arrow + green LED
- Wall < 50 cm: red X + red LED
================================
""")

me.send_expansion_command("mled sl 255")

try:
    while True:
        lr, fb, ud, yv = get_keyboard_input()

        if flying:
            me.send_rc_control(lr, fb, ud, yv)

        sleep(0.05)

except KeyboardInterrupt:
    pass

finally:
    print("Stopping...")

    if flying:
        me.send_rc_control(0, 0, 0, 0)
        me.land()

    set_display(CLEAR, "off")
