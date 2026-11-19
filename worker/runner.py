import signal
import time

import logging

from services.mongo_service import MongoService
from settings.mongo import mongo_settings
from settings.worker import worker_settings
from logging_config import setup_logging

setup_logging("worker")
logger = logging.getLogger(__name__)

mongo_service: MongoService = None

_stopping = False


def _connect() -> None:
    global mongo_service

    mongo_service = MongoService(
        host=mongo_settings.mongodb_host,
        port=mongo_settings.mongodb_port,
        username=mongo_settings.mongodb_username,
        password=mongo_settings.mongodb_password,
        database=mongo_settings.mongodb_database,
    )
    mongo_service.connect()


def _handle_stop(signum, frame) -> None:
    global _stopping
    if _stopping:
        return
    _stopping = True
    logger.info("收到退出信号 %s，准备退出", signum)


def _install_signal_handlers() -> None:
    for signal_name in ("SIGINT", "SIGTERM", "SIGBREAK"):
        signal_value = getattr(signal, signal_name, None)
        if signal_value is None:
            continue
        try:
            signal.signal(signal_value, _handle_stop)
        except (ValueError, OSError):
            logger.debug("无法注册 %s 的信号处理器", signal_name)


def _close() -> None:
    if mongo_service is not None:
        mongo_service.close()


def run_worker() -> None:
    _connect()
    _install_signal_handlers()
    logger.info("worker骨架已启动, poll_interval=%ss", worker_settings.worker_poll_interval)

    try:
        while not _stopping:
            time.sleep(worker_settings.worker_poll_interval)
    finally:
        _close()
        logger.info("worker已退出")


if __name__ == "__main__":
    run_worker()
