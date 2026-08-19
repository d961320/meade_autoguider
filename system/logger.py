import logging
from pathlib import Path


def get_logger(name="autoguider"):
    log_dir = Path.home() / "meade_autoguider" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-7s %(message)s"
    )

    file_handler = logging.FileHandler(
        log_dir / "autoguider.log",
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
