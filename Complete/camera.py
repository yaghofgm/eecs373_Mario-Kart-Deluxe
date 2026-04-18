import cv2
import os
from datetime import datetime

class Camera:
    def __init__(self, device_index=0, save_dir="photos"):
        self.device_index = device_index
        self.save_dir = save_dir
        self.cap = None
        os.makedirs(save_dir, exist_ok=True)

    def open(self):
        # self.cap = cv2.VideoCapture(self.device_index)
        # if not self.cap.isOpened():
        #     raise RuntimeError(f"Could not open camera at index {self.device_index}")
        # print("Camera opened successfully.")
        self.cap = cv2.VideoCapture(self.device_index)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 15)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera at index {self.device_index}")
        print("Camera opened successfully.")

    def take_picture(self, filename=None):
        if self.cap is None or not self.cap.isOpened():
            raise RuntimeError("Camera is not open. Call open() first.")
        
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to capture frame.")
        
        if filename is None:
            filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
        
        filepath = os.path.join(self.save_dir, filename)
        cv2.imwrite(filepath, frame)
        print(f"Picture saved to {filepath}")
        return filepath

    def record_video(self, duration=None, filename=None, fps=30, resolution=None):
        """
        Record video to file.
        - duration: seconds to record. If None, records until 'q' is pressed.
        - filename: output filename. Defaults to timestamped .avi
        - fps: target framerate (Jetson cameras may cap lower)
        - resolution: (width, height) tuple. Defaults to camera's native res.
        """
        if self.cap is None or not self.cap.isOpened():
            raise RuntimeError("Camera is not open. Call open() first.")

        # Set resolution if requested
        if resolution:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if filename is None:
            filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".avi"

        filepath = os.path.join(self.save_dir, filename)

        # MJPG is the most reliable codec on Jetson Nano for .avi
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(filepath, fourcc, fps, (actual_w, actual_h))

        if not writer.isOpened():
            raise RuntimeError("VideoWriter failed to open. Check codec/path.")

        print(f"Recording to {filepath} ({actual_w}x{actual_h} @ {fps}fps)")
        print("Press 'q' to stop." if duration is None else f"Recording for {duration}s...")

        import time
        start = time.time()
        frames_written = 0

        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("Warning: dropped frame.")
                    continue

                writer.write(frame)
                frames_written += 1

                elapsed = time.time() - start

                # Stop conditions
                if duration and elapsed >= duration:
                    break
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            writer.release()
            elapsed = time.time() - start
            print(f"Saved {frames_written} frames ({elapsed:.1f}s) to {filepath}")

        return filepath

    def close(self):
        if self.cap:
            self.cap.release()
            self.cap = None
            print("Camera closed.")

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()