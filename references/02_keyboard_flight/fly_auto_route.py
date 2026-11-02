from djitellopy import Tello

tello = Tello()

tello.connect()
tello.takeoff()

try:
    tello.move_left(20)  # 20 cm is the minimum
    tello.rotate_clockwise(90)
    tello.move_forward(20)
finally:
    tello.land()