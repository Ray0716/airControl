import cv2
import mediapipe as mp
import pyautogui

# Initialize MediaPipe Hands and PyAutoGUI
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)  # Use the default webcam


# Get screen dimensions
screen_width, screen_height = pyautogui.size()

# Start webcam
cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break
    
    # Flip the frame horizontally for a natural selfie view
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape  # Get dimensions of the frame
    
    # Convert the image to RGB for MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    # Process hand landmarks
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Get the tip of the index finger (landmark 8)
            x = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x
            y = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y
            
            # Map x, y to screen coordinates
            screen_x = int(x * screen_width)
            screen_y = int(y * screen_height)
            
            # Move the mouse
            pyautogui.moveTo(screen_x, screen_y)
            
            # Draw the hand landmarks on the frame
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # Show the webcam feed
    cv2.imshow('Virtual Mouse', frame)
    if cv2.waitKey(1) & 0xFF == 27:  # Exit on pressing 'Esc'
        break

cap.release()
cv2.destroyAllWindows()
