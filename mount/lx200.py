#!/usr/bin/env python3

"""
Generisk LX200-mountdriver.

Driveren er foreløbig ikke koblet ind i hovedprogrammet.
Den kan testes med en simuleret seriel forbindelse, indtil
det fysiske LX200-kompatible mount er tilgængeligt.
"""

from __future__ import annotations

import glob
import os
import time
from typing import Any

import serial

from mount.base import MountBase


class LX200Mount(MountBase):
    """Generisk driver til LX200-kompatible mounts."""

    DRIVER_NAME = "Generic LX200"
    DRIVER_VERSION = "0.1"

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
        baudrate: int = 9600,
        timeout: float = 1.0,
        serial_connection: Any | None = None,
    ) -> None:
        self.requested_port = port
        self.baudrate = int(baudrate)
        self.timeout = float(timeout)

        # Kan sættes til en FakeSerial under indendørs test.
        self.ser = serial_connection

        self.port: str | None = None
        self.product = ""
        self.firmware = ""
        self.last_error: str | None = None
        self.active_direction: str | None = None
        self.speed_mode = "CENTER"

    @property
    def connected(self) -> bool:
        if self.ser is None:
            return False

        return bool(
            getattr(
                self.ser,
                "is_open",
                True,
            )
        )

    def _find_ports(self) -> list[str]:
        candidates: list[str] = []

        candidates.extend(
            sorted(glob.glob("/dev/serial/by-id/*"))
        )
        candidates.extend(
            sorted(glob.glob("/dev/ttyUSB*"))
        )
        candidates.extend(
            sorted(glob.glob("/dev/ttyACM*"))
        )

        result: list[str] = []

        for candidate in candidates:
            real_path = os.path.realpath(candidate)

            if real_path not in result:
                result.append(real_path)

        return result

    def connect(self) -> bool:
        """
        Find og åbn en serielport.

        Hvis serial_connection blev leveret til konstruktøren,
        bruges den allerede eksisterende forbindelse.
        """

        self.last_error = None

        if self.connected:
            self.port = (
                self.requested_port
                or getattr(self.ser, "port", "simulator")
            )

            self._read_identity()
            return True

        candidates = (
            [self.requested_port]
            if self.requested_port
            else self._find_ports()
        )

        for port in candidates:
            if port is None:
                continue

            try:
                connection = serial.Serial(
                    port=port,
                    baudrate=self.baudrate,
                    timeout=self.timeout,
                    write_timeout=self.timeout,
                )

                self.ser = connection
                self.port = port

                time.sleep(0.5)

                self._read_identity()
                return True

            except Exception as error:
                self.last_error = str(error)

                try:
                    if self.ser is not None:
                        self.ser.close()
                except Exception:
                    pass

                self.ser = None
                self.port = None

        return False

    def disconnect(self) -> None:
        self.safe_stop()

        if self.ser is not None:
            try:
                self.ser.close()
            finally:
                self.ser = None

        self.active_direction = None

    # Kompatibilitet med den nuværende AutoStar-driver.
    def close(self) -> None:
        self.disconnect()

    def send(self, command: str) -> None:
        if not self.connected:
            raise RuntimeError(
                "LX200-mountet er ikke forbundet"
            )

        if not command.startswith(":"):
            raise ValueError(
                "LX200-kommandoen skal begynde med ':'"
            )

        if not command.endswith("#"):
            raise ValueError(
                "LX200-kommandoen skal slutte med '#'"
            )

        reset_input_buffer = getattr(
            self.ser,
            "reset_input_buffer",
            None,
        )

        if callable(reset_input_buffer):
            reset_input_buffer()

        self.ser.write(
            command.encode("ascii")
        )

        flush = getattr(
            self.ser,
            "flush",
            None,
        )

        if callable(flush):
            flush()

    def query(
        self,
        command: str,
        timeout: float = 2.0,
    ) -> str:
        self.send(command)

        reply = bytearray()
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            character = self.ser.read(1)

            if not character:
                continue

            if character == b"#":
                break

            reply.extend(character)

        if not reply:
            raise TimeoutError(
                f"Intet svar på {command}"
            )

        return (
            bytes(reply)
            .decode("latin1")
            .replace("\xdf", "°")
            .strip()
        )

    def _read_identity(self) -> None:
        """
        Produkt- og firmwarekommandoer er ikke nødvendigvis
        implementeret ens på alle LX200-kompatible mounts.
        Derfor er fejl her ikke fatale.
        """

        try:
            self.product = self.query(":GVP#")
        except Exception:
            self.product = self.DRIVER_NAME

        try:
            self.firmware = self.query(":GVN#")
        except Exception:
            self.firmware = ""

    def get_ra(self) -> str | None:
        return self.query(":GR#")

    def get_dec(self) -> str | None:
        return self.query(":GD#")

    def set_speed(self, speed_mode: str) -> None:
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

        if speed_mode is not None:
            self.set_speed(speed_mode)

        if self.active_direction is not None:
            self.stop()

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
        speed_mode: str = "GUIDE",
    ) -> None:
        direction = str(
            direction
        ).strip().lower()

        if direction not in self.MOVE_COMMANDS:
            raise ValueError(
                "Retning skal være n, s, e eller w"
            )

        if not isinstance(milliseconds, int):
            raise TypeError(
                "Pulslængden skal være et heltal"
            )

        if not 50 <= milliseconds <= 5000:
            raise ValueError(
                "Pulslængden skal være 50-5000 ms"
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
    ) -> None:
        self.pulse(
            "n",
            milliseconds,
        )

    def pulse_south(
        self,
        milliseconds: int,
    ) -> None:
        self.pulse(
            "s",
            milliseconds,
        )

    def pulse_east(
        self,
        milliseconds: int,
    ) -> None:
        self.pulse(
            "e",
            milliseconds,
        )

    def pulse_west(
        self,
        milliseconds: int,
    ) -> None:
        self.pulse(
            "w",
            milliseconds,
        )

    # Kompatibilitet med din nuværende MountController.
    def north(
        self,
        milliseconds: int,
    ) -> None:
        self.pulse_north(milliseconds)

    def south(
        self,
        milliseconds: int,
    ) -> None:
        self.pulse_south(milliseconds)

    def east(
        self,
        milliseconds: int,
    ) -> None:
        self.pulse_east(milliseconds)

    def west(
        self,
        milliseconds: int,
    ) -> None:
        self.pulse_west(milliseconds)

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
