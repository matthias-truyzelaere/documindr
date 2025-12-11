"""Custom logging configuration with colored output."""

import logging
import sys

RESET = "\033[0m"
WHITE = "\033[37m"
BG = "\033[48;2;48;111;102m"


class CustomFormatter(logging.Formatter):
    """Custom log formatter with colored level badges."""

    fmt = "%(level_badge)s %(message)s"

    LEVEL_BADGES = {
        logging.DEBUG: f"\t{BG}{WHITE} DEBUG {RESET}",
        logging.INFO: f"\t{BG}{WHITE} INFO {RESET}",
        logging.WARNING: f"\t{BG}{WHITE} WARNING {RESET}",
        logging.ERROR: f"\t{BG}{WHITE} ERROR {RESET}",
        logging.CRITICAL: f"\t{BG}{WHITE} CRITICAL {RESET}",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colored badge."""
        record.level_badge = self.LEVEL_BADGES.get(
            record.levelno,
            f"[{record.levelname}]",
        )
        return logging.Formatter(self.fmt).format(record)


def setup_logger() -> None:
    """Initialize root logger with custom formatter and reduced uvicorn noise."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter())

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)

    # Reduce uvicorn log noise
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.ERROR)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance for the specified module name."""
    return logging.getLogger(name)
