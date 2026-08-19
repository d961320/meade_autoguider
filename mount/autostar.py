import glob
import os
import time

import serial


class AutoStar:
    def __init__(self, port=None):
        self.requested_port = port
        self.ser = None
        self.port = None
        self.product = ""
        self.firmware = ""

    def _find_ports(self):
        ports = []
        ports.extend(sorted(glob.glob("/dev/serial/by-id/*")))
        ports.extend(sorted(glob.glob("/dev/ttyUSB*")))
        ports.extend(sorted(glob.glob("/dev/ttyACM*")))

        result = []

        for path in ports:
            real_path = os.path.realpath(path)

            if real_path not in result:
                result.append(real_path)

        return result

    def connect(self):
        candidates = (
            [self.requested_port]
            if self.requested_port
            else self._find_ports()
        )

        for port in candidates:
            try:
                self.ser = serial.Serial(
                    port,
                    9600,
                    timeout=1,
                    write_timeout=1,
                )

                self.port = port
                time.sleep(0.5)

                self.product = self.query(":GVP#")
                self.firmware = self.query(":GVN#")

                return True

            except Exception:
                try:
                    self.ser.close()
                except Exception:
                    pass

                self.ser = None

        return False

    def close(self):
        try:
            self.stop()
        except Exception:
            pass

        if self.ser:
            self.ser.close()

        self.ser = None

    def send(self, command):
        if self.ser is None:
            raise RuntimeError("Ikke forbundet")

        self.ser.reset_input_buffer()
        self.ser.write(command.encode("ascii"))
        self.ser.flush()

    def query(self, command):
        self.send(command)

        reply = b""
        deadline = time.time() + 2

        while time.time() < deadline:
            char = self.ser.read(1)

            if not char:
                continue

            if char == b"#":
                break

            reply += char

        return (
            reply.decode("latin1")
            .replace("\xdf", "°")
        )

    def get_ra(self):
        return self.query(":GR#")

    def get_dec(self):
        return self.query(":GD#")

    def stop(self):
        if self.ser:
            self.send(":Q#")

    def pulse(self, direction, milliseconds):
        direction = direction.lower()

        if direction not in ("n", "s", "e", "w"):
            raise ValueError("Retning skal være n, s, e eller w")

        milliseconds = max(100, min(5000, int(milliseconds)))

        self.send(":RC#")

        try:
            self.send(f":M{direction}#")
            time.sleep(milliseconds / 1000.0)
        finally:
            try:
                self.send(f":Q{direction}#")
            finally:
                self.send(":Q#")

    def north(self, milliseconds):
        self.pulse("n", milliseconds)

    def south(self, milliseconds):
        self.pulse("s", milliseconds)

    def east(self, milliseconds):
        self.pulse("e", milliseconds)

    def west(self, milliseconds):
        self.pulse("w", milliseconds)
