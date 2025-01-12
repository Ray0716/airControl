import cv2
import mediapipe as mp
import pyautogui
import time
import threading



# Initialize MediaPipe Hands and PyAutoGUI
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)  # Use the default webcam


# Get screen dimensions
screen_width, screen_height = pyautogui.size()


BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode


options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path='/path/to/model.task'),
    running_mode=VisionRunningMode.VIDEO, num_hands=2)


can_pinch_index_finger = True
can_fist = True


def is_pinch_index_finger(landmarks):
    global can_pinch_index_finger
    
    # Get the thumb and index finger tip landmarks
    thumb_tip = landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]

    # Calculate the Euclidean distance between thumb_tip and index_tip
    distance = ((thumb_tip.x - index_tip.x) ** 2 + (thumb_tip.y - index_tip.y) ** 2 + (thumb_tip.z - index_tip.z) ** 2) ** 0.5

    # Define a threshold for the pinch (this value may need to be adjusted)
    pinch_threshold = 0.05

    # Return True if the distance between the thumb and index tip is smaller than the threshold
    
    

    if can_pinch_index_finger and (distance < pinch_threshold):

        threading.Timer(0.5, enable_pinch_index_finger).start()  # Set the timer to reset the flag after 1 second
        can_pinch_index_finger = False
        return True
    else: 
        return False

def is_pinch_middle_finger(landmarks):
    # Get the thumb and index finger tip landmarks
    thumb_tip = landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    middle_tip = landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

    # Calculate the Euclidean distance between thumb_tip and index_tip
    distance = ((thumb_tip.x - middle_tip.x) ** 2 + (thumb_tip.y - middle_tip.y) ** 2 + (thumb_tip.z - middle_tip.z) ** 2) ** 0.5

    # Define a threshold for the pinch (this value may need to be adjusted)
    pinch_threshold = 0.1

    # Return True if the distance between the thumb and middle tip is smaller than the threshold
    return distance < pinch_threshold


def is_fist(hand_landmarks):
    global can_fist
    # Landmarks for fingertips
    finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky fingertips
    finger_folded = True

    for tip in finger_tips:
        # Check if fingertip is below its corresponding middle knuckle
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            finger_folded = False
            break

    # Thumb check: Tip (4) should be near the wrist or below knuckle (2)
    thumb_folded = hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x

    
    if can_fist and (finger_folded and thumb_folded):
        threading.Timer(0.5, enable_fist).start()  # Set the timer to reset the flag after 1 second
        can_fist = False
        return True
    else: 
        return False


def enable_pinch_index_finger():
    global can_pinch_index_finger
    can_pinch_index_finger = True

def enable_fist():
    global can_fist
    can_fist = True


mouse_down = False 

coordinate_history = [] # get a log of history of positions 
deadzone = 0.006

stabilized_x = 0.5
stabilized_y = 0.5

stabilization_watch_back_index = 5 # NEEDS TO BE LESS THAN THE LENGHT OF WATCH BACKHISTORY STACK!!!!!

averaging_amount = 5

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
            x = (hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x) + float(-0.1) # -0.1 for right hand, 0.1 for left
            y = (hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].y) + float(-0.4) # y offset 
            z = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].z
            
            #add the curr coords to history
            coordinate_history.append([x, y])
            # Separate x and y values
            x_values = [pair[0] for pair in coordinate_history]
            y_values = [pair[1] for pair in coordinate_history]

            if len(coordinate_history) == 1:
                x_val_avg_list = x_values[:-1]
                y_val_avg_list = y_values[:-1]


            #calc deadzones
            # if not first time
            if len(coordinate_history) <= stabilization_watch_back_index: #if first time
                stabilized_x = x
                stabilized_y = y
                deadzone_watchback_x = x
                deadzone_watchback_y = y


            if(abs(deadzone_watchback_x - x) >= deadzone): #if it move out of deadzone
                stabilized_x = x
            
            if(abs(deadzone_watchback_y - y) >= deadzone): #if it move out of deadzone
                stabilized_y = y


            # Calculate averages (comment out if no want average)
            if len(coordinate_history) >= 2:
                x_val_avg_list = x_values[-(averaging_amount):-1]
                y_val_avg_list = y_values[-(averaging_amount):-1]
                average_x = sum(x_val_avg_list) / len(x_val_avg_list)
                average_y = sum(y_val_avg_list) / len(y_val_avg_list)


            # Map x, y to screen coordinates
            screen_x = int(stabilized_x * screen_width)
            screen_y = int(stabilized_y * screen_height)


            # if not first time, add deadzonewatchack x and y
            if len(coordinate_history) >= stabilization_watch_back_index:
                deadzone_watchback_x = x_values[-(stabilization_watch_back_index - 1)]
                deadzone_watchback_y = y_values[-(stabilization_watch_back_index - 1)]
            

            # delet first element of list
            if len(coordinate_history) >= 30: #30 is history list length
                del coordinate_history[0]

            
            
            # Move the mouse
            pyautogui.moveTo(screen_x, screen_y)
            
            thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
            middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

            pinchIndex = is_pinch_index_finger(hand_landmarks)
            pinchMiddle = is_pinch_middle_finger(hand_landmarks)
            isFist = is_fist(hand_landmarks)

            #print(pinchIndex, pinchMiddle, coordinate_history)
            print(pinchIndex, pinchMiddle, isFist, x_val_avg_list, y_val_avg_list)

            
            if pinchIndex:
                pyautogui.click(screen_x, screen_y)
                print("clicked")

            if pinchMiddle:
                """start_x = int((thumb_tip.x + middle_tip.x) / 2 * screen_width)
                start_y = int((thumb_tip.y + middle_tip.y) / 2 * screen_height)"""
        
                # # Click the mouse at the starting position
                # pyautogui.mouseDown(start_x, start_y)
                if not mouse_down:
                    mouse_down = True
                    pyautogui.mouseDown(screen_x, screen_y)
                """ else:
                    pyautogui.moveTo(start_x, start_y)
                    print(f"Mouse moved to ({start_x}, {start_y})")"""
                    # # Small delay to prevent excessive CPU usage (you can adjust this value)
                    # if not pinchMiddle:
                    #     pyautogui.mouseUp()
                    #     mouse_down = False
                    #     break
            else:
                if mouse_down: # do we need this condition?
                    pyautogui.mouseUp()
                    mouse_down = False

            if isFist:
                pyautogui.hotkey('ctrl', 'up')



            displayString = (str(pinchIndex) + ": pindex, " + str(pinchMiddle) + ": pmid, cursorXcoord: " + str(x) + "cursorY" + str(y))
            # Define text parameters
            text = displayString
            org = (30, 30)  # Bottom-left corner of the text
            org2 = (30, 50)
            font = cv2.FONT_HERSHEY_DUPLEX
            fontScale = 1
            color = (0, 0, 255)  # Blue color in BGR
            thickness = 2

            # Add text to the image
            cv2.putText(frame, text, org, font, fontScale, color, thickness, cv2.LINE_AA)

            #cv2.putText(frame, str("screenx: " + str(screen_x) + ", scry:" + str(screen_y)), org2, int(fontScale), color, thickness, cv2.LINE_AA)

            # Draw the hand landmarks on the frame
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
               

                

    # Show the webcam feed
    cv2.imshow('Virtual Mouse', frame)
    if cv2.waitKey(1) & 0xFF == 27:  # Exit on pressing 'Esc'
        break



    #is_pinch_index_finger(landmarks)

cap.release()
cv2.destroyAllWindows()
