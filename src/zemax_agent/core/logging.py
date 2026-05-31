from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional


_initialized: bool = False
_root_logger: Optional[logging.Logger] = None


def setup_logging(
    level: str = "INFO",
    log_file: str = "./logs/zemax_agent.log",
    fmt: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt: str = "%Y-%m-%d %H:%M:%S",
) -> logging.Logger:
    global _initialized, _root_logger

    if _initialized:
        return _root_logger  # type: ignore[return-value]

    logger = logging.getLogger("zemax_agent")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _root_logger = logger
    _initialized = True

    logger.info("Logging initialized (level=%s, file=%s)", level, log_file)
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    qualname = "zemax_agent"
    if name:
        qualname = f"{qualname}.{name}"
    return logging.getLogger(qualname)
