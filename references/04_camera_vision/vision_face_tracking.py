# Import the required libraries
from djitellopy import Tello  # Control the Tello drone
import cv2  # Image processing
import numpy as np
import time

# Set up the face classifier (OpenCV's Haar cascade)
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


tello = Tello()
tello.connect()
print(f"Battery: {tello.get_battery()}%")

# Start the video stream
tello.streamon()

# Set the image size
FRAME_W, FRAME_H = 640, 480

# PID values (proportional: pid[0], derivative: pid[1], integral: pid[2])
'''
Proportional: the bigger the error, the faster the turn
Integral: removes long-term offset when the system cannot reach the target. Too much I can cause oscillation or overshoot
Derivative: adds correction when the error changes fast, reducing shake
'''
pid = [0.4, 0.4, 0]
p_error = 0  # Previous error

# Center tolerance (pixels)
FACE_CENTER_THRESHOLD = 15

# Take off and climb
tello.takeoff()
tello.move_up(50)

try:
    while True:
        # Get a frame
        frame = tello.get_frame_read().frame
        frame = cv2.resize(frame, (FRAME_W, FRAME_H))
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # djitellopy 2.5 gives RGB
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        yaw_velocity = 0  # Reset the turn speed

        if len(faces) > 0:
            # Pick the biggest face
            x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
            cx, cy = x + w // 2, y + h // 2

            # Draw the box and center point
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 5, (0, 255, 0), cv2.FILLED)

            # Calculate the error
            error = cx - FRAME_W // 2

            # PID calculation
            speed = pid[0] * error + pid[1] * (error - p_error)
            speed = int(np.clip(speed, -100, 100))

            # Only turn when the error is past the threshold
            if abs(error) > FACE_CENTER_THRESHOLD:
                yaw_velocity = speed

            p_error = error  # Update the error
        else:
            p_error = 0

        # Send the control command
        tello.send_rc_control(0, 0, 0, yaw_velocity)

        # Show the image
        cv2.imshow("Tello Face Tracking", frame)

        # Press q to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            tello.land()
            break

except (Exception, KeyboardInterrupt) as e:
    print(f"Error: {e}")
    tello.land()

# Stop the stream and release resources
tello.streamoff()
tello.end()
cv2.destroyAllWindows()
