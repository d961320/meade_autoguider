#!/usr/bin/env python3

from mount.serial_connection import SerialConnection


class FakeSerial:
    """Minimal seriel simulator."""

    def __init__(self):
        self.is_open = True
        self.port = "FAKE-SERIAL"
        self.commands = []
        self.reply = bytearray()

        self.responses = {
            ":GVP#": b"LX200 Simulator#",
            ":GVN#": b"0.1#",
            ":GR#": b"12:34:56#",
            ":GD#": b"+45\xdf12:34#",
        }

    def reset_input_buffer(self):
        self.reply.clear()

    def write(self, data):
        command = data.decode(
            "ascii"
        )

        self.commands.append(
            command
        )

        self.reply = bytearray(
            self.responses.get(
                command,
                b"",
            )
        )

    def flush(self):
        pass

    def read(self, size=1):
        if not self.reply:
            return b""

        result = bytes(
            self.reply[:size]
        )

        del self.reply[:size]

        return result

    def close(self):
        self.is_open = False


fake = FakeSerial()

connection = SerialConnection(
    connection=fake,
)

assert connection.connect()
assert connection.connected

print(
    "Port:",
    connection.port,
)

print(
    "Produkt:",
    connection.query(":GVP#"),
)

print(
    "Firmware:",
    connection.query(":GVN#"),
)

print(
    "RA:",
    connection.query(":GR#"),
)

print(
    "DEC:",
    connection.query(":GD#"),
)

connection.send(":Q#")

print()
print("Sendte kommandoer:")

for command in fake.commands:
    print(command)

connection.close()

assert not connection.connected

print()
print(
    "SerialConnection-test bestået."
)
