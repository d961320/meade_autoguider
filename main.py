import time

from gui.display import Display
from gui.keyboard import Keyboard
from gui.screens import Screens
from gui.touch import Touchscreen
from mount.controller import MountController
from system.logger import get_logger


def main():
    logger = get_logger()

    display = Display()
    touch = Touchscreen()
    keyboard = Keyboard()
    mount = MountController()

    display_open = False

    try:
        display.open()
        display_open = True

        display.splash("Starter system...")
        logger.info("Application starting")

        touch.open()
        keyboard.open()

        display.splash("Søger AutoStar...")
        mount.connect()

        if mount.connected:
            logger.info("AutoStar connected")
        else:
            logger.warning("AutoStar not connected")

        screens = Screens(
            display,
            touch,
            keyboard,
            mount,
            logger,
        )

        screens.run()
        return 0

    except KeyboardInterrupt:
        logger.info("Ctrl+C received")
        return 130

    except Exception as error:
        logger.exception("Unhandled system error")
        print("SYSTEMFEJL:", error)

        if display_open:
            try:
                display.info_screen(
                    "SYSTEMFEJL",
                    [
                        ("Fejl", str(error)[:38]),
                    ],
                    footer="Programmet afsluttes",
                )
                time.sleep(3)
            except Exception:
                pass

        return 1

    finally:
        mount.safe_stop()
        mount.disconnect()
        keyboard.close()
        touch.close()

        if display_open:
            try:
                display.shutdown()
                time.sleep(2)
                display.blank()
            finally:
                display.close()

        logger.info("Application stopped")


if __name__ == "__main__":
    raise SystemExit(main())
