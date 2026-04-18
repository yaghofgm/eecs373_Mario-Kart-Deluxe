import time
import cv2
import os
from datetime import datetime
from camera import Camera
from motorController import MotorController
from direction_classifier import LaneClassifier

def run_classifier_test_with_recording():
    # --- 1. Setup Folders ---
    save_folder = "debug_videos"
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = os.path.join(save_folder, f"debug_{timestamp}.mp4")

    print("⚠️ You have 20 seconds to unplug the monitor and keyboard! ⚠️")
    for i in range(20, 0, -1):
        print(f"Starting in {i}...")
        time.sleep(1)

    # --- 2. Initialize Hardware & Classifier ---
    cam = Camera()
    cam.open()
    motors = MotorController()
    classifier = LaneClassifier() 

    # --- 3. Setup Video Recorder ---
    # Get frame properties from the camera
    frame_width = int(cam.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cam.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = 15 # Matching the FPS set in your camera.py
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, fps, (frame_width, frame_height))

    print(f"GO! Recording RAW debug video to: {video_path}")
    
    speed = 17 
    lost_start_time = None # Tracks how long the line has been lost

    try:
        while True:
            ret, frame = cam.cap.read()
            if not ret:
                continue
            
            # --- 4. Process and Get Actions (No Visuals) ---
            action, _ = classifier.get_action(frame, return_visuals=False)
            
            # Write the RAW frame to the video file, with no filters or boxes
            out.write(frame)
            
            # --- 5. Motor Logic ---
            if action == "LOST":
                if lost_start_time is None:
                    # Start the timer the exact moment we lose the line
                    lost_start_time = time.time()
                    print("Line lost, starting 1-second timer...")
                
                # Check if it has been 1 second since we lost the line
                elif time.time() - lost_start_time >= 1.0:
                    print("Line LOST for over 1 second! Stopping.")
                    motors.stop()
                    break 
                
                # If it's been less than 1 second, it just loops again 
                # (holding whatever motor command it was last doing)
                
            else:
                # We see the line! Reset the timer if it was running
                if lost_start_time is not None:
                    print("Line re-acquired! Resetting timer.")
                    lost_start_time = None
                
                # Execute normal steering logic
                if action == "STRAIGHT":
                    motors.forward(speed)
                elif action == "TURN_LEFT":
                    motors.turn_left(speed)
                elif action == "TURN_RIGHT":
                    motors.turn_right(speed)
                elif action == "CRITICAL":
                    motors.stop()
                
    except KeyboardInterrupt:
        print("Test interrupted.")
    finally:
        # --- 6. Cleanup ---
        motors.stop()
        cam.close()
        out.release() # CRITICAL: properly saves the mp4 file
        print(f"Finished. Raw video saved to {video_path}")

if __name__ == "__main__":
    run_classifier_test_with_recording()