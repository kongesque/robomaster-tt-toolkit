from djitellopy import tello  # DJI Tello control package
import KeyPressModule as kp    # Custom key press module
from time import sleep         # sleep pauses the program
import time                    # time module, used for timestamps
import numpy as np             # NumPy, for maths and image arrays
import cv2                     # OpenCV, for image processing and display
import math                    # math module
import os                      # os module, used to create the photo folder

# Basic drone control settings
###### PARAMETERS #######
fSpeed = 150 / 10  # Forward speed (cm/s), about 15 cm/s at RC speed 15. Measure yours
aSpeed = 360 / 10  # Angular speed (deg/s), 360/10 = 36 deg/s
interval = 0.25    # Time interval (seconds)

dInterval = fSpeed * interval  # Distance moved per interval
aInterval = aSpeed * interval  # Angle changed per interval
############################################

# Starting drone position and angle
x, y = 500, 500  # Origin is the image center (500, 500)
a = 0            # Current movement angle
yaw = 0          # Drone yaw (rotation angle)

# Set up keyboard input
kp.init()
me = tello.Tello()  # Create the Tello object
me.connect()        # Connect to the drone
print(me.get_battery())  # Print the battery level
me.streamon()  # Start the live video stream

points = [(0, 0), (0, 0)]  # Records the flight path

# Function: read the keyboard and control the drone
def getKeyboardInput():
    lr, fb, ud, yv = 0, 0, 0, 0  # Reset left/right, forward/back, up/down and rotate speeds
    speed = 15  # Speed setting
    aspeed = 50  # Angular speed setting
    global x, y, yaw, a  # Use global variables
    d = 0  # Distance moved

    # Set movement direction and angle from the keys
    if kp.getKey("LEFT"):
        lr = -speed  # Move left
        d = dInterval  # Update distance
        a = -180  # Update angle
    elif kp.getKey("RIGHT"):
        lr = speed  # Move right
        d = -dInterval  # Update distance
        a = 180  # Update angle

    if kp.getKey("UP"):
        fb = speed  # Move forward
        d = dInterval  # Update distance
        a = 270  # Update angle
    elif kp.getKey("DOWN"):
        fb = -speed  # Move back
        d = -dInterval  # Update distance
        a = -90  # Update angle

    if kp.getKey("w"):
        ud = speed  # Move up

    elif kp.getKey("s"):
        ud = -speed  # Move down

    if kp.getKey("a"):
        yv = -aspeed  # Rotate left
        yaw -= aInterval  # Update yaw
    elif kp.getKey("d"):
        yv = aspeed  # Rotate right
        yaw += aInterval  # Update yaw

    if kp.getKey("q"):
        me.land()  # Land
    if kp.getKey("e"):
        me.takeoff()  # Take off

    if kp.getKey('z'):
        # Capture an image and save it, named by timestamp
        os.makedirs('Resources/Images', exist_ok=True)
        img2 = cv2.cvtColor(me.get_frame_read().frame, cv2.COLOR_RGB2BGR)
        cv2.imwrite(f'Resources/Images/{time.time()}.jpg', img2)
        time.sleep(0.3)  # Wait 0.3 seconds

    sleep(interval)  # Pause the program

    # Calculate the new position
    a += yaw  # Update angle
    x += int(d * math.cos(math.radians(a)))  # Calculate x
    y += int(d * math.sin(math.radians(a)))  # Calculate y

    return [lr, fb, ud, yv, x, y]  # Return control values and position

# Function: draw the flight path and current position
def drawPoints(img, points):
    # Draw the flight path
    for point in points:
        cv2.circle(img, point, 5, (0, 0, 255), cv2.FILLED)  # Past points in red

    # Draw the current position
    cv2.circle(img, points[-1], 8, (0, 255, 0), cv2.FILLED)  # Current position in green
    cv2.putText(img, f'({(points[-1][0] - 500) / 100},{(points[-1][1] - 500) / 100})m',
                (points[-1][0] + 10, points[-1][1] + 30), cv2.FONT_HERSHEY_PLAIN, 1,
                (255, 0, 255), 1)  # Show position in metres

# Main loop: read the keyboard, control the drone, update the display
try:
    while True:
        vals = getKeyboardInput()  # Read keyboard input
        me.send_rc_control(vals[0], vals[1], vals[2], vals[3])  # Send the control command

        # Create a 1000x1000 black image for the path
        img = np.zeros((1000, 1000, 3), np.uint8)

        # If the position changed, add it to the path
        if (points[-1][0] != vals[4] or points[-1][1] != vals[5]):
            points.append((vals[4], vals[5]))

        drawPoints(img, points)  # Draw the path and position
        cv2.imshow("Output", img)  # Show the image window

        # img2 = me.get_frame_read().frame  # Get the drone's live image
        # img2 = cv2.resize(img2, (360, 240))  # Resize the image
        # cv2.imshow("Image", img2)  # Show the live image

        cv2.waitKey(1)  # Wait 1 ms each loop
except KeyboardInterrupt:
    me.land()
