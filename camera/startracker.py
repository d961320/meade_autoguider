import cv2
import numpy as np


class StarTracker:
    def find_stars(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        smooth = cv2.GaussianBlur(gray, (5, 5), 0)

        background = float(np.median(smooth))
        sigma = float(np.std(smooth))
        threshold_value = max(
            0,
            min(255, background + 4.0 * sigma),
        )

        _, binary = cv2.threshold(
            smooth,
            threshold_value,
            255,
            cv2.THRESH_BINARY,
        )

        contours, _ = cv2.findContours(
            binary.astype(np.uint8),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        stars = []

        for contour in contours:
            x, y, width, height = cv2.boundingRect(contour)

            if width < 2 or height < 2:
                continue

            if width > 40 or height > 40:
                continue

            roi = gray[
                y:y + height,
                x:x + width,
            ].astype(np.float64)

            if roi.size == 0:
                continue

            local_background = float(np.median(roi))
            signal = roi - local_background
            signal[signal < 0] = 0

            flux = float(signal.sum())

            if flux <= 0:
                continue

            yy, xx = np.indices(signal.shape)

            center_x = x + float((xx * signal).sum() / flux)
            center_y = y + float((yy * signal).sum() / flux)

            stars.append(
                {
                    "x": center_x,
                    "y": center_y,
                    "flux": flux,
                    "area": float(cv2.contourArea(contour)),
                }
            )

        stars.sort(
            key=lambda star: star["flux"],
            reverse=True,
        )

        return stars[:25]
