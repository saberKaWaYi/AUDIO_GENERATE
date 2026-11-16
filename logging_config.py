import logging
import logging.config

from pathlib import Path

from settings.common import LogServiceName
from settings_config import settings

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

WEB_LOG = LOG_DIR / "web.log"


def _standard_formatters() -> dict:
    return {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    }


def _console_handler() -> dict:
    return {
        "class": "logging.StreamHandler",
        "formatter": "standard",
        "level": "DEBUG",
    }


def _logging_dict_web(debug: bool) -> dict:
    level = "DEBUG" if debug else "INFO"
    handlers = ["web_file", "console"]
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": _standard_formatters(),
        "handlers": {
            "web_file": {
                "class": "logging.FileHandler",
                "filename": str(WEB_LOG),
                "formatter": "standard",
                "level": level,
                "encoding": "utf-8",
            },
            "console": _console_handler(),
        },
        "loggers": {
            "app": {"handlers": handlers, "level": level, "propagate": False},
            "services": {"handlers": handlers, "level": level, "propagate": False},
            "uvicorn": {"handlers": handlers, "level": level, "propagate": False},
            "uvicorn.error": {"handlers": handlers, "level": level, "propagate": False},
            "uvicorn.access": {"handlers": handlers, "level": level, "propagate": False},
            "fastapi": {"handlers": handlers, "level": level, "propagate": False},
        },
    }


def setup_logging(service: LogServiceName, *, debug: bool | None = None) -> None:
    if service != "web":
        raise ValueError(f"Unknown log service: {service!r}")
    effective_debug = settings.get_service_debug(service) if debug is None else debug
    logging.config.dictConfig(_logging_dict_web(effective_debug))
