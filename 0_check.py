"""Hardware check: battery, ToF, matrix, top LED. Motors stay off."""
from kit import *

with Drone() as d:
    print("Battery:", d.battery(), "%")
    print("Front ToF:", d.tof(), "mm")  # 8192 = nothing in range

    # Show each arrow
    for name, arrow in [("UP", ARROW_UP), ("DOWN", ARROW_DOWN), ("LEFT", ARROW_LEFT), ("RIGHT", ARROW_RIGHT)]:
        print("Matrix:", name, "- if left/right look backwards, set SWAP_LR_ARROWS in kit.py")
        d.show(arrow)
        time.sleep(1.5)

    # Show each LED colour
    for name, color in [("green", GREEN), ("red", RED), ("off", OFF)]:
        print("Top LED:", name)
        d.led(color)
        time.sleep(0.7)

    d.show(CHECK)  # tick = all done
    time.sleep(1)
print("Check done.")
