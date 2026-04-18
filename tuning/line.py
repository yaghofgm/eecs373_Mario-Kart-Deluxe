"""
White Dashed Line Detector — Direction Focused
===============================================
Detects the white dashed center line and estimates:
  - Lateral error  : how far left/right the line is from frame center
  - Heading angle  : the angle of the line (direction the road points)

Both values are what you feed into your PID controller.

Usage:
    python3 line_direction.py --source vid.mp4
    python3 line_direction.py --source 0        # live camera

Controls:
    SPACE  - pause/resume
    S      - save params to lane_params.json
    Q      - quit
"""

import cv2
import numpy as np
import json
import argparse
import sys

PARAM_FILE = "lane_params.json"
CV_MAJOR   = int(cv2.__version__.split(".")[0])

# ── Parameters (tune these with trackbars) ────────────────────────────────────
params = {
    "blur_k":          5,

    # White HSV — start broad, narrow down
    "white_s_max":    50,    # low saturation = white/gray
    "white_v_min":   180,    # high value = bright

    # Canny
    "canny_low":      30,
    "canny_high":    100,

    # Hough
    "hough_thresh":   20,
    "hough_min_len":  15,
    "hough_max_gap":  30,    # larger gap helps connect dashes

    # ROI: only look at the bottom portion of the frame
    # roi_top = 0.35 means use bottom 65% of frame
    "roi_top":        35,    # percent from top (0–90)

    # Direction line filtering
    # Only keep lines within this angle range from vertical (degrees)
    # The dashed center line runs mostly vertically in the camera view
    "angle_min":      60,    # degrees from horizontal — keep near-vertical lines
    "angle_max":      90,
}

WIN_CTRL = "Controls"
WIN_OUT  = "Direction output"
WIN_MASK = "White mask"
WIN_DBG  = "Hough lines (raw)"


def nothing(_): pass


