from  djitellopy import  tello

import KeyPressModule as kp
from time import  sleep

kp.init()
me = tello.Tello()
me.connect()
print(me.get_battery())

def getKeyboardInput():
    lr, fb, up, yv = 0, 0, 0, 0  # lr = left/right speed, fb = forward/back speed, up = up/down speed, yv = rotate speed
    speed = 50

    if kp.getKey("LEFT"): lr = -speed
    elif kp.getKey("RIGHT"): lr = speed

    if kp.getKey("UP"): fb = speed
    elif kp.getKey("DOWN"): fb = -speed

    if kp.getKey("w"): up = speed
    elif kp.getKey("s"): up = -speed

    if kp.getKey("a"): yv = -speed
    elif kp.getKey("d"): yv = speed

    if kp.getKey("q"): me.land()
    if kp.getKey("e"): me.takeoff()

    return [lr, fb, up, yv]

try:
    while True:
        vals = getKeyboardInput()
        me.send_rc_control(vals[0], vals[1], vals[2], vals[3])
        sleep(0.05)
except KeyboardInterrupt:
    me.land()



