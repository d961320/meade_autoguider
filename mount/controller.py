from mount.autostar import AutoStar


class MountController:
    MIN_PULSE_MS = 100
    MAX_PULSE_MS = 5000

    def __init__(self, port=None):
        self.driver = AutoStar(port)
        self.last_error = None

    @property
    def connected(self):
        serial_port = self.driver.ser

        if serial_port is None:
            return False

        return getattr(serial_port, "is_open", True)

    def connect(self):
        self.last_error = None

        try:
            connected = self.driver.connect()

            if not connected:
                self.last_error = "Kunne ikke forbinde til AutoStar"

            return connected

        except Exception as error:
            self.last_error = str(error)
            self.safe_stop()
            return False

    def disconnect(self):
        self.safe_stop()

        try:
            self.driver.close()
        except Exception as error:
            self.last_error = str(error)

    def status(self):
        ra = None
        dec = None

        if self.connected:
            try:
                ra = self.driver.get_ra()
                dec = self.driver.get_dec()

            except Exception as error:
                self.last_error = str(error)
                self.safe_stop()

        return {
            "connected": self.connected,
            "port": self.driver.port,
            "product": self.driver.product or "",
            "firmware": self.driver.firmware or "",
            "ra": ra,
            "dec": dec,
            "last_error": self.last_error,
        }

    def stop(self):
        if not self.connected:
            return

        self.driver.stop()
        self.last_error = None

    def safe_stop(self):
        try:
            if self.connected:
                self.driver.stop()
        except Exception:
            pass

    def _pulse(self, function, milliseconds):
        if not isinstance(milliseconds, int):
            raise TypeError("Pulslængden skal være et heltal")

        if not self.MIN_PULSE_MS <= milliseconds <= self.MAX_PULSE_MS:
            raise ValueError(
                "Pulslængden skal være mellem 100 og 5000 ms"
            )

        if not self.connected:
            raise RuntimeError("Mountet er ikke forbundet")

        try:
            function(milliseconds)
            self.last_error = None

        except Exception as error:
            self.last_error = str(error)
            self.safe_stop()
            raise

    def pulse_east(self, milliseconds):
        self._pulse(self.driver.east, milliseconds)

    def pulse_west(self, milliseconds):
        self._pulse(self.driver.west, milliseconds)

    def pulse_north(self, milliseconds):
        self._pulse(self.driver.north, milliseconds)

    def pulse_south(self, milliseconds):
        self._pulse(self.driver.south, milliseconds)
