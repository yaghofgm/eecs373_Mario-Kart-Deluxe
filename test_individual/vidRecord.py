import cv2
import time

# Open the camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Get the native resolution of the camera
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Set up the VideoWriter
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
fps = 20.0  # Adjust if playback is too fast/slow
output_filename = 'output_flat_3.mp4'

out = cv2.VideoWriter(output_filename, fourcc, fps, (frame_width, frame_height))

print(f"Headless recording started. Saving to {output_filename}.")
print("Recording for 80 seconds. You can unplug the monitor now...")

start_time = time.time()
duration_limit = 120  # seconds

try:
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("Error: Failed to grab frame.")
            break
            
        # Save the frame to our video file (No imshow!)
        out.write(frame)
        
        # Check elapsed time
        elapsed_time = time.time() - start_time
        if elapsed_time >= duration_limit:
            print(f"Successfully recorded for {duration_limit} seconds.")
            break

except KeyboardInterrupt:
    # This allows you to safely stop it with Ctrl+C if you are still plugged in
    print("\nRecording stopped by user.")

finally:
    # CLEANUP: This is the most important part!
    # Even if the script errors out, the 'finally' block ensures the video file 
    # is properly sealed so it doesn't turn into a "text file".
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print("Done. Video file safely closed.")
