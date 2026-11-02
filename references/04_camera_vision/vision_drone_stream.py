from djitellopy import Tello
import cv2

# Set up the Tello
tello = Tello()
tello.connect()  # Connect to the drone

# Check the battery
print(f"Battery remaining: {tello.get_battery()}%")

# Start the video stream
tello.streamon()

# Get video from the drone camera
frame_read = tello.get_frame_read()

# Set image width and height
frame_width = 640
frame_height = 480

try:
    while True:
        # Get the current frame
        frame = frame_read.frame
        frame = cv2.resize(frame, (frame_width, frame_height))  # Resize the image

        # Flip horizontally (if needed)
        frame = cv2.flip(frame, 1)

        # djitellopy 2.5 gives RGB frames; OpenCV windows expect BGR
        image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        image.flags.writeable = False  # Improves processing speed
        # Make the image writable again and convert back to BGR
        # image.flags.writeable = True
        # image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        cv2.imshow('Tello Tracking', image)
        # Press 'q' to leave the loop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
except KeyboardInterrupt:
    # Ctrl+C leaves the program
    pass
finally:
    # Release resources
    tello.streamoff()
    tello.end()
    cv2.destroyAllWindows()
