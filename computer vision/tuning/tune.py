"""
Lane Detection Parameter Tuner
================================
Run this script to interactively tune parameters for:
  - HSV color thresholding (white lane lines + blue finish line)
  - Canny edge detection
  - Hough line transform
  - Region of interest (ROI)

Usage:
    python tune_lane_params.py --source video.mp4
    python tune_lane_params.py --source 0          # live camera (index 0)
    python tune_lane_params.py --source image.png  # single image

Controls:
    SPACE  - pause/resume video
    S      - save current parameters to lane_params.json
    Q      - quit
"""

import cv2
import numpy as np
import json
import argparse
import sys

# ── Saved parameter output file ──────────────────────────────────────────────
PARAM_FILE = "lane_params.json"

# ── OpenCV version check (3.x returns 3 values, 4.x returns 2) ───────────────
CV_MAJOR = int(cv2.__version__.split(".")[0])

def find_contours(mask):
    """Version-safe wrapper: OpenCV 3.x returns (image, contours, hierarchy),
    OpenCV 4.x returns (contours, hierarchy)."""
    result = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if CV_MAJOR >= 4:
        contours, hierarchy = result
    else:
        _, contours, hierarchy = result
    return contours, hierarchy

# ── Default parameter values ─────────────────────────────────────────────────
params = {
    # Gaussian blur kernel size (must be odd)
    "blur_k": 5,

    # Canny edge detection
    "canny_low": 50,
    "canny_high": 150,

    # Hough line transform
    "hough_threshold": 40,     # min votes
    "hough_min_len": 30,       # min line length (px)
    "hough_max_gap": 20,       # max gap between segments (px)

    # ROI: fraction of frame height from the TOP to start the ROI mask
    # e.g. 0.4 means ignore the top 40% of the frame
    "roi_top_frac": 0.40,

    # White line HSV thresholds
    "white_h_low":  0,   "white_h_high":  180,
    "white_s_low":  0,   "white_s_high":   60,
    "white_v_low": 180,  "white_v_high":  255,

    # Blue finish-line HSV thresholds
    "blue_h_low":  90,  "blue_h_high": 130,
    "blue_s_low":  80,  "blue_s_high": 255,
    "blue_v_low":  80,  "blue_v_high": 255,
}

# ── Trackbar window name ──────────────────────────────────────────────────────
WIN_CTRL   = "Controls"
WIN_EDGES  = "Edges"
WIN_MASK_W = "White mask"
WIN_MASK_B = "Blue mask"
WIN_OUT    = "Lane detection output"

# OpenCV 3.x returns (image, contours, hierarchy); 4.x returns (contours, hierarchy)
CV_MAJOR = int(cv2.__version__.split(".")[0])


def find_contours(mask):
    if CV_MAJOR >= 4:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    else:
        _, contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours


def nothing(_): pass


