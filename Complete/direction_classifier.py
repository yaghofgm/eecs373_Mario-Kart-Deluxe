import cv2
import numpy as np

class LaneClassifier:
    def __init__(self, 
                 hsv_min=(0, 0, 180), 
                 hsv_max=(140, 8, 255), 
                 center_pct=50, 
                 green_hw_pct=17, 
                 yellow_thick_pct=23, 
                 ignore_top_pct=35, 
                 noise_threshold=50):
        """
        Initializes the Lane Classifier with tuned vision parameters.
        """
        # HSV Filters
        self.lower_hsv = np.array(hsv_min)
        self.upper_hsv = np.array(hsv_max)
        
        # Region Geometry (Percentages)
        self.center_pct = center_pct / 100.0
        self.green_hw_pct = green_hw_pct / 100.0
        self.yellow_thick_pct = yellow_thick_pct / 100.0
        self.ignore_top_pct = ignore_top_pct / 100.0
        
        # Noise Filtering
        self.noise_thresh = noise_threshold

    def get_action(self, frame, return_visuals=False):
        """
        Processes a single BGR frame and returns a driving command.
        Returns:
            action (str): "STRAIGHT", "TURN_LEFT", "TURN_RIGHT", "CRITICAL", or "LOST"
            display (numpy array, optional): The visual debug frame
        """
        h, w = frame.shape[:2]

        # --- 1. Generate Mask & Apply Throwaway Region ---
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_hsv, self.upper_hsv)

        # Zero out the ignored top region
        ignore_h = int(h * self.ignore_top_pct)
        mask[0:ignore_h, :] = 0 

        # --- 2. Calculate Region Boundaries ---
        cx = int(w * self.center_pct)
        green_hw = int(w * self.green_hw_pct)
        yellow_th = int(w * self.yellow_thick_pct)

        g_left = max(0, cx - green_hw)
        g_right = min(w, cx + green_hw)
        y_left = max(0, g_left - yellow_th)
        y_right = min(w, g_right + yellow_th)

        # --- 3. DECISION ENGINE: Count pixels ---
        px_green = cv2.countNonZero(mask[:, g_left:g_right])
        px_yellow_left = cv2.countNonZero(mask[:, y_left:g_left])
        px_yellow_right = cv2.countNonZero(mask[:, g_right:y_right])
        px_red_left = cv2.countNonZero(mask[:, 0:y_left])
        px_red_right = cv2.countNonZero(mask[:, y_right:w])

        # --- 4. Determine Action State ---
        # Outputting standard strings makes it easy for your car logic to parse
        action = "LOST"
        
        if px_red_left > self.noise_thresh or px_red_right > self.noise_thresh:
            action = "CRITICAL"
        elif px_yellow_left > self.noise_thresh:
            action = "TURN_LEFT"
        elif px_yellow_right > self.noise_thresh:
            action = "TURN_RIGHT"
        elif px_green > self.noise_thresh:
            action = "STRAIGHT"

        # --- 5. Optional Debug Visuals ---
        if not return_visuals:
            return action, None
            
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 255), -1) 
        cv2.rectangle(overlay, (y_left, 0), (y_right, h), (0, 255, 255), -1) 
        cv2.rectangle(overlay, (g_left, 0), (g_right, h), (0, 255, 0), -1) 
        cv2.rectangle(overlay, (0, 0), (w, ignore_h), (50, 50, 50), -1)

        display = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)
        display[mask > 0] = [255, 255, 255] 

        # Add text overlay based on action
        color_map = {
            "CRITICAL": (0, 0, 255),
            "TURN_RIGHT": (0, 255, 255),
            "TURN_LEFT": (0, 255, 255),
            "STRAIGHT": (0, 255, 0),
            "LOST": (200, 200, 200)
        }
        cv2.putText(display, f"CMD: {action}", (10, ignore_h + 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_map[action], 2)

        return action, display