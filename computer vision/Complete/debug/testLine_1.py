import time
import cv2
from camera import Camera
from motorController import MotorController
from direction_classifier import LaneClassifier

def run_classifier_test():
    print("⚠️ You have 120 seconds to unplug the monitor and keyboard! ⚠️")
    for i in range(20, 0, -1):
        print(f"Starting in {i}...")
        time.sleep(1)

    # Initialize Hardware and Classifier
    cam = Camera()
    cam.open()
    motors = MotorController()
    
    # Using the default HSV parameters in your LaneClassifier 
    # which seem already tuned for white lines (low saturation, high value)
    classifier = LaneClassifier() 

    print("GO! Driving via LaneClassifier. Will stop if the line is LOST...")
    
    speed = 20 # Safe testing speed

    try:
        while True:
            ret, frame = cam.cap.read()
            if not ret:
                print("Warning: Missed a frame.")
                continue
            
            # Ask the classifier what to do based on the current frame
            action, _ = classifier.get_action(frame, return_visuals=False)
            
            # Map the classifier's action to the motor controller
            if action == "STRAIGHT":
                motors.forward(speed)
            elif action == "TURN_LEFT":
                motors.turn_left(speed)
            elif action == "TURN_RIGHT":
                motors.turn_right(speed)
            elif action == "CRITICAL":
                # Critical usually means it's right on the edge or confused
                # Slowing down or stopping briefly is safest
                motors.stop()
            elif action == "LOST":
                print("Line LOST! Stopping the car.")
                motors.stop()
                break # Exit the loop
                
    except KeyboardInterrupt:
        print("Test interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Safety net: ALWAYS stop motors and release camera
        motors.stop()
        cam.close()
        print("Hardware safely shut down. Test complete.")

if __name__ == "__main__":
    run_classifier_test()
