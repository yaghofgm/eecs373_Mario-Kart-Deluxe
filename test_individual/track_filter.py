"""
Black Track Filter — Jetson Production
---------------------------------------
Tuned values (from debug session):
  V max (black ceiling) = 99
  V min (white floor)   = 180
  S max                 = 255
  Blur kernel           = 5
  Morph open            = 3
  Morph close           = 7

Black track surface     → GREEN
White markings inside   → BLUE
"""

import cv2
import numpy as np

# ── Config ────────────────────────────────────────────────────────────────────
CAMERA_INDEX = 0
FRAME_WIDTH  = 640
FRAME_HEIGHT = 480

# ── Tuned filter parameters ───────────────────────────────────────────────────
V_MAX   = 99    # brightness ceiling for black
V_MIN_W = 180   # brightness floor for white markings
S_MAX   = 255   # saturation ceiling (allow any)
BLUR_K  = 5     # gaussian blur kernel (odd)
OPEN_K  = 3     # morphological open (denoise)
CLOSE_K = 7     # morphological close (fill gaps)

def flood_fill_interior(mask):
    h, w = mask.shape
    flood = mask.copy()
    fill_mask = np.zeros((h + 2, w + 2), np.uint8)
    for pt in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        cv2.floodFill(flood, fill_mask, pt, 255)
    return cv2.bitwise_not(flood)

def process_frame(frame):
    blurred = cv2.GaussianBlur(frame, (BLUR_K, BLUR_K), 0)
    hsv     = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # Black mask
    black_mask = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([179, S_MAX, V_MAX]))
    k_open  = cv2.getStructuringElement(cv2.MORPH_RECT, (OPEN_K,  OPEN_K))
    k_close = cv2.getStructuringElement(cv2.MORPH_RECT, (CLOSE_K, CLOSE_K))
    black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_OPEN,  k_open)
    black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_CLOSE, k_close)

    # White interior mask
    interior   = flood_fill_interior(black_mask)
    white_px   = cv2.inRange(hsv, np.array([0, 0, V_MIN_W]), np.array([179, 80, 255]))
    white_mask = cv2.bitwise_and(interior, white_px)

    return black_mask, white_mask

cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

if not cap.isOpened():
    raise RuntimeError(f"Cannot open camera index {CAMERA_INDEX}.")

print("[INFO] Running. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    black_mask, white_mask = process_frame(frame)

    output = frame.copy()
    green = np.full_like(frame, (0, 200, 0))
    blue  = np.full_like(frame, (255, 80, 0))
    output = np.where(cv2.cvtColor(black_mask, cv2.COLOR_GRAY2BGR) == 255, green, output)
    output = np.where(cv2.cvtColor(white_mask, cv2.COLOR_GRAY2BGR) == 255, blue,  output)

    cv2.imshow("Track Filter", output)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()