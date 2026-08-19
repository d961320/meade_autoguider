import select
import time

from evdev import InputDevice, ecodes

from config import (
    LCD_HEIGHT,
    LCD_WIDTH,
    TOUCH_DEVICE,
    TOUCH_RAW_X_BOTTOM,
    TOUCH_RAW_X_TOP,
    TOUCH_RAW_Y_LEFT,
    TOUCH_RAW_Y_RIGHT,
)


class Touchscreen:
    def __init__(self):
        self.device = None
        self.raw_x = 0
        self.raw_y = 0
        self.last_touch_time = 0.0
        self.debounce_seconds = 0.35
        self.touch_is_down = False

    def open(self):
        self.device = InputDevice(TOUCH_DEVICE)
        print("Touchscreen:", self.device.name, TOUCH_DEVICE)
        self.drain_events()

    def close(self):
        if self.device is not None:
            try:
                self.device.close()
            except OSError:
                pass

        self.device = None

    def drain_events(self):
        if self.device is None:
            return

        while True:
            try:
                readable, _, _ = select.select(
                    [self.device.fd],
                    [],
                    [],
                    0,
                )

                if not readable:
                    break

                self.device.read()

            except (BlockingIOError, OSError):
                break

    @staticmethod
    def raw_to_screen(raw_x, raw_y):
        screen_x = (
            (TOUCH_RAW_Y_LEFT - raw_y)
            / (TOUCH_RAW_Y_LEFT - TOUCH_RAW_Y_RIGHT)
            * (LCD_WIDTH - 1)
        )

        screen_y = (
            (raw_x - TOUCH_RAW_X_TOP)
            / (TOUCH_RAW_X_BOTTOM - TOUCH_RAW_X_TOP)
            * (LCD_HEIGHT - 1)
        )

        screen_x = max(0, min(LCD_WIDTH - 1, screen_x))
        screen_y = max(0, min(LCD_HEIGHT - 1, screen_y))

        return int(round(screen_x)), int(round(screen_y))

    def read_release(self):
        if self.device is None:
            return None

        try:
            readable, _, _ = select.select(
                [self.device.fd],
                [],
                [],
                0,
            )

            if not readable:
                return None

            events = self.device.read()

        except (BlockingIOError, OSError):
            return None

        released = False

        for event in events:
            if event.type == ecodes.EV_ABS:
                if event.code == ecodes.ABS_X:
                    self.raw_x = event.value
                elif event.code == ecodes.ABS_Y:
                    self.raw_y = event.value

            elif (
                event.type == ecodes.EV_KEY
                and event.code == ecodes.BTN_TOUCH
            ):
                if event.value == 1:
                    self.touch_is_down = True
                elif event.value == 0 and self.touch_is_down:
                    self.touch_is_down = False
                    released = True

        if not released:
            return None

        now = time.monotonic()

        if now - self.last_touch_time < self.debounce_seconds:
            return None

        self.last_touch_time = now
        position = self.raw_to_screen(self.raw_x, self.raw_y)
        self.drain_events()

        return position
