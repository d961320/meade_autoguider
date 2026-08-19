import time

import cv2

from config import (
    CAMERA_DEVICE,
    CAMERA_FOURCC,
    CAMERA_FPS,
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
)


class Camera:
    def __init__(self):
        self.cap = None
        self.last_frame_time = None

    def open(self):
        self.cap = cv2.VideoCapture(
            CAMERA_DEVICE,
            cv2.CAP_V4L2,
        )

        if not self.cap.isOpened():
            raise RuntimeError("Kan ikke åbne kameraet")

        self.cap.set(
            cv2.CAP_PROP_FOURCC,
            cv2.VideoWriter_fourcc(*CAMERA_FOURCC),
        )
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

    def close(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def read(self):
        if self.cap is None:
            raise RuntimeError("Kameraet er ikke åbnet")

        ok, frame = self.cap.read()

        if not ok:
            return None

        self.last_frame_time = time.monotonic()
        return frame
