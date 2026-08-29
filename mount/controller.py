#!/usr/bin/env python3

"""
Fælles MountController.

Controlleren skjuler den valgte mount-driver for resten
af programmet. GUI, guiding og Manual Slew bruger derfor
samme interface, uanset om driveren er AutoStar, AutoStarV2
eller senere LX200.
"""

from config import MOUNT_DRIVER, MOUNT_PORT
from mount.factory import create_mount


class MountController:
    MIN_PULSE_MS = 100
    MAX_PULSE_MS = 5000

    def __init__(
        self,
        port=None,
        driver_name=None,
        **driver_options,
    ):
        if driver_name is None:
            driver_name = MOUNT_DRIVER

        if port is None:
            port = MOUNT_PORT

        self.driver_name = driver_name

        self.driver = create_mount(
            driver_name=driver_name,
            port=port,
            **driver_options,
        )

        self.last_error = None

    @property
    def connected(self):
        """
        Returnér forbindelsesstatus for både gamle og nye drivere.
        """

        connected = getattr(
            self.driver,
            "connected",
            None,
        )

        if connected is not None:
            return bool(connected)

        serial_port = getattr(
            self.driver,
            "ser",
            None,
        )

        if serial_port is None:
            return False

        return bool(
            getattr(
                serial_port,
                "is_open",
                True,
            )
        )

    def connect(self):
        self.last_error = None

        try:
            connected = self.driver.connect()

            if not connected:
                driver_error = getattr(
                    self.driver,
                    "last_error",
                    None,
                )

                self.last_error = (
                    driver_error
                    or "Kunne ikke forbinde til mountet"
                )

            return connected

        except Exception as error:
            self.last_error = str(error)
            self.safe_stop()
            return False

    def disconnect(self):
        self.safe_stop()

        try:
            disconnect_method = getattr(
                self.driver,
                "disconnect",
                None,
            )

            if callable(disconnect_method):
                disconnect_method()
            else:
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
            "driver": getattr(
                self.driver,
                "DRIVER_NAME",
                type(self.driver).__name__,
            ),
            "driver_version": getattr(
                self.driver,
                "DRIVER_VERSION",
                "",
            ),
            "port": getattr(
                self.driver,
                "port",
                None,
            ),
            "product": getattr(
                self.driver,
                "product",
                "",
            ) or "",
            "firmware": getattr(
                self.driver,
                "firmware",
                "",
            ) or "",
            "ra": ra,
            "dec": dec,
            "last_error": self.last_error,
        }

    def stop(self):
        if not self.connected:
            return

        try:
            self.driver.stop()
            self.last_error = None

        except Exception as error:
            self.last_error = str(error)
            raise

    def safe_stop(self):
        try:
            safe_stop_method = getattr(
                self.driver,
                "safe_stop",
                None,
            )

            if callable(safe_stop_method):
                safe_stop_method()

            elif self.connected:
                self.driver.stop()

        except Exception:
            pass

    def _pulse(
        self,
        function,
        milliseconds,
        speed_mode=None,
    ):
        if not isinstance(milliseconds, int):
            raise TypeError(
                "Pulslængden skal være et heltal"
            )

        if not (
            self.MIN_PULSE_MS
            <= milliseconds
            <= self.MAX_PULSE_MS
        ):
            raise ValueError(
                "Pulslængden skal være mellem "
                "100 og 5000 ms"
            )

        if not self.connected:
            raise RuntimeError(
                "Mountet er ikke forbundet"
            )

        try:
            if speed_mode is None:
                function(milliseconds)
            else:
                function(
                    milliseconds,
                    speed_mode,
                )

            self.last_error = None

        except Exception as error:
            self.last_error = str(error)
            self.safe_stop()
            raise

    def pulse_east(
        self,
        milliseconds,
        speed_mode=None,
    ):
        function = getattr(
            self.driver,
            "pulse_east",
            None,
        )

        if not callable(function):
            function = self.driver.east

        self._pulse(
            function,
            milliseconds,
            speed_mode,
        )

    def pulse_west(
        self,
        milliseconds,
        speed_mode=None,
    ):
        function = getattr(
            self.driver,
            "pulse_west",
            None,
        )

        if not callable(function):
            function = self.driver.west

        self._pulse(
            function,
            milliseconds,
            speed_mode,
        )

    def pulse_north(
        self,
        milliseconds,
        speed_mode=None,
    ):
        function = getattr(
            self.driver,
            "pulse_north",
            None,
        )

        if not callable(function):
            function = self.driver.north

        self._pulse(
            function,
            milliseconds,
            speed_mode,
        )

    def pulse_south(
        self,
        milliseconds,
        speed_mode=None,
    ):
        function = getattr(
            self.driver,
            "pulse_south",
            None,
        )

        if not callable(function):
            function = self.driver.south

        self._pulse(
            function,
            milliseconds,
            speed_mode,
        )
