#!/usr/bin/env python3

"""
AutoStar V2-driver.

Denne version bruger:

    mount/base.py
    mount/serial_connection.py

Den eksisterende mount/autostar.py ændres ikke endnu.
"""

from __future__ import annotations

import time
from typing import Any

from mount.base import MountBase
from mount.serial_connection import SerialConnection


class AutoStarV2(MountBase):
    """Driver til Meade AutoStar #497."""

    DRIVER_NAME = "Meade AutoStar"
    DRIVER_VERSION = "2.0"

    CAPABILITIES = {
        "read_coordinates": True,
        "guide_pulse": True,
        "manual_slew": True,
        "goto": False,
    }

    SPEED_COMMANDS = {
        "GUIDE": ":RG#",
        "CENTER": ":RC#",
        "FIND": ":RM#",
        "SLEW": ":RS#",
    }

    MOVE_COMMANDS = {
        "n": ":Mn#",
        "s": ":Ms#",
        "e": ":Me#",
        "w": ":Mw#",
    }

    STOP_COMMANDS = {
        "n": ":Qn#",
        "s": ":Qs#",
        "e": ":Qe#",
        "w": ":Qw#",
    }

    def __init__(
        self,
        port: str | None = None,
        connection: SerialConnection | None = None,
    ) -> None:
        self.serial = (
            connection
            if connection is not None
            else SerialConnection(
                port=port,
                baudrate=9600,
                timeout=1.0,
                write_timeout=1.0,
                startup_delay=0.5,
            )
        )

        self.product = ""
        self.firmware = ""
        self.last_error: str | None = None
        self.active_direction: str | None = None
        self.speed_mode = "CENTER"

    @property
    def connected(self) -> bool:
        return self.serial.connected

    @property
    def port(self) -> str | None:
        return self.serial.port

    def connect(self) -> bool:
        self.last_error = None

        try:
            if not self.serial.connect():
                self.last_error = (
                    self.serial.last_error
                    or "Kunne ikke forbinde til AutoStar"
                )
                return False

            self.product = self.serial.query(
                ":GVP#"
            )

            self.firmware = self.serial.query(
                ":GVN#"
            )

            return True

        except Exception as error:
            self.last_error = str(error)
            self.disconnect()
            return False

    def disconnect(self) -> None:
        self.safe_stop()
        self.serial.close()
        self.active_direction = None

    # Kompatibilitet med den gamle AutoStar-driver.
    def close(self) -> None:
        self.disconnect()

    def send(
        self,
        command: str,
    ) -> None:
        self.serial.send(command)

    def query(
        self,
        command: str,
    ) -> str:
        return self.serial.query(command)

    def get_ra(self) -> str | None:
        return self.query(":GR#")

    def get_dec(self) -> str | None:
        return self.query(":GD#")

    def set_speed(
        self,
        speed_mode: str,
    ) -> None:
        speed_mode = str(
            speed_mode
        ).strip().upper()

        if speed_mode not in self.SPEED_COMMANDS:
            raise ValueError(
                "Hastighed skal være "
                "GUIDE, CENTER, FIND eller SLEW"
            )

        self.stop()

        self.send(
            self.SPEED_COMMANDS[speed_mode]
        )

        self.speed_mode = speed_mode

    def start_move(
        self,
        direction: str,
        speed_mode: str | None = None,
    ) -> None:
        direction = str(
            direction
        ).strip().lower()

        if direction not in self.MOVE_COMMANDS:
            raise ValueError(
                "Retning skal være n, s, e eller w"
            )

        if not self.connected:
            raise RuntimeError(
                "AutoStar er ikke forbundet"
            )

        if self.active_direction is not None:
            self.stop()

        if speed_mode is not None:
            self.set_speed(speed_mode)

        self.send(
            self.SPEED_COMMANDS[self.speed_mode]
        )

        self.send(
            self.MOVE_COMMANDS[direction]
        )

        self.active_direction = direction

    def stop_direction(
        self,
        direction: str,
    ) -> None:
        direction = str(
            direction
        ).strip().lower()

        if direction not in self.STOP_COMMANDS:
            raise ValueError(
                "Retning skal være n, s, e eller w"
            )

        if self.connected:
            self.send(
                self.STOP_COMMANDS[direction]
            )
            self.send(":Q#")

        if self.active_direction == direction:
            self.active_direction = None

    def stop(self) -> None:
        if not self.connected:
            self.active_direction = None
            return

        direction = self.active_direction

        try:
            if direction in self.STOP_COMMANDS:
                self.send(
                    self.STOP_COMMANDS[direction]
                )
        finally:
            self.send(":Q#")
            self.active_direction = None

    def pulse(
        self,
        direction: str,
        milliseconds: int,
        speed_mode: str = "CENTER",
    ) -> None:
        direction = str(
            direction
        ).strip().lower()

        speed_mode = str(
            speed_mode
        ).strip().upper()

        if direction not in self.MOVE_COMMANDS:
            raise ValueError(
                "Retning skal være n, s, e eller w"
            )

        if speed_mode not in self.SPEED_COMMANDS:
            raise ValueError(
                "Hastighed skal være "
                "GUIDE, CENTER, FIND eller SLEW"
            )

        if not isinstance(milliseconds, int):
            raise TypeError(
                "Pulslængden skal være et heltal"
            )

        if not 50 <= milliseconds <= 5000:
            raise ValueError(
                "Pulslængden skal være 50-5000 ms"
            )

        if speed_mode == "SLEW":
            milliseconds = min(
                milliseconds,
                1000,
            )

        try:
            self.start_move(
                direction,
                speed_mode,
            )

            time.sleep(
                milliseconds / 1000.0
            )

        finally:
            try:
                self.stop_direction(direction)
            except Exception:
                self.safe_stop()

    def pulse_north(
        self,
        milliseconds: int,
        speed_mode: str = "CENTER",
    ) -> None:
        self.pulse(
            "n",
            milliseconds,
            speed_mode,
        )

    def pulse_south(
        self,
        milliseconds: int,
        speed_mode: str = "CENTER",
    ) -> None:
        self.pulse(
            "s",
            milliseconds,
            speed_mode,
        )

    def pulse_east(
        self,
        milliseconds: int,
        speed_mode: str = "CENTER",
    ) -> None:
        self.pulse(
            "e",
            milliseconds,
            speed_mode,
        )

    def pulse_west(
        self,
        milliseconds: int,
        speed_mode: str = "CENTER",
    ) -> None:
        self.pulse(
            "w",
            milliseconds,
            speed_mode,
        )

    # Gamle metode-navne beholdes for kompatibilitet.
    def north(
        self,
        milliseconds: int,
        speed_mode: str = "CENTER",
    ) -> None:
        self.pulse_north(
            milliseconds,
            speed_mode,
        )

    def south(
        self,
        milliseconds: int,
        speed_mode: str = "CENTER",
    ) -> None:
        self.pulse_south(
            milliseconds,
            speed_mode,
        )

    def east(
        self,
        milliseconds: int,
        speed_mode: str = "CENTER",
    ) -> None:
        self.pulse_east(
            milliseconds,
            speed_mode,
        )

    def west(
        self,
        milliseconds: int,
        speed_mode: str = "CENTER",
    ) -> None:
        self.pulse_west(
            milliseconds,
            speed_mode,
        )

    def status(self) -> dict[str, Any]:
        status = super().status()

        status.update(
            {
                "port": self.port,
                "product": self.product,
                "firmware": self.firmware,
                "speed_mode": self.speed_mode,
                "active_direction": (
                    self.active_direction
                ),
                "last_error": self.last_error,
            }
        )

        return status
