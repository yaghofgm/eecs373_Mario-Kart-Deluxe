import cv2
import numpy as np

class Filter:
    def __init__(self,
                v_max=99,
                v_min=180,
                s_max=255,
                blue_kernel=5,
                morph_open=3,
                morph_close=7
        ):
        self.v_max = v_max
        self.v_min = v_min
        self.s_max = s_max
        self.blue_kernel = blue_kernel
        self.morph_open = morph_open
        self.morph_close = morph_close

    def flood_fill_interior(self, mask):
        h, w = mask.shape
        flood = mask.copy()
        fill_mask = np.zeros((h + 2, w + 2), np.uint8)
        for pt in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
            cv2.floodFill(flood, fill_mask, pt, 255)
        return cv2.bitwise_not(flood)

    def process_frame(self, frame):
        blurred = cv2.GaussianBlur(frame, (BLUR_K, BLUR_K), 0)
        hsv     = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # black
        black_mask = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([179, S_MAX, V_MAX]))
        k_open  = cv2.getStructuringElement(cv2.MORPH_RECT, (OPEN_K,  OPEN_K))
        k_close = cv2.getStructuringElement(cv2.MORPH_RECT, (CLOSE_K, CLOSE_K))
        black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_OPEN,  k_open)
        black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_CLOSE, k_close)

        # white
        interior   = flood_fill_interior(black_mask)
        white_px   = cv2.inRange(hsv, np.array([0, 0, V_MIN_W]), np.array([179, 80, 255]))
        white_mask = cv2.bitwise_and(interior, white_px)

        # green (incoming)

        return black_mask, white_mask
