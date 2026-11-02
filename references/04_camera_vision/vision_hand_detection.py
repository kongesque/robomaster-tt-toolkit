"""
Hand detection program
Real-time hand detection and tracking with MediaPipe and OpenCV
Features: detect hand landmarks, draw the skeleton, identify left/right hand
"""

import cv2  # OpenCV image processing library
import mediapipe as mp  # Google MediaPipe hand detection library
import time  # Used to calculate FPS

# ============ Set up MediaPipe modules ============
mp_hands = mp.solutions.hands  # Hand detection solution
mp_drawing = mp.solutions.drawing_utils  # Drawing tools
mp_drawing_styles = mp.solutions.drawing_styles  # Default drawing styles

# ============ Set hand detection parameters ============
hands = mp_hands.Hands(
    static_image_mode=False,  # False: video stream mode, True: still image mode
    max_num_hands=2,  # Max hands to detect (1-2)
    min_detection_confidence=0.5,  # Detection confidence threshold (0.0-1.0), higher is stricter
    min_tracking_confidence=0.5  # Tracking confidence threshold (0.0-1.0), higher is steadier
)

# ============ Open the camera ============
cap = cv2.VideoCapture(0)  # 0 is the default camera; with several use 1, 2...
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Set frame width
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Set frame height

prev_time = 0  # Previous frame time, used for FPS

print("Hand detection program started...")
print("Press 'q' to quit")

# ============ Main detection loop ============

while cap.isOpened():
    # Read a camera frame
    success, image = cap.read()  # success: read worked, image: image array
    if not success:
        print("Cannot read camera frame")
        continue

    # ============ Image preprocessing ============
    image = cv2.flip(image, 1)  # Flip horizontally (mirror view feels natural)

    # Convert colour: BGR -> RGB (OpenCV uses BGR, MediaPipe needs RGB)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # ============ Run hand detection ============
    results = hands.process(image_rgb)  # Process the image, return results

    # ============ Calculate FPS (frames per second) ============
    curr_time = time.time()  # Current time
    fps = 1 / max(curr_time - prev_time, 1e-6)  # FPS = 1 / time difference
    prev_time = curr_time  # Update previous frame time

    # ============ Draw detection results ============
    # If hands are found (results.multi_hand_landmarks holds all detected hands)
    if results.multi_hand_landmarks:
        # Loop over each detected hand
        for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            # Draw the hand skeleton (21 landmarks + connections)
            mp_drawing.draw_landmarks(
                image,  # Image to draw on
                hand_landmarks,  # Hand landmark coordinates
                mp_hands.HAND_CONNECTIONS,  # Hand skeleton connections
                mp_drawing_styles.get_default_hand_landmarks_style(),  # Landmark style
                mp_drawing_styles.get_default_hand_connections_style()  # Connection style
            )

            # ============ Get hand information ============
            handedness = results.multi_handedness[hand_idx]  # Info for hand number hand_idx
            hand_label = handedness.classification[0].label  # Left or Right hand
            hand_score = handedness.classification[0].score  # Recognition confidence (0.0-1.0)

            # ============ Calculate text position ============
            h, w, c = image.shape  # Image height, width and channels
            wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]  # Wrist landmark
            wrist_x, wrist_y = int(wrist.x * w), int(wrist.y * h)  # Convert to pixel coordinates

            # Show hand type and confidence above the wrist
            cv2.putText(image, f'{hand_label} ({hand_score:.2f})',  # Text to show
                        (wrist_x - 50, wrist_y - 20),  # Text position (above the wrist)
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7,  # Font and size
                        (0, 255, 0), 2)  # Colour (green) and thickness

    # ============ Show statistics ============
    # Count detected hands
    hand_count = len(results.multi_hand_landmarks) if results.multi_hand_landmarks else 0

    # Show FPS (top left)
    cv2.putText(image, f'FPS: {int(fps)}', (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Show hand count (top left, second line)
    cv2.putText(image, f'Hands: {hand_count}', (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # ============ Show the window ============
    cv2.imshow('Hand Detection', image)  # Window title: Hand Detection

    # ============ Keyboard events ============
    # Wait 5 ms and check for the 'q' key
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break  # Press 'q' to leave the loop and end the program

# ============ Clean up ============
cap.release()  # Release the camera
cv2.destroyAllWindows()  # Close all OpenCV windows
hands.close()  # Close the MediaPipe hand model
print("Program ended")