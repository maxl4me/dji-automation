"""Structured logging for the framework.

Uses Python's stdlib `logging` for terminal output. Allure steps are added
at the page-object layer via the @allure.step decorator (not here).

Log format is deliberately simple — timestamp, level, logger name, message.
Avoids JSON logging which is overkill for a solo project and harder to read locally.
"""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False
_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%H:%M:%S"


def _configure_once(level: int = logging.INFO) -> None:
    """Idempotent root logger setup. Called on first get_logger() invocation."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT))

    root = logging.getLogger()
    root.handlers.clear()  # remove any pre-existing handlers (pytest can inject)
    root.addHandler(handler)
    root.setLevel(level)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-specific logger. Call with `__name__` from the calling module."""
    _configure_once()
    return logging.getLogger(name)
