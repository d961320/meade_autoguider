#!/usr/bin/env python3

"""
Kontinuerlig manuel bevægelse af Meade-mount.

Dette modul er adskilt fra den eksisterende Guide Test.

Eksempel:

    slew = ManualSlew(mount)

    slew.set_speed("FIND")
    slew.start("e")

    # Mountet bevæger sig, indtil:
    slew.stop()

ManualSlew forventer et eksisterende MountController-objekt,
hvor den fungerende AutoStar-driver findes som mount.driver.
"""


class ManualSlew:
    """Sikker manuel styring af mountet."""

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

    def __init__(self, mount_controller):
        self.mount = mount_controller

        self.speed = "FIND"
        self.active_direction = None
        self.last_error = None

    @property
    def connected(self):
        """Returnér True, når MountController er forbundet."""

        return bool(self.mount.connected)

    @property
    def moving(self):
        """Returnér True, når en manuel bevægelse er aktiv."""

        return self.active_direction is not None

    def set_speed(self, speed):
        """
        Vælg manuel bevægelseshastighed.

        Muligheder:
            GUIDE
            CENTER
            FIND
            SLEW
        """

        speed = str(speed).strip().upper()

        if speed not in self.SPEED_COMMANDS:
            raise ValueError(
                "Hastighed skal være "
                "GUIDE, CENTER, FIND eller SLEW"
            )

        self._require_connection()

        # Stop altid en eksisterende bevægelse,
        # før hastigheden ændres.
        self.stop()

        try:
            self._send(
                self.SPEED_COMMANDS[speed]
            )

            self.speed = speed
            self.last_error = None

        except Exception as error:
            self.last_error = str(error)
            self.safe_stop()
            raise

    def next_speed(self):
        """
        Skift til næste hastighed.

        GUIDE -> CENTER -> FIND -> SLEW -> GUIDE
        """

        speeds = [
            "GUIDE",
            "CENTER",
            "FIND",
            "SLEW",
        ]

        current_index = speeds.index(
            self.speed
        )

        next_index = (
            current_index + 1
        ) % len(speeds)

        self.set_speed(
            speeds[next_index]
        )

        return self.speed

    def start(self, direction):
        """
        Start kontinuerlig bevægelse.

        direction:
            n = nord
            s = syd
            e = øst
            w = vest

        Bevægelsen fortsætter, indtil stop() kaldes.
        """

        direction = str(
            direction
        ).strip().lower()

        if direction not in self.MOVE_COMMANDS:
            raise ValueError(
                "Retning skal være n, s, e eller w"
            )

        self._require_connection()

        # Undgå at starte to retninger samtidig.
        if self.active_direction is not None:
            self.stop()

        try:
            # Send hastigheden igen før bevægelsen.
            # Det gør tilstanden tydelig og robust.
            self._send(
                self.SPEED_COMMANDS[self.speed]
            )

            self._send(
                self.MOVE_COMMANDS[direction]
            )

            self.active_direction = direction
            self.last_error = None

        except Exception as error:
            self.last_error = str(error)
            self.safe_stop()
            raise

    def start_north(self):
        self.start("n")

    def start_south(self):
        self.start("s")

    def start_east(self):
        self.start("e")

    def start_west(self):
        self.start("w")

    def stop(self):
        """
        Stop den aktive retning og send derefter samlet STOP.

        Metoden må gerne kaldes, selv om mountet allerede står stille.
        """

        if not self.connected:
            self.active_direction = None
            return

        direction = self.active_direction

        try:
            if direction in self.STOP_COMMANDS:
                self._send(
                    self.STOP_COMMANDS[direction]
                )

            # Samlet nødstop som ekstra sikkerhed.
            self._send(":Q#")

            self.active_direction = None
            self.last_error = None

        except Exception as error:
            self.active_direction = None
            self.last_error = str(error)
            raise

    def safe_stop(self):
        """
        Forsøg at stoppe mountet uden at rejse en ny fejl.

        Bruges ved undtagelser og programafslutning.
        """

        try:
            if self.connected:
                direction = self.active_direction

                if direction in self.STOP_COMMANDS:
                    self._send(
                        self.STOP_COMMANDS[direction]
                    )

                self._send(":Q#")

        except Exception:
            pass

        finally:
            self.active_direction = None

    def close(self):
        """Stop enhver bevægelse."""

        self.safe_stop()

    def _send(self, command):
        """
        Send en kommando gennem den eksisterende AutoStar-driver.

        Al protokollogik for Manual Slew holdes i denne fil.
        """

        driver = getattr(
            self.mount,
            "driver",
            None,
        )

        if driver is None:
            raise RuntimeError(
                "MountController har ingen AutoStar-driver"
            )

        send_method = getattr(
            driver,
            "send",
            None,
        )

        if not callable(send_method):
            raise RuntimeError(
                "AutoStar-driveren har ingen send()-metode"
            )

        send_method(command)

    def _require_connection(self):
        if not self.connected:
            raise RuntimeError(
                "Mountet er ikke forbundet"
            )

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        self.safe_stop()
