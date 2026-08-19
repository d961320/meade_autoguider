import glob
import select
import termios
import tty

from evdev import InputDevice, ecodes


KEY_MAP = {
    ecodes.KEY_N: "n",
    ecodes.KEY_P: "p",
    ecodes.KEY_V: "v",
    ecodes.KEY_Q: "q",
    ecodes.KEY_X: "x",
    ecodes.KEY_R: "r",
    ecodes.KEY_E: "e",
    ecodes.KEY_W: "w",
    ecodes.KEY_S: "s",
    ecodes.KEY_ENTER: "\n",
    ecodes.KEY_ESC: "\x1b",
    ecodes.KEY_DOWN: "down",
    ecodes.KEY_UP: "up",
    ecodes.KEY_KPPLUS: "+",
    ecodes.KEY_EQUAL: "+",
    ecodes.KEY_KPMINUS: "-",
    ecodes.KEY_MINUS: "-",
}


class Keyboard:
    def __init__(self):
        self.tty_file = None
        self.old_settings = None
        self.local_devices = []

    def open(self):
        self._open_terminal()
        self._find_local_keyboards()

    def close(self):
        if self.tty_file is not None and self.old_settings is not None:
            try:
                termios.tcsetattr(
                    self.tty_file.fileno(),
                    termios.TCSADRAIN,
                    self.old_settings,
                )
            except (OSError, termios.error):
                pass

        if self.tty_file is not None:
            try:
                self.tty_file.close()
            except OSError:
                pass

        self.tty_file = None
        self.old_settings = None

        for device in self.local_devices:
            try:
                device.close()
            except OSError:
                pass

        self.local_devices = []

    def read(self):
        key = self._read_local()

        if key is not None:
            return key

        return self._read_terminal()

    def _open_terminal(self):
        try:
            self.tty_file = open(
                "/dev/tty",
                "r",
                encoding="utf-8",
            )

            self.old_settings = termios.tcgetattr(
                self.tty_file.fileno()
            )

            tty.setcbreak(
                self.tty_file.fileno()
            )

            print("Terminal/SSH-tastatur aktivt.")

        except (OSError, termios.error):
            self.tty_file = None
            self.old_settings = None

    def _find_local_keyboards(self):
        for path in sorted(glob.glob("/dev/input/event*")):
            try:
                device = InputDevice(path)
                key_codes = device.capabilities().get(
                    ecodes.EV_KEY,
                    [],
                )

                if (
                    ecodes.KEY_Q in key_codes
                    and ecodes.KEY_ENTER in key_codes
                ):
                    self.local_devices.append(device)
                    print("Lokalt tastatur:", device.name, path)
                else:
                    device.close()

            except OSError:
                continue

    def _read_terminal(self):
        if self.tty_file is None:
            return None

        try:
            readable, _, _ = select.select(
                [self.tty_file],
                [],
                [],
                0,
            )

            if readable:
                key = self.tty_file.read(1)

                if key:
                    return key.lower()

        except (OSError, ValueError):
            return None

        return None

    def _read_local(self):
        if not self.local_devices:
            return None

        fds = [device.fd for device in self.local_devices]

        try:
            readable, _, _ = select.select(
                fds,
                [],
                [],
                0,
            )
        except (OSError, ValueError):
            return None

        if not readable:
            return None

        for device in self.local_devices:
            if device.fd not in readable:
                continue

            try:
                events = device.read()
            except (BlockingIOError, OSError):
                continue

            for event in events:
                if (
                    event.type == ecodes.EV_KEY
                    and event.value == 1
                ):
                    key = KEY_MAP.get(event.code)

                    if key is not None:
                        return key

        return None
