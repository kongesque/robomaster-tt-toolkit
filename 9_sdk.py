"""Type raw SDK commands and see the reply. Type quit to leave.

Try: battery?   EXT tof?   EXT mled s r A   EXT led 0 255 0   takeoff   land
"""
from kit import *

with Drone() as d:
    while True:
        cmd = input("sdk> ").strip()
        if cmd == "quit":
            break
        if cmd == "takeoff":
            d.takeoff()  # so the kit knows to land when you quit
        elif cmd == "land":
            d.land()
        elif cmd:
            print(d.t.send_command_with_return(cmd, timeout=10))