def create_trackbars():
    cv2.namedWindow(WIN_CTRL, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN_CTRL, 400, 600)

    def tb(name, val, maxval):
        cv2.createTrackbar(name, WIN_CTRL, int(val), maxval, nothing)

    tb("Blur kernel",    params["blur_k"] // 2,  10)
    tb("White S max",    params["white_s_max"],  255)
    tb("White V min",    params["white_v_min"],  255)
    tb("Canny low",      params["canny_low"],    255)
    tb("Canny high",     params["canny_high"],   255)
    tb("Hough thresh",   params["hough_thresh"], 100)
    tb("Hough min len",  params["hough_min_len"],200)
    tb("Hough max gap",  params["hough_max_gap"],100)
    tb("ROI top %",      params["roi_top"],       90)
    tb("Angle min",      params["angle_min"],     90)
    tb("Angle max",      params["angle_max"],     90)


def read_trackbars():
    def g(n): return cv2.getTrackbarPos(n, WIN_CTRL)
    params["blur_k"]         = max(1, g("Blur kernel") * 2 + 1)
    params["white_s_max"]    = g("White S max")
    params["white_v_min"]    = g("White V min")
    params["canny_low"]      = g("Canny low")
    params["canny_high"]     = g("Canny high")
    params["hough_thresh"]   = max(1, g("Hough thresh"))
    params["hough_min_len"]  = max(1, g("Hough min len"))
    params["hough_max_gap"]  = max(0, g("Hough max gap"))
    params["roi_top"]        = g("ROI top %")
    params["angle_min"]      = g("Angle min")
    params["angle_max"]      = g("Angle max")


def get_white_mask(hsv):
    """Isolate white/light-gray pixels."""
    return cv2.inRange(
        hsv,
        (0,   0,                     params["white_v_min"]),
        (180, params["white_s_max"], 255)
    )


def get_roi_mask(frame):
    h, w = frame.shape[:2]
    top_y = int(h * params["roi_top"] / 100.0)
    mask = np.zeros((h, w), dtype=np.uint8)
    # Slight trapezoid: wider at bottom, narrower at top
    # This helps focus on the road ahead and ignore the edges
    margin_top = w // 4
    pts = np.array([
        [margin_top,     top_y],
        [w - margin_top, top_y],
        [w,              h],
        [0,              h]
    ], dtype=np.int32)
    cv2.fillPoly(mask, [pts], 255)
    return mask


def line_angle_deg(x1, y1, x2, y2):
    """Angle from horizontal in degrees (0=horizontal, 90=vertical)."""
    dx = x2 - x1
    dy = y2 - y1
    return abs(np.degrees(np.arctan2(abs(dy), abs(dx) + 1e-6)))


def fit_direction_line(lines, frame_shape):
    """
    Given a list of Hough line segments, filter to near-vertical ones
    and fit a single best-fit line through all their endpoints.

    Returns:
        (angle_deg, lateral_error_px, (x1,y1,x2,y2)) or None
        - angle_deg       : heading angle from vertical (0 = straight ahead)
        - lateral_error_px: how far the line is from frame center (+ = right)
        - (x1,y1,x2,y2)  : the fitted line to draw
    """
    if lines is None:
        return None

    h, w = frame_shape[:2]
    cx = w // 2

    a_min = params["angle_min"]
    a_max = params["angle_max"]

    # Collect all endpoints from qualifying lines
    points = []
    for seg in lines:
        x1, y1, x2, y2 = seg[0]
        angle = line_angle_deg(x1, y1, x2, y2)
        if a_min <= angle <= a_max:
            points.append((x1, y1))
            points.append((x2, y2))

    if len(points) < 4:   # need at least 2 segments worth of points
        return None

    pts = np.array(points, dtype=np.float32)
    xs  = pts[:, 0]
    ys  = pts[:, 1]

    # Fit a line using least-squares (polyfit degree 1: x = m*y + b)
    # We fit x as a function of y because the line is near-vertical
    # (fitting y=mx+b would be numerically unstable for steep lines)
    try:
        coeffs = np.polyfit(ys, xs, 1)   # x = m*y + b
    except np.linalg.LinAlgError:
        return None

    m, b = coeffs   # x = m*y + b

    # Evaluate fitted line at top and bottom of ROI
    top_y  = int(h * params["roi_top"] / 100.0)
    bot_y  = h
    top_x  = int(m * top_y + b)
    bot_x  = int(m * bot_y + b)

    # Lateral error: where the line crosses the bottom of the frame vs center
    lateral_error = bot_x - cx

    # Heading angle: angle of the fitted line from vertical
    # 0° = perfectly straight ahead, + = leaning right, - = leaning left
    heading_angle = np.degrees(np.arctan2(top_x - bot_x, bot_y - top_y))

    return heading_angle, lateral_error, (top_x, top_y, bot_x, bot_y)


def draw_overlay(output, result, frame_shape):
    h, w = frame_shape[:2]
    cx = w // 2

    # Center reference line
    cv2.line(output, (cx, h - 10), (cx, h - 50), (255, 80, 80), 2)

    if result is None:
        cv2.putText(output, "NO LINE DETECTED",
                    (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return

    angle_deg, lateral_err, (x1, y1, x2, y2) = result

    # Draw fitted direction line
    cv2.line(output, (x1, y1), (x2, y2), (0, 255, 0), 3)

    # Draw a direction arrow at the midpoint
    mid_x = (x1 + x2) // 2
    mid_y = (y1 + y2) // 2
    arrow_len = 40
    tip_x = mid_x + int(arrow_len * np.sin(np.radians(angle_deg)))
    tip_y = mid_y - int(arrow_len * np.cos(np.radians(angle_deg)))
    cv2.arrowedLine(output, (mid_x, mid_y), (tip_x, tip_y), (0, 255, 255), 2, tipLength=0.4)

    # Lateral error indicator at bottom
    cv2.line(output, (cx + lateral_err, h - 10), (cx + lateral_err, h - 50), (0, 255, 0), 2)
    cv2.line(output, (cx, h - 30), (cx + lateral_err, h - 30), (0, 200, 200), 1)

    # Text readout
    cv2.putText(output, f"Lateral error : {lateral_err:+.0f} px",
                (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
    cv2.putText(output, f"Heading angle : {angle_deg:+.1f} deg",
                (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)

    # Combined steering signal hint
    # You can blend these two: steering = Kp_lat * lateral_err + Kp_ang * angle_deg
    steering = 0.5 * lateral_err + 8.0 * angle_deg
    cv2.putText(output, f"Steering hint : {steering:+.1f}",
                (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 200, 0), 2)


def process_frame(frame):
    h, w = frame.shape[:2]
    blurred = cv2.GaussianBlur(frame, (params["blur_k"], params["blur_k"]), 0)
    hsv     = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    white_mask = get_white_mask(hsv)
    roi_mask   = get_roi_mask(frame)
    masked     = cv2.bitwise_and(white_mask, roi_mask)

    # Draw ROI outline on output
    output = frame.copy()
    roi_vis_pts = np.array([
        [w // 4,     int(h * params["roi_top"] / 100)],
        [3 * w // 4, int(h * params["roi_top"] / 100)],
        [w,          h],
        [0,          h],
    ], dtype=np.int32)
    cv2.polylines(output, [roi_vis_pts], True, (0, 200, 255), 1)

    edges = cv2.Canny(masked, params["canny_low"], params["canny_high"])

    lines = cv2.HoughLinesP(
        edges,
        rho=1, theta=np.pi / 180,
        threshold=params["hough_thresh"],
        minLineLength=params["hough_min_len"],
        maxLineGap=params["hough_max_gap"]
    )

    # Debug: show all raw Hough lines before filtering
    dbg = frame.copy()
    if lines is not None:
        for seg in lines:
            x1, y1, x2, y2 = seg[0]
            angle = line_angle_deg(x1, y1, x2, y2)
            color = (0, 255, 0) if params["angle_min"] <= angle <= params["angle_max"] else (0, 0, 180)
            cv2.line(dbg, (x1, y1), (x2, y2), color, 2)

    result = fit_direction_line(lines, frame.shape)
    draw_overlay(output, result, frame.shape)

    return output, masked, dbg, result


def save_params(result):
    data = dict(params)
    if result:
        data["last_lateral_error"] = round(result[0], 2)
        data["last_heading_angle"] = round(result[1], 2)
    with open(PARAM_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[detector] Saved to {PARAM_FILE}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="0")
    args = parser.parse_args()

    src = args.source
    try:
        src = int(src)
    except ValueError:
        pass

    if isinstance(src, str) and src.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
        frame_orig = cv2.imread(src)
        if frame_orig is None:
            print(f"ERROR: cannot open {src}"); sys.exit(1)
        video_mode = False
    else:
        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            print(f"ERROR: cannot open {src}"); sys.exit(1)
        video_mode = True

    print(f"[detector] OpenCV {cv2.__version__}")
    create_trackbars()
    paused = False
    last_result = None
    frame = None

    print("[detector] SPACE=pause  S=save  Q=quit")
    print("[detector] Green lines  = kept (near-vertical)")
    print("[detector] Red lines    = rejected by angle filter")

    while True:
        if video_mode:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
        else:
            frame = frame_orig.copy()

        read_trackbars()
        output, mask, dbg, last_result = process_frame(frame)

        cv2.imshow(WIN_OUT,  output)
        cv2.imshow(WIN_MASK, mask)
        cv2.imshow(WIN_DBG,  dbg)

        key = cv2.waitKey(30 if video_mode and not paused else 50) & 0xFF
        if   key == ord('q'): break
        elif key == ord('s'): save_params(last_result)
        elif key == ord(' '):
            paused = not paused
            print(f"[detector] {'Paused' if paused else 'Resumed'}")

    if video_mode:
        cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()