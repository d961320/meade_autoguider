#!/usr/bin/env python3

from mount.autostar_v2 import AutoStarV2
from mount.serial_connection import SerialConnection


class FakeSerial:
    def __init__(self):
        self.is_open = True
        self.port = "FAKE-AUTOSTAR"
        self.commands = []
        self.reply = bytearray()

        self.responses = {
            ":GVP#": b"Autostar#",
            ":GVN#": b"43Ea#",
            ":GR#": b"04:56:44#",
            ":GD#": b"+88\xdf34:32#",
        }

    def reset_input_buffer(self):
        self.reply.clear()

    def write(self, data):
        command = data.decode("ascii")

        self.commands.append(command)

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

serial_connection = SerialConnection(
    connection=fake,
)

mount = AutoStarV2(
    connection=serial_connection,
)

assert mount.connect()
assert mount.connected

print("Driver:", mount.DRIVER_NAME)
print("Version:", mount.DRIVER_VERSION)
print("Port:", mount.port)
print("Produkt:", mount.product)
print("Firmware:", mount.firmware)
print("RA:", mount.get_ra())
print("DEC:", mount.get_dec())

mount.set_speed("FIND")
mount.start_move("e")
mount.stop()

print()
print("Status:")
print(mount.status())

print()
print("Sendte kommandoer:")

for command in fake.commands:
    print(command)

mount.disconnect()

assert not mount.connected

print()
print("AutoStar V2-test bestået.")