def create_trackbars():
    cv2.namedWindow(WIN_CTRL, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN_CTRL, 420, 700)

    def tb(name, val, maxval):
        cv2.createTrackbar(name, WIN_CTRL, val, maxval, nothing)

    # Blur
    tb("Blur kernel",      params["blur_k"] // 2, 10)   # stored as half (×2+1)

    # Canny
    tb("Canny low",        params["canny_low"],   255)
    tb("Canny high",       params["canny_high"],  255)

    # Hough
    tb("Hough threshold",  params["hough_threshold"], 200)
    tb("Hough min len",    params["hough_min_len"],   200)
    tb("Hough max gap",    params["hough_max_gap"],   100)

    # ROI
    tb("ROI top %",        int(params["roi_top_frac"] * 100), 90)

    # White HSV
    tb("W H low",   params["white_h_low"],   180)
    tb("W H high",  params["white_h_high"],  180)
    tb("W S low",   params["white_s_low"],   255)
    tb("W S high",  params["white_s_high"],  255)
    tb("W V low",   params["white_v_low"],   255)
    tb("W V high",  params["white_v_high"],  255)

    # Blue HSV
    tb("B H low",   params["blue_h_low"],   180)
    tb("B H high",  params["blue_h_high"],  180)
    tb("B S low",   params["blue_s_low"],   255)
    tb("B S high",  params["blue_s_high"],  255)
    tb("B V low",   params["blue_v_low"],   255)
    tb("B V high",  params["blue_v_high"],  255)


def read_trackbars():
    def g(name): return cv2.getTrackbarPos(name, WIN_CTRL)

    bk = g("Blur kernel") * 2 + 1   # ensure odd
    params["blur_k"]          = max(1, bk)
    params["canny_low"]       = g("Canny low")
    params["canny_high"]      = g("Canny high")
    params["hough_threshold"] = max(1, g("Hough threshold"))
    params["hough_min_len"]   = max(1, g("Hough min len"))
    params["hough_max_gap"]   = max(0, g("Hough max gap"))
    params["roi_top_frac"]    = g("ROI top %") / 100.0

    params["white_h_low"]  = g("W H low")
    params["white_h_high"] = g("W H high")
    params["white_s_low"]  = g("W S low")
    params["white_s_high"] = g("W S high")
    params["white_v_low"]  = g("W V low")
    params["white_v_high"] = g("W V high")

    params["blue_h_low"]   = g("B H low")
    params["blue_h_high"]  = g("B H high")
    params["blue_s_low"]   = g("B S low")
    params["blue_s_high"]  = g("B S high")
    params["blue_v_low"]   = g("B V low")
    params["blue_v_high"]  = g("B V high")


def make_roi_mask(frame):
    """Trapezoidal ROI: ignore the top roi_top_frac of the frame."""
    h, w = frame.shape[:2]
    top_y = int(h * params["roi_top_frac"])
    mask = np.zeros((h, w), dtype=np.uint8)
    pts = np.array([[0, top_y], [w, top_y], [w, h], [0, h]], dtype=np.int32)
    cv2.fillPoly(mask, [pts], 255)
    return mask


def process_frame(frame):
    h, w = frame.shape[:2]
    output = frame.copy()

    # ── 1. Colour-space and blur ──────────────────────────────────────────────
    blurred = cv2.GaussianBlur(frame, (params["blur_k"], params["blur_k"]), 0)
    hsv     = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # ── 2. Color masks ────────────────────────────────────────────────────────
    white_mask = cv2.inRange(
        hsv,
        (params["white_h_low"], params["white_s_low"], params["white_v_low"]),
        (params["white_h_high"], params["white_s_high"], params["white_v_high"])
    )
    blue_mask = cv2.inRange(
        hsv,
        (params["blue_h_low"], params["blue_s_low"], params["blue_v_low"]),
        (params["blue_h_high"], params["blue_s_high"], params["blue_v_high"])
    )

    # ── 3. ROI ────────────────────────────────────────────────────────────────
    roi_mask    = make_roi_mask(frame)
    white_roi   = cv2.bitwise_and(white_mask, roi_mask)
    blue_roi    = cv2.bitwise_and(blue_mask,  roi_mask)

    # ── 4. Canny on white mask ────────────────────────────────────────────────
    edges = cv2.Canny(white_roi, params["canny_low"], params["canny_high"])

    # ── 5. Hough lines ────────────────────────────────────────────────────────
    lines = cv2.HoughLinesP(
        edges,
        rho=1, theta=np.pi/180,
        threshold=params["hough_threshold"],
        minLineLength=params["hough_min_len"],
        maxLineGap=params["hough_max_gap"]
    )

    # Draw lane lines
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(output, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # ── Estimate steering error ───────────────────────────────────────────
        xs = [(l[0][0] + l[0][2]) / 2 for l in lines]
        center_x = int(np.mean(xs))
        frame_cx  = w // 2
        error = center_x - frame_cx

        cv2.line(output, (center_x, h - 20), (center_x, h - 60), (0, 255, 0), 2)
        cv2.line(output, (frame_cx,  h - 20), (frame_cx,  h - 60), (255, 0, 0), 2)
        cv2.putText(output, f"Steering error: {error:+d}px",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Overlay blue finish line detection
    blue_contours = find_contours(blue_roi)
    if blue_contours:
        largest = max(blue_contours, key=cv2.contourArea)
        if cv2.contourArea(largest) > 500:
            cv2.drawContours(output, [largest], -1, (255, 100, 0), 3)
            cv2.putText(output, "FINISH LINE DETECTED",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 100, 0), 2)

    # Draw ROI boundary
    top_y = int(h * params["roi_top_frac"])
    cv2.line(output, (0, top_y), (w, top_y), (0, 200, 255), 1)

    return output, edges, white_roi, blue_roi


def save_params():
    with open(PARAM_FILE, "w") as f:
        json.dump(params, f, indent=2)
    print(f"[tuner] Parameters saved to {PARAM_FILE}")


def main():
    parser = argparse.ArgumentParser(description="Lane detection parameter tuner")
    parser.add_argument("--source", default="0",
                        help="Video file path, image path, or camera index (default: 0)")
    args = parser.parse_args()

    # Determine source type
    src = args.source
    try:
        src = int(src)   # camera index
    except ValueError:
        pass             # file path

    # Open source
    if isinstance(src, str) and src.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
        # Single image mode
        frame_orig = cv2.imread(src)
        if frame_orig is None:
            print(f"[tuner] ERROR: Could not open image: {src}")
            sys.exit(1)
        video_mode = False
    else:
        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            print(f"[tuner] ERROR: Could not open source: {src}")
            sys.exit(1)
        video_mode = True

    print(f"[tuner] OpenCV {cv2.__version__} detected (CV_MAJOR={CV_MAJOR})")
    create_trackbars()
    paused = False
    frame = None

    print(__doc__)
    print("[tuner] Starting... Press S to save, Q to quit, SPACE to pause.")

    while True:
        if video_mode:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # loop
                    continue
        else:
            frame = frame_orig.copy()

        read_trackbars()
        output, edges, w_mask, b_mask = process_frame(frame)

        cv2.imshow(WIN_OUT,    output)
        cv2.imshow(WIN_EDGES,  edges)
        cv2.imshow(WIN_MASK_W, w_mask)
        cv2.imshow(WIN_MASK_B, b_mask)

        key = cv2.waitKey(30 if video_mode and not paused else 50) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            save_params()
        elif key == ord(' '):
            paused = not paused
            print(f"[tuner] {'Paused' if paused else 'Resumed'}")

    if video_mode:
        cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()