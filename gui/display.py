import mmap
import os

import cv2
import numpy as np

from config import (
    FRAMEBUFFER_DEVICE,
    FRAMEBUFFER_STRIDE,
    LCD_HEIGHT,
    LCD_WIDTH,
)
from version import PROGRAM_NAME, PROGRAM_VERSION


class Display:
    def __init__(self):
        self.fd = None
        self.fb = None
        self.width = LCD_WIDTH
        self.height = LCD_HEIGHT
        self.stride = FRAMEBUFFER_STRIDE
        self.map_size = self.stride * self.height

    def open(self):
        self.fd = os.open(FRAMEBUFFER_DEVICE, os.O_RDWR)
        self.fb = mmap.mmap(
            self.fd,
            self.map_size,
            mmap.MAP_SHARED,
            mmap.PROT_READ | mmap.PROT_WRITE,
        )

        print("Framebuffer:", FRAMEBUFFER_DEVICE)
        print("Opløsning:", f"{self.width}x{self.height}")
        print("Farvedybde: 16 bit RGB565")
        print("Stride:", self.stride)
        print("Mapped størrelse:", self.map_size)

    def close(self):
        if self.fb is not None:
            try:
                self.fb.close()
            except OSError:
                pass
            self.fb = None

        if self.fd is not None:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = None

    def show(self, screen):
        if self.fb is None:
            return

        if screen.shape[:2] != (self.height, self.width):
            screen = cv2.resize(
                screen,
                (self.width, self.height),
                interpolation=cv2.INTER_AREA,
            )

        blue = screen[:, :, 0].astype(np.uint16) >> 3
        green = screen[:, :, 1].astype(np.uint16) >> 2
        red = screen[:, :, 2].astype(np.uint16) >> 3

        rgb565 = ((red << 11) | (green << 5) | blue).astype("<u2")

        self.fb.seek(0)
        self.fb.write(rgb565.tobytes())
        self.fb.flush()

    def blank(self):
        if self.fb is None:
            return

        self.fb.seek(0)
        self.fb.write(bytes(self.map_size))
        self.fb.flush()

    @staticmethod
    def centered_text(screen, text, y, scale, color, thickness=1):
        font = cv2.FONT_HERSHEY_SIMPLEX
        size, _ = cv2.getTextSize(text, font, scale, thickness)
        x = max(0, (screen.shape[1] - size[0]) // 2)

        cv2.putText(
            screen,
            text,
            (x, y),
            font,
            scale,
            color,
            thickness,
            cv2.LINE_AA,
        )

    @staticmethod
    def button(screen, rect, label, selected=False, danger=False, enabled=True):
        x1, y1, x2, y2 = rect

        if not enabled:
            fill, border, text_color = (
                (22, 22, 22),
                (65, 65, 65),
                (90, 90, 90),
            )
        elif danger:
            fill, border, text_color = (
                (60, 28, 28),
                (0, 0, 255),
                (255, 255, 255),
            )
        elif selected:
            fill, border, text_color = (
                (65, 60, 20),
                (0, 255, 255),
                (255, 255, 255),
            )
        else:
            fill, border, text_color = (
                (42, 42, 42),
                (155, 155, 155),
                (255, 255, 255),
            )

        cv2.rectangle(screen, (x1, y1), (x2, y2), fill, -1)
        cv2.rectangle(screen, (x1, y1), (x2, y2), border, 2)

        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.44
        size, _ = cv2.getTextSize(label, font, scale, 1)

        cv2.putText(
            screen,
            label,
            (
                x1 + (x2 - x1 - size[0]) // 2,
                y1 + (y2 - y1 + size[1]) // 2,
            ),
            font,
            scale,
            text_color,
            1,
            cv2.LINE_AA,
        )

    def splash(self, status):
        screen = np.zeros(
            (self.height, self.width, 3),
            dtype=np.uint8,
        )

        self.centered_text(
            screen,
            PROGRAM_NAME.upper(),
            65,
            0.72,
            (255, 255, 255),
        )
        self.centered_text(
            screen,
            f"Professional {PROGRAM_VERSION}",
            96,
            0.46,
            (180, 180, 180),
        )
        cv2.line(
            screen,
            (50, 120),
            (self.width - 50, 120),
            (100, 100, 100),
            1,
        )
        self.centered_text(
            screen,
            status,
            190,
            0.56,
            (0, 255, 255),
        )

        self.show(screen)

    def main_menu(self, items, selected):
        screen = np.zeros(
            (self.height, self.width, 3),
            dtype=np.uint8,
        )

        self.centered_text(
            screen,
            f"{PROGRAM_NAME} {PROGRAM_VERSION}",
            32,
            0.55,
            (255, 255, 255),
        )

        for index, (label, value, enabled) in enumerate(items):
            y1 = 48 + index * 38

            self.button(
                screen,
                (18, y1, self.width - 18, y1 + 32),
                label,
                selected=index == selected,
                enabled=enabled,
            )

            if value:
                font = cv2.FONT_HERSHEY_SIMPLEX
                size, _ = cv2.getTextSize(value, font, 0.34, 1)

                cv2.putText(
                    screen,
                    value,
                    (self.width - 28 - size[0], y1 + 21),
                    font,
                    0.34,
                    (200, 200, 200) if enabled else (90, 90, 90),
                    1,
                    cv2.LINE_AA,
                )

        self.centered_text(
            screen,
            "N=naeste  V=vaelg  Q=afslut",
            313,
            0.34,
            (150, 150, 150),
        )

        self.show(screen)

    def info_screen(self, title, lines, footer="V/touch = tilbage"):
        screen = np.zeros(
            (self.height, self.width, 3),
            dtype=np.uint8,
        )

        self.centered_text(
            screen,
            title,
            36,
            0.64,
            (255, 255, 255),
        )

        y = 76

        for label, value in lines:
            cv2.putText(
                screen,
                f"{label}:",
                (24, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.44,
                (175, 175, 175),
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                screen,
                str(value),
                (170, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.44,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
            y += 34

        self.centered_text(
            screen,
            footer,
            307,
            0.36,
            (150, 150, 150),
        )

        self.show(screen)

    def mount_test_screen(self, connected, pulse_ms, message):
        screen = np.zeros(
            (self.height, self.width, 3),
            dtype=np.uint8,
        )

        self.centered_text(
            screen,
            "MOUNT TEST",
            30,
            0.66,
            (255, 255, 255),
        )

        self.centered_text(
            screen,
            "FORBUNDET" if connected else "IKKE TILSLUTTET",
            52,
            0.39,
            (0, 255, 0) if connected else (0, 0, 255),
        )

        self.button(screen, (175, 65, 305, 108), "NORD", enabled=connected)
        self.button(screen, (35, 118, 155, 161), "VEST", enabled=connected)
        self.button(screen, (180, 118, 300, 161), "STOP", danger=True)
        self.button(screen, (325, 118, 445, 161), "OEST", enabled=connected)
        self.button(screen, (175, 171, 305, 214), "SYD", enabled=connected)
        self.button(screen, (25, 225, 145, 266), "- PULS")
        self.button(screen, (335, 225, 455, 266), "+ PULS")
        self.button(screen, (170, 272, 310, 315), "TILBAGE")

        self.centered_text(
            screen,
            f"Puls: {pulse_ms} ms",
            248,
            0.42,
            (0, 255, 255),
        )

        cv2.putText(
            screen,
            message[:60],
            (8, 306),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.31,
            (200, 200, 200),
            1,
            cv2.LINE_AA,
        )

        self.show(screen)

    def camera_screen(self, frame, fps, stars, selected_index, locked):
        screen = np.zeros(
            (self.height, self.width, 3),
            dtype=np.uint8,
        )

        camera_width = 370
        scale = min(
            camera_width / frame.shape[1],
            self.height / frame.shape[0],
        )

        new_width = int(frame.shape[1] * scale)
        new_height = int(frame.shape[0] * scale)

        preview = cv2.resize(
            frame,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA,
        )

        x0 = (camera_width - new_width) // 2
        y0 = (self.height - new_height) // 2

        screen[
            y0:y0 + new_height,
            x0:x0 + new_width,
        ] = preview

        for index, star in enumerate(stars):
            sx = x0 + int(round(star["x"] * scale))
            sy = y0 + int(round(star["y"] * scale))
            color = (0, 255, 0) if locked and index == selected_index else (0, 255, 255)
            radius = 10 if index == selected_index else 6
            cv2.circle(screen, (sx, sy), radius, color, 2)

        cv2.rectangle(
            screen,
            (370, 0),
            (479, 319),
            (35, 35, 35),
            -1,
        )

        self.button(screen, (375, 10, 474, 65), "NAESTE")
        self.button(screen, (375, 75, 474, 130), "VAELG")
        self.button(screen, (375, 140, 474, 195), "FRIGIV")
        self.button(screen, (375, 260, 474, 315), "TILBAGE")

        cv2.putText(
            screen,
            f"FPS {fps:4.1f}",
            (380, 225),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        cv2.putText(
            screen,
            f"Stars {len(stars)}",
            (380, 245),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        self.show(screen)

    def shutdown(self):
        screen = np.zeros(
            (self.height, self.width, 3),
            dtype=np.uint8,
        )

        self.centered_text(
            screen,
            PROGRAM_NAME,
            88,
            0.75,
            (255, 255, 255),
        )
        self.centered_text(
            screen,
            "Autoguider stoppet",
            170,
            0.62,
            (0, 255, 0),
        )
        self.centered_text(
            screen,
            "Vender tilbage til terminal",
            215,
            0.43,
            (190, 190, 190),
        )

        self.show(screen)
