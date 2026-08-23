#!/usr/bin/env python3

from mount.lx200 import LX200Mount


class FakeSerial:
    """Minimal seriel simulator til driver-test."""

    def __init__(self):
        self.is_open = True
        self.port = "FAKE-LX200"
        self.commands = []
        self.reply = bytearray()

        self.responses = {
            ":GVP#": b"LX200 Simulator#",
            ":GVN#": b"0.1#",
            ":GR#": b"12:34:56#",
            ":GD#": b"+45\xdf12:34#",
        }

    def reset_input_buffer(self):
        pass

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


fake_serial = FakeSerial()

mount = LX200Mount(
    serial_connection=fake_serial,
)

assert mount.connect()
assert mount.connected

print("Driver:", mount.DRIVER_NAME)
print("Produkt:", mount.product)
print("Firmware:", mount.firmware)
print("RA:", mount.get_ra())
print("DEC:", mount.get_dec())

mount.set_speed("FIND")
mount.start_move("e")
mount.stop()

print()
print("Sendte kommandoer:")

for command in fake_serial.commands:
    print(command)

mount.disconnect()

print()
print("LX200-simulatortest bestået.")
