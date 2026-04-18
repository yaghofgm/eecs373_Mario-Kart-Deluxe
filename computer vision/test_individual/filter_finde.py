"""
Black Track Filter — Jetson Debug Tool
--------------------------------------
Shows RAW | FILTERED side-by-side in a single window.
Press 'q' to quit, 's' to save a snapshot.

Tune the sliders in real time to dial in your black detection.
"""

import cv2
import numpy as np

# ── Config ────────────────────────────────────────────────────────────────────
CAMERA_INDEX = 0          # Change if your external camera is /dev/video1, 2, etc.
FRAME_WIDTH  = 640
FRAME_HEIGHT = 480
WINDOW_NAME  = "Track Filter Debug  [RAW | FILTERED]"
SNAPSHOT_PATH = "snapshot.png"

# ── Trackbar callback (no-op; values are read each frame) ─────────────────────
def nothing(_): pass

# ── Setup window + sliders ────────────────────────────────────────────────────
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

# Black in HSV: low Value, any Hue/Sat
#   H: 0-179   S: 0-255   V: 0-255
cv2.createTrackbar("V max  (black ceiling)", WINDOW_NAME,  80, 255, nothing)
cv2.createTrackbar("S max  (desaturated?)",  WINDOW_NAME, 255, 255, nothing)
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
        "Try changing CAMERA_INDEX (0, 1, 2…) or check /dev/video*."
    )

print(f"[INFO] Camera opened on index {CAMERA_INDEX}")
print("[INFO] Press 'q' to quit | 's' to save snapshot")

snapshot_counter = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("[WARN] Frame grab failed — retrying…")
        continue

    # ── Read sliders ──────────────────────────────────────────────────────────
    v_max   = cv2.getTrackbarPos("V max  (black ceiling)", WINDOW_NAME)
    s_max   = cv2.getTrackbarPos("S max  (desaturated?)",  WINDOW_NAME)
    blur_k  = cv2.getTrackbarPos("Blur kernel (odd)",      WINDOW_NAME)
    open_k  = cv2.getTrackbarPos("Morph open  (denoise)",  WINDOW_NAME)
    close_k = cv2.getTrackbarPos("Morph close (fill)",     WINDOW_NAME)

    # Kernels must be odd and ≥ 1
    blur_k  = max(1, blur_k  | 1)
    open_k  = max(1, open_k  | 1)
    close_k = max(1, close_k | 1)

    # ── Pre-process ───────────────────────────────────────────────────────────
    blurred = cv2.GaussianBlur(frame, (blur_k, blur_k), 0)
    hsv     = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # Black = any hue, any saturation, but LOW value
    lower_black = np.array([  0,   0,   0])
    upper_black = np.array([179, s_max, v_max])
    mask = cv2.inRange(hsv, lower_black, upper_black)

    # Morphological cleanup
    k_open  = cv2.getStructuringElement(cv2.MORPH_RECT, (open_k,  open_k))
    k_close = cv2.getStructuringElement(cv2.MORPH_RECT, (close_k, close_k))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  k_open)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k_close)

    # ── Build filtered view ───────────────────────────────────────────────────
    # Green overlay on detected track region, original colour elsewhere
    mask_3ch   = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    green_layer = np.zeros_like(frame)
    green_layer[:] = (0, 220, 80)          # green fill

    filtered = np.where(mask_3ch == 255, green_layer, frame)

    # Optional: draw contours for shape debug
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2:]
    cv2.drawContours(filtered, contours, -1, (0, 0, 255), 2)  # red borders

    # ── Overlay stats on RAW frame ────────────────────────────────────────────
    pct = 100.0 * cv2.countNonZero(mask) / mask.size
    info = [
        f"V max={v_max}  S max={s_max}",
        f"Blur={blur_k}  Open={open_k}  Close={close_k}",
        f"Black coverage: {pct:.1f}%",
        f"Contours found: {len(contours)}",
    ]
    raw_display = frame.copy()
    for i, line in enumerate(info):
        cv2.putText(raw_display, line, (8, 22 + i * 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1, cv2.LINE_AA)

    # Labels
    cv2.putText(raw_display, "RAW",      (8, FRAME_HEIGHT - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    cv2.putText(filtered,    "FILTERED", (8, FRAME_HEIGHT - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

    # ── Side-by-side ──────────────────────────────────────────────────────────
    combined = np.hstack([raw_display, filtered])
    cv2.imshow(WINDOW_NAME, combined)

    # ── Key handling ──────────────────────────────────────────────────────────
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        path = f"snapshot_{snapshot_counter:03d}.png"
        cv2.imwrite(path, combined)
        print(f"[INFO] Snapshot saved → {path}")
        snapshot_counter += 1

cap.release()
cv2.destroyAllWindows()
print("[INFO] Done.")