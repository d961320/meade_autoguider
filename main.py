import subprocess
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
    requested_action = "exit"
    exit_code = 0

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
            logger.warning(
                "AutoStar not connected"
            )

        screens = Screens(
            display,
            touch,
            keyboard,
            mount,
            logger,
        )

        requested_action = (
            screens.run()
            or "exit"
        )

    except KeyboardInterrupt:
        logger.info("Ctrl+C received")
        exit_code = 130

    except Exception as error:
        logger.exception(
            "Unhandled system error"
        )

        print(
            "SYSTEMFEJL:",
            error,
        )

        if display_open:
            try:
                display.info_screen(
                    "SYSTEMFEJL",
                    [
                        (
                            "Fejl",
                            str(error)[:38],
                        ),
                    ],
                    footer="Programmet afsluttes",
                )

                time.sleep(3)

            except Exception:
                pass

        exit_code = 1

    finally:
        try:
            mount.safe_stop()
        except Exception:
            pass

        try:
            mount.disconnect()
        except Exception:
            pass

        try:
            keyboard.close()
        except Exception:
            pass

        try:
            touch.close()
        except Exception:
            pass

        if display_open:
            try:
                display.shutdown()
                time.sleep(2)
                display.blank()

            except Exception:
                pass

            finally:
                try:
                    display.close()
                except Exception:
                    pass

        logger.info("Application stopped")

    if (
        requested_action == "poweroff"
        and exit_code == 0
    ):
        logger.info(
            "Raspberry Pi poweroff requested"
        )

        try:
            subprocess.run(
                [
                    "sudo",
                    "-n",
                    "systemctl",
                    "poweroff",
                ],
                check=True,
            )

        except subprocess.CalledProcessError as error:
            logger.exception(
                "Raspberry Pi poweroff failed"
            )

            print(
                "Kunne ikke slukke Raspberry Pi:",
                error,
            )

            return 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
