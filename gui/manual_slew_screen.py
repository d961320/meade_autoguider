#!/usr/bin/env python3

"""
Manuel kontinuerlig mount-styring.

Denne skærm bruger:
    mount/manual_slew.py

Den eksisterende Guide Test ændres ikke.

Touch:
    Ét tryk på retning starter bevægelsen.
    STOP eller TILBAGE standser bevægelsen.

Tastatur:
    n = nord
    s = syd
    e = øst
    w = vest
    x = stop

    g = guide-hastighed
    c = center-hastighed
    f = find-hastighed
    m = maksimal slew-hastighed

    q eller Esc = tilbage
"""

import time

import cv2
import numpy as np

from mount.manual_slew import ManualSlew


class ManualSlewScreen:
    """LCD-skærm til manuel kontinuerlig mount-bevægelse."""

    WIDTH = 480
    HEIGHT = 320

    # Retningsknapper
    NORTH_RECT = (175, 48, 305, 91)
    WEST_RECT = (28, 101, 158, 144)
    STOP_RECT = (175, 101, 305, 144)
    EAST_RECT = (322, 101, 452, 144)
    SOUTH_RECT = (175, 154, 305, 197)

    # Hastighedsknapper
    GUIDE_RECT = (15, 214, 122, 253)
    CENTER_RECT = (129, 214, 236, 253)
    FIND_RECT = (243, 214, 350, 253)
    SLEW_RECT = (357, 214, 464, 253)

    BACK_RECT = (170, 270, 310, 315)

    SPEED_LABELS = {
        "GUIDE": "GUIDE",
        "CENTER": "CENTER",
        "FIND": "FIND",
        "SLEW": "MAX",
    }

    DIRECTION_NAMES = {
        "n": "NORD",
        "s": "SYD",
        "e": "OEST",
        "w": "VEST",
    }

    def __init__(
        self,
        display,
        touch,
        keyboard,
        mount_controller,
        logger=None,
    ):
        self.display = display
        self.touch = touch
        self.keyboard = keyboard
        self.mount = mount_controller
        self.logger = logger

        self.slew = ManualSlew(
            mount_controller
        )

        self.message = "Klar"
        self.active_direction = None

    def run(self):
        """
        Vis skærmen og behandl input, indtil brugeren går tilbage.
        """

        try:
            # FIND er en praktisk standard til manuel navigation.
            self.slew.set_speed("FIND")
            self.message = "Tryk retning - STOP for at standse"

            while True:
                self.draw()

                action = self._read_action()

                if action is None:
                    time.sleep(0.02)
                    continue

                if action == "back":
                    self._stop_safely()
                    return

                if action == "stop":
                    self._stop_safely()
                    self.message = "STOP sendt"
                    continue

                if action.startswith("speed:"):
                    speed = action.split(":", 1)[1]
                    self._set_speed(speed)
                    continue

                if action.startswith("move:"):
                    direction = action.split(":", 1)[1]
                    self._start_direction(direction)
                    continue

        except KeyboardInterrupt:
            self._stop_safely()
            raise

        except Exception as error:
            self._stop_safely()
            self.message = f"Fejl: {error}"

            if self.logger is not None:
                self.logger.exception(
                    "Manual Slew screen failed"
                )

            self.draw()
            time.sleep(2)

        finally:
            self._stop_safely()

    def draw(self):
        """Tegn hele Manual Slew-skærmen."""

        screen = np.zeros(
            (self.HEIGHT, self.WIDTH, 3),
            dtype=np.uint8,
        )

        self.display.centered_text(
            screen,
            "MANUAL SLEW",
            29,
            0.66,
            (255, 255, 255),
        )

        connected_text = (
            "FORBUNDET"
            if self.mount.connected
            else "IKKE TILSLUTTET"
        )

        connected_color = (
            (0, 255, 0)
            if self.mount.connected
            else (0, 0, 255)
        )

        self.display.centered_text(
            screen,
            connected_text,
            45,
            0.34,
            connected_color,
        )

        self._draw_direction_button(
            screen,
            self.NORTH_RECT,
            "NORD",
            "n",
        )

        self._draw_direction_button(
            screen,
            self.WEST_RECT,
            "VEST",
            "w",
        )

        self.display.button(
            screen,
            self.STOP_RECT,
            "STOP",
            danger=True,
            enabled=True,
        )

        self._draw_direction_button(
            screen,
            self.EAST_RECT,
            "OEST",
            "e",
        )

        self._draw_direction_button(
            screen,
            self.SOUTH_RECT,
            "SYD",
            "s",
        )

        self._draw_speed_button(
            screen,
            "GUIDE",
            self.GUIDE_RECT,
        )

        self._draw_speed_button(
            screen,
            "CENTER",
            self.CENTER_RECT,
        )

        self._draw_speed_button(
            screen,
            "FIND",
            self.FIND_RECT,
        )

        self._draw_speed_button(
            screen,
            "SLEW",
            self.SLEW_RECT,
        )

        self.display.button(
            screen,
            self.BACK_RECT,
            "TILBAGE",
        )

        status = (
            f"Koerer {self.DIRECTION_NAMES[self.active_direction]}"
            if self.active_direction
            else self.message
        )

        cv2.putText(
            screen,
            status[:55],
            (8, 267),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.34,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )

        self.display.show(screen)

    def _draw_direction_button(
        self,
        screen,
        rect,
        label,
        direction,
    ):
        selected = (
            self.active_direction == direction
        )

        self.display.button(
            screen,
            rect,
            label,
            selected=selected,
            enabled=self.mount.connected,
        )

    def _draw_speed_button(
        self,
        screen,
        speed,
        rect,
    ):
        selected = (
            self.slew.speed == speed
        )

        danger = (
            speed == "SLEW"
            and selected
        )

        self.display.button(
            screen,
            rect,
            self.SPEED_LABELS[speed],
            selected=selected,
            danger=danger,
            enabled=self.mount.connected,
        )

    def _read_action(self):
        """
        Returnér én handling fra tastatur eller touch.
        """

        key = (
            self.keyboard.read()
            if self.keyboard is not None
            else None
        )

        keyboard_actions = {
            "n": "move:n",
            "s": "move:s",
            "e": "move:e",
            "w": "move:w",

            "x": "stop",

            "g": "speed:GUIDE",
            "c": "speed:CENTER",
            "f": "speed:FIND",
            "m": "speed:SLEW",

            "q": "back",
            "\x1b": "back",
        }

        if key in keyboard_actions:
            return keyboard_actions[key]

        position = self.touch.read_release()

        if position is None:
            return None

        x, y = position

        if self._inside(x, y, self.NORTH_RECT):
            return "move:n"

        if self._inside(x, y, self.WEST_RECT):
            return "move:w"

        if self._inside(x, y, self.STOP_RECT):
            return "stop"

        if self._inside(x, y, self.EAST_RECT):
            return "move:e"

        if self._inside(x, y, self.SOUTH_RECT):
            return "move:s"

        if self._inside(x, y, self.GUIDE_RECT):
            return "speed:GUIDE"

        if self._inside(x, y, self.CENTER_RECT):
            return "speed:CENTER"

        if self._inside(x, y, self.FIND_RECT):
            return "speed:FIND"

        if self._inside(x, y, self.SLEW_RECT):
            return "speed:SLEW"

        if self._inside(x, y, self.BACK_RECT):
            return "back"

        return None

    def _start_direction(
        self,
        direction,
    ):
        if not self.mount.connected:
            self.message = "Mount ikke tilsluttet"
            return

        try:
            # Stop en eventuel tidligere retning.
            self._stop_safely()

            actions = {
                "n": self.slew.start_north,
                "s": self.slew.start_south,
                "e": self.slew.start_east,
                "w": self.slew.start_west,
            }

            actions[direction]()

            self.active_direction = direction

            self.message = (
                f"{self.DIRECTION_NAMES[direction]} "
                f"{self.slew.speed}"
            )

            if self.logger is not None:
                self.logger.info(
                    "Manual Slew start: "
                    f"{direction} "
                    f"speed={self.slew.speed}"
                )

        except Exception as error:
            self.active_direction = None
            self.message = f"Fejl: {error}"

            if self.logger is not None:
                self.logger.exception(
                    "Manual Slew movement failed"
                )

            self._stop_safely()

    def _set_speed(
        self,
        speed,
    ):
        if not self.mount.connected:
            self.message = "Mount ikke tilsluttet"
            return

        try:
            self._stop_safely()
            self.slew.set_speed(speed)

            self.message = (
                f"Hastighed: "
                f"{self.SPEED_LABELS[speed]}"
            )

            if self.logger is not None:
                self.logger.info(
                    f"Manual Slew speed={speed}"
                )

        except Exception as error:
            self.message = f"Fejl: {error}"

            if self.logger is not None:
                self.logger.exception(
                    "Manual Slew speed change failed"
                )

            self._stop_safely()

    def _stop_safely(self):
        try:
            self.slew.safe_stop()
        finally:
            self.active_direction = None

    @staticmethod
    def _inside(
        x,
        y,
        rect,
    ):
        x1, y1, x2, y2 = rect

        return (
            x1 <= x <= x2
            and y1 <= y <= y2
        )
