"""
Black Track Filter — Jetson Debug Tool
--------------------------------------
Black track surface → GREEN
White markings inside the track (dashes, text) → BLUE

Shows RAW | FILTERED side-by-side.
Press 'q' to quit, 's' to save a snapshot.
"""

import cv2
import numpy as np

# ── Config ────────────────────────────────────────────────────────────────────
CAMERA_INDEX = 0
FRAME_WIDTH  = 640
FRAME_HEIGHT = 480
WINDOW_NAME  = "Track Filter Debug  [RAW | FILTERED]"

def nothing(_): pass

# ── Setup window + sliders ────────────────────────────────────────────────────
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

cv2.createTrackbar("V max  (black ceiling)", WINDOW_NAME,  80, 255, nothing)
cv2.createTrackbar("V min  (white floor)",   WINDOW_NAME, 180, 255, nothing)
cv2.createTrackbar("S max  (allow any sat)", WINDOW_NAME, 255, 255, nothing)
cv2.createTrackbar("Blur kernel (odd)",      WINDOW_NAME,   5,  31, nothing)
cv2.createTrackbar("Morph open  (denoise)",  WINDOW_NAME,   3,  21, nothing)
cv2.createTrackbar("Morph close (fill)",     WINDOW_NAME,   7,  21, nothing)

# ── Camera ────────────────────────────────────────────────────────────────────
cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

if not cap.isOpened():
    raise RuntimeError(
        f"Cannot open camera index {CAMERA_INDEX}. "
        "Try changing CAMERA_INDEX (0, 1, 2) or check /dev/video*."
    )

print(f"[INFO] Camera opened on index {CAMERA_INDEX}")
print("[INFO] Press 'q' to quit | 's' to save snapshot")

snapshot_counter = 0

def flood_fill_interior(mask):
    """
    Returns a mask of the INTERIOR holes (white markings enclosed by black).
    Flood-fills from corners (background), inverts — leftover = enclosed interior.
    """
    h, w = mask.shape
    flood = mask.copy()
    fill_mask = np.zeros((h + 2, w + 2), np.uint8)
    for pt in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        cv2.floodFill(flood, fill_mask, pt, 255)
    # Pixels the flood couldn't reach = enclosed interior
    interior = cv2.bitwise_not(flood)
    return interior

while True:
    ret, frame = cap.read()
    if not ret:
        print("[WARN] Frame grab failed — retrying...")
        continue

    # ── Read sliders ──────────────────────────────────────────────────────────
    v_max   = cv2.getTrackbarPos("V max  (black ceiling)", WINDOW_NAME)
    v_min_w = cv2.getTrackbarPos("V min  (white floor)",   WINDOW_NAME)
    s_max   = cv2.getTrackbarPos("S max  (allow any sat)", WINDOW_NAME)
    blur_k  = cv2.getTrackbarPos("Blur kernel (odd)",      WINDOW_NAME)
    open_k  = cv2.getTrackbarPos("Morph open  (denoise)",  WINDOW_NAME)
    close_k = cv2.getTrackbarPos("Morph close (fill)",     WINDOW_NAME)

    blur_k  = max(1, blur_k  | 1)
    open_k  = max(1, open_k  | 1)
    close_k = max(1, close_k | 1)

    # ── Pre-process ───────────────────────────────────────────────────────────
    blurred = cv2.GaussianBlur(frame, (blur_k, blur_k), 0)
    hsv     = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # ── Mask 1: black pixels ──────────────────────────────────────────────────
    black_mask = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([179, s_max, v_max]))

    k_open  = cv2.getStructuringElement(cv2.MORPH_RECT, (open_k,  open_k))
    k_close = cv2.getStructuringElement(cv2.MORPH_RECT, (close_k, close_k))
    black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_OPEN,  k_open)
    black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_CLOSE, k_close)

    # ── Mask 2: interior holes (white markings enclosed by black) ─────────────
    interior_mask = flood_fill_interior(black_mask)

    # Optionally refine: only keep pixels that are actually bright (white)
    white_pixels  = cv2.inRange(hsv, np.array([0, 0, v_min_w]), np.array([179, 80, 255]))
    interior_mask = cv2.bitwise_and(interior_mask, white_pixels)

    # ── Build colored filtered view ───────────────────────────────────────────
    filtered = frame.copy()

    # Green for black track surface
    green = np.full_like(frame, (0, 200, 0))
    filtered = np.where(cv2.cvtColor(black_mask, cv2.COLOR_GRAY2BGR) == 255, green, filtered)

    # Blue for white markings inside track
    blue = np.full_like(frame, (255, 80, 0))
    filtered = np.where(cv2.cvtColor(interior_mask, cv2.COLOR_GRAY2BGR) == 255, blue, filtered)

    # Red contours around the black track boundary
    contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2:]
    cv2.drawContours(filtered, contours, -1, (0, 0, 255), 2)

    # ── Stats overlay on RAW ──────────────────────────────────────────────────
    black_pct    = 100.0 * cv2.countNonZero(black_mask)    / black_mask.size
    interior_pct = 100.0 * cv2.countNonZero(interior_mask) / interior_mask.size
    info = [
        f"V max={v_max}  V white-floor={v_min_w}  S max={s_max}",
        f"Blur={blur_k}  Open={open_k}  Close={close_k}",
        f"Black(green): {black_pct:.1f}%   White(blue): {interior_pct:.1f}%",
        f"Contours: {len(contours)}",
    ]
    raw_display = frame.copy()
    for i, line in enumerate(info):
        cv2.putText(raw_display, line, (8, 22 + i * 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)

    cv2.putText(raw_display, "RAW",      (8, FRAME_HEIGHT - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(filtered,    "FILTERED", (8, FRAME_HEIGHT - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    combined = np.hstack([raw_display, filtered])
    cv2.imshow(WINDOW_NAME, combined)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        path = f"snapshot_{snapshot_counter:03d}.png"
        cv2.imwrite(path, combined)
        print(f"[INFO] Snapshot saved -> {path}")
        snapshot_counter += 1

cap.release()
cv2.destroyAllWindows()
print("[INFO] Done.")