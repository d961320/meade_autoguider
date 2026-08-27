#!/usr/bin/env python3

"""
Fælles seriel forbindelse til mount-drivere.

Denne klasse håndterer:

- søgning efter serielporte
- åbning og lukning af port
- afsendelse af kommandoer
- læsning af #-terminerede svar
- timeout
- sikker oprydning

AutoStar- og LX200-driverne kan senere bruge denne klasse,
så de ikke selv behøver importere eller håndtere pyserial.
"""

from __future__ import annotations

import glob
import os
import time
from typing import Any

import serial


class SerialConnection:
    """Fælles seriel transport til LX200-lignende mounts."""

    def __init__(
        self,
        port: str | None = None,
        baudrate: int = 9600,
        timeout: float = 1.0,
        write_timeout: float | None = None,
        startup_delay: float = 0.5,
        connection: Any | None = None,
    ) -> None:
        self.requested_port = port
        self.baudrate = int(baudrate)
        self.timeout = float(timeout)

        self.write_timeout = (
            float(write_timeout)
            if write_timeout is not None
            else self.timeout
        )

        self.startup_delay = float(startup_delay)

        # Bruges til simulator- og enhedstest.
        self.connection = connection

        self.port: str | None = None
        self.last_error: str | None = None

    @property
    def connected(self) -> bool:
        """Returnér True, når forbindelsen findes og er åben."""

        if self.connection is None:
            return False

        return bool(
            getattr(
                self.connection,
                "is_open",
                True,
            )
        )

    def find_ports(self) -> list[str]:
        """
        Find sandsynlige USB-serielporte.

        /dev/serial/by-id foretrækkes, fordi navnene dér
        normalt er mere stabile end /dev/ttyUSB0 osv.
        """

        candidates: list[str] = []

        candidates.extend(
            sorted(
                glob.glob(
                    "/dev/serial/by-id/*"
                )
            )
        )

        candidates.extend(
            sorted(
                glob.glob(
                    "/dev/ttyUSB*"
                )
            )
        )

        candidates.extend(
            sorted(
                glob.glob(
                    "/dev/ttyACM*"
                )
            )
        )

        result: list[str] = []

        for candidate in candidates:
            real_path = os.path.realpath(
                candidate
            )

            if real_path not in result:
                result.append(real_path)

        return result

    def connect(self) -> bool:
        """
        Åbn den ønskede port eller prøv fundne porte én ad gangen.

        Returnerer True ved succes og False ved fejl.
        """

        self.last_error = None

        # En simuleret eller allerede åben forbindelse.
        if self.connected:
            self.port = (
                self.requested_port
                or getattr(
                    self.connection,
                    "port",
                    "simulator",
                )
            )

            return True

        candidates = (
            [self.requested_port]
            if self.requested_port
            else self.find_ports()
        )

        for port in candidates:
            if not port:
                continue

            try:
                connection = serial.Serial(
                    port=port,
                    baudrate=self.baudrate,
                    timeout=self.timeout,
                    write_timeout=self.write_timeout,
                )

                self.connection = connection
                self.port = port

                if self.startup_delay > 0:
                    time.sleep(
                        self.startup_delay
                    )

                return True

            except Exception as error:
                self.last_error = str(error)

                try:
                    if self.connection is not None:
                        self.connection.close()
                except Exception:
                    pass

                self.connection = None
                self.port = None

        return False

    def close(self) -> None:
        """Luk forbindelsen."""

        if self.connection is not None:
            try:
                self.connection.close()
            finally:
                self.connection = None

        self.port = None

    def send(
        self,
        command: str,
        clear_input: bool = True,
    ) -> None:
        """
        Send en ASCII-kommando.

        LX200-kommandoer skal normalt begynde med :
        og slutte med #.
        """

        self._require_connection()
        self._validate_command(command)

        if clear_input:
            self.clear_input()

        self.connection.write(
            command.encode("ascii")
        )

        flush = getattr(
            self.connection,
            "flush",
            None,
        )

        if callable(flush):
            flush()

    def query(
        self,
        command: str,
        timeout: float = 2.0,
        terminator: bytes = b"#",
        encoding: str = "latin1",
    ) -> str:
        """
        Send en kommando og læs frem til terminatoren.

        Eksempel:
            :GR# -> 12:34:56#
        """

        self.send(command)

        reply = self.read_until(
            terminator=terminator,
            timeout=timeout,
        )

        if not reply:
            raise TimeoutError(
                f"Intet svar på {command}"
            )

        return (
            reply.decode(
                encoding,
                errors="replace",
            )
            .replace("\xdf", "°")
            .strip()
        )

    def read_until(
        self,
        terminator: bytes = b"#",
        timeout: float = 2.0,
    ) -> bytes:
        """Læs bytes frem til terminatoren eller timeout."""

        self._require_connection()

        if not terminator:
            raise ValueError(
                "Terminator må ikke være tom"
            )

        reply = bytearray()
        deadline = (
            time.monotonic()
            + float(timeout)
        )

        while time.monotonic() < deadline:
            chunk = self.connection.read(1)

            if not chunk:
                continue

            if chunk == terminator:
                return bytes(reply)

            reply.extend(chunk)

        return bytes(reply)

    def clear_input(self) -> None:
        """Tøm inputbufferen, hvis forbindelsen understøtter det."""

        self._require_connection()

        reset_input_buffer = getattr(
            self.connection,
            "reset_input_buffer",
            None,
        )

        if callable(reset_input_buffer):
            reset_input_buffer()

    def _require_connection(self) -> None:
        if not self.connected:
            raise RuntimeError(
                "Den serielle forbindelse er ikke åben"
            )

    @staticmethod
    def _validate_command(
        command: str,
    ) -> None:
        if not isinstance(command, str):
            raise TypeError(
                "Kommandoen skal være tekst"
            )

        if not command:
            raise ValueError(
                "Kommandoen må ikke være tom"
            )

        if not command.startswith(":"):
            raise ValueError(
                "Kommandoen skal begynde med ':'"
            )

        if not command.endswith("#"):
            raise ValueError(
                "Kommandoen skal slutte med '#'"
            )

    def __enter__(
        self,
    ) -> "SerialConnection":
        if not self.connect():
            raise RuntimeError(
                self.last_error
                or "Kunne ikke åbne serielport"
            )

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()
