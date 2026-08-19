import time


class Menu:
    START_Y = 48
    ROW_HEIGHT = 38
    ROW_VISIBLE_HEIGHT = 32

    def __init__(self, display, touch, keyboard=None):
        self.display = display
        self.touch = touch
        self.keyboard = keyboard

    def run(self, items, selected=0, allow_back=True):
        while True:
            display_items = [
                (
                    item["label"],
                    item.get("value", ""),
                    item.get("enabled", True),
                )
                for item in items
            ]

            self.display.main_menu(display_items, selected)

            key = self.keyboard.read() if self.keyboard else None

            if key in {"n", "down"}:
                selected = (selected + 1) % len(items)

            elif key in {"p", "up"}:
                selected = (selected - 1) % len(items)

            elif key in {"v", "\r", "\n"}:
                if items[selected].get("enabled", True):
                    return items[selected]["action"]

            elif allow_back and key in {"q", "\x1b"}:
                return None

            touch = self.touch.read_release()

            if touch is not None:
                x, y = touch

                if 18 <= x <= 462 and y >= self.START_Y:
                    index = int(
                        (y - self.START_Y) // self.ROW_HEIGHT
                    )

                    if (
                        0 <= index < len(items)
                        and self.START_Y + index * self.ROW_HEIGHT
                        <= y
                        <= self.START_Y
                        + index * self.ROW_HEIGHT
                        + self.ROW_VISIBLE_HEIGHT
                        and items[index].get("enabled", True)
                    ):
                        return items[index]["action"]

            time.sleep(0.02)
