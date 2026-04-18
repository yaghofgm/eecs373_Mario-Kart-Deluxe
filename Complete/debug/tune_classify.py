import cv2
import numpy as np

# --- Initialization ---
video_path = "debug_videos/debug_20260417_172929.mp4"
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print(f"Error: Could not open {video_path}")
    exit()

total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
if total_frames <= 0:
    total_frames = 0
    while cap.read()[0]:
        total_frames += 1
cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

# Global playback state
playing = False

def nothing(x):
    pass

# --- NEW: Mouse Callback for Custom Button ---
def mouse_click(event, x, y, flags, param):
    global playing
    if event == cv2.EVENT_LBUTTONDOWN:
        # Check if click is within our custom button boundaries (X: 330-430, Y: 130-160)
        if 330 <= x <= 430 and 130 <= y <= 160:
            playing = not playing

# --- Window Setup ---
cv2.namedWindow("Controls", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Controls", 450, 650)
cv2.namedWindow("Tuner", cv2.WINDOW_NORMAL)
cv2.namedWindow("Mask", cv2.WINDOW_NORMAL) 

# Attach the mouse click detector to the Controls window
cv2.setMouseCallback("Controls", mouse_click)

# --- Trackbars ---
cv2.createTrackbar("Video Progress", "Controls", 0, total_frames - 1, nothing)

# HSV Detection
cv2.createTrackbar("Hue Min", "Controls", 0, 179, nothing)
cv2.createTrackbar("Hue Max", "Controls", 130, 179, nothing)
cv2.createTrackbar("Sat Min", "Controls", 0, 255, nothing)
cv2.createTrackbar("Sat Max", "Controls", 8, 255, nothing)
cv2.createTrackbar("Val Min", "Controls", 168, 255, nothing)
cv2.createTrackbar("Val Max", "Controls", 255, 255, nothing)

# Autonomous Driving Regions
cv2.createTrackbar("Ignore Top (%)", "Controls", 20, 100, nothing) 
cv2.createTrackbar("Center X (%)", "Controls", 50, 100, nothing)
cv2.createTrackbar("Green Half-Width (%)", "Controls", 17, 50, nothing)
cv2.createTrackbar("Yellow Thickness (%)", "Controls", 23, 50, nothing)

# Minimum white pixels needed to trigger a state
NOISE_THRESHOLD = 50 

current_frame_idx = -1
frame = None

while True:
    req_frame_idx = cv2.getTrackbarPos("Video Progress", "Controls")

    if req_frame_idx != current_frame_idx:
        if req_frame_idx != current_frame_idx + 1:
            cap.set(cv2.CAP_PROP_POS_FRAMES, req_frame_idx)
        ret, frame = cap.read()
        if not ret:
            playing = False
            continue
        current_frame_idx = req_frame_idx

    if frame is None:
        continue

    h, w = frame.shape[:2]
    
    h_min = cv2.getTrackbarPos("Hue Min", "Controls")
    h_max = cv2.getTrackbarPos("Hue Max", "Controls")
    s_min = cv2.getTrackbarPos("Sat Min", "Controls")
    s_max = cv2.getTrackbarPos("Sat Max", "Controls")
    v_min = cv2.getTrackbarPos("Val Min", "Controls")
    v_max = cv2.getTrackbarPos("Val Max", "Controls")
    
    ignore_top_val = cv2.getTrackbarPos("Ignore Top (%)", "Controls")
    center_val = cv2.getTrackbarPos("Center X (%)", "Controls")
    green_val = cv2.getTrackbarPos("Green Half-Width (%)", "Controls")
    yellow_val = cv2.getTrackbarPos("Yellow Thickness (%)", "Controls")

    # --- 1. Generate Mask & Apply Throwaway Region ---
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lo = np.array([h_min, s_min, v_min])
    hi = np.array([h_max, s_max, v_max])
    mask = cv2.inRange(hsv, lo, hi)

    ignore_h = int(h * (ignore_top_val / 100.0))
    mask[0:ignore_h, :] = 0 

    # --- 2. Calculate Region Boundaries ---
    cx = int(w * (center_val / 100.0))
    green_hw = int(w * (green_val / 100.0))
    yellow_th = int(w * (yellow_val / 100.0))

    g_left = max(0, cx - green_hw)
    g_right = min(w, cx + green_hw)
    y_left = max(0, g_left - yellow_th)
    y_right = min(w, g_right + yellow_th)

    # --- 3. DECISION ENGINE: Count pixels in each zone ---
    px_green = cv2.countNonZero(mask[:, g_left:g_right])
    
    px_yellow_left = cv2.countNonZero(mask[:, y_left:g_left])
    px_yellow_right = cv2.countNonZero(mask[:, g_right:y_right])
    
    px_red_left = cv2.countNonZero(mask[:, 0:y_left])
    px_red_right = cv2.countNonZero(mask[:, y_right:w])

    action_text = "LOST: SPECIAL FUNCTION"
    action_color = (200, 200, 200)

    if px_red_left > NOISE_THRESHOLD or px_red_right > NOISE_THRESHOLD:
        action_text = "CRITICAL: RED ZONE EXTREME CORRECT"
        action_color = (0, 0, 255)
    elif px_yellow_left > NOISE_THRESHOLD:
        action_text = "CORRECTING: TURN RIGHT ->"
        action_color = (0, 255, 255)
    elif px_yellow_right > NOISE_THRESHOLD:
        action_text = "<- CORRECTING: TURN LEFT"
        action_color = (0, 255, 255)
    elif px_green > NOISE_THRESHOLD:
        action_text = "GOOD: DRIVING STRAIGHT"
        action_color = (0, 255, 0)

    # --- 4. Draw Visuals ---
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 255), -1) 
    cv2.rectangle(overlay, (y_left, 0), (y_right, h), (0, 255, 255), -1) 
    cv2.rectangle(overlay, (g_left, 0), (g_right, h), (0, 255, 0), -1) 
    cv2.rectangle(overlay, (0, 0), (w, ignore_h), (50, 50, 50), -1)

    display = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)
    display[mask > 0] = [255, 255, 255] 

    cv2.putText(display, f"ACTION: {action_text}", (10, 80), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, action_color, 2)

    # --- 5. Dashboard ---
    dashboard = np.zeros((175, 450, 3), dtype=np.uint8)
    cv2.putText(dashboard, "HSV Filters:", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(dashboard, f"Hue: {h_min:3} -> {h_max:3}", (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    cv2.putText(dashboard, f"Sat: {s_min:3} -> {s_max:3}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    cv2.putText(dashboard, f"Val: {v_min:3} -> {v_max:3}", (20, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    cv2.putText(dashboard, "Lane Regions:", (220, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(dashboard, f"Center: {center_val}%", (230, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(dashboard, f"Green : {green_val}% width", (230, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    cv2.putText(dashboard, f"Yellow: {yellow_val}% thick", (230, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    cv2.putText(dashboard, f"Ignore Top: {ignore_top_val}%", (230, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

    # --- NEW: Draw Play/Pause Button on Dashboard ---
    btn_color = (0, 200, 0) if not playing else (0, 0, 200) # Green for Play, Red for Pause
    btn_text = "PLAY" if not playing else "PAUSE"
    cv2.rectangle(dashboard, (330, 130), (430, 160), btn_color, -1)
    cv2.putText(dashboard, btn_text, (345, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow("Controls", dashboard)
    cv2.imshow("Tuner", display)
    cv2.imshow("Mask", mask) 

    key = cv2.waitKey(30) & 0xFF
    if key == ord('q'):
        break
    elif key == ord(' '):
        playing = not playing

    if playing:
        next_frame = (current_frame_idx + 1) % total_frames
        cv2.setTrackbarPos("Video Progress", "Controls", next_frame)

cap.release()
cv2.destroyAllWindows()