#!/usr/bin/env python3

from gui.display import Display
from gui.keyboard import Keyboard
from gui.manual_slew_screen import ManualSlewScreen
from gui.touch import Touchscreen
from mount.controller import MountController
from system.logger import get_logger


display = Display()
touch = Touchscreen()
keyboard = Keyboard()
mount = MountController()
logger = get_logger()

try:
    display.open()
    touch.open()
    keyboard.open()

    if not mount.connect():
        raise RuntimeError(
            "Kunne ikke forbinde til AutoStar"
        )

    screen = ManualSlewScreen(
        display=display,
        touch=touch,
        keyboard=keyboard,
        mount_controller=mount,
        logger=logger,
    )

    screen.run()

finally:
    try:
        mount.safe_stop()
    except Exception:
        pass

    mount.disconnect()
    keyboard.close()
    touch.close()

    display.blank()
    display.close()
