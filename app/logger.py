import logging
import logging.handlers
import sys

COLORS = {
    logging.DEBUG: "\033[37m",  # серый
    logging.INFO: "\033[36m",  # голубой
    logging.WARNING: "\033[33m",  # жёлтый
    logging.ERROR: "\033[31m",  # красный
    logging.CRITICAL: "\033[41m",  # красный фон
}
RESET = "\033[0m"


class ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color = COLORS.get(record.levelno, RESET)
        record.levelname = f"{color}{record.levelname}{RESET}"
        record.name = f"{color}{record.name}{RESET}"
        return super().format(record)


def init_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    formatter = ColorFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()
    root.addHandler(handler)


def create_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
