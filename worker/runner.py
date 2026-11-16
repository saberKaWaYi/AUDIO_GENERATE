import signal
import time
from datetime import datetime
from typing import Optional

from models.schemas_task import AUDIO_TASKS_COLLECTION, TaskStatus, TaskType
from services.elevenlabs_service import ElevenLabsService
from services.mongo_service import MongoService
from settings.elevenlabs import elevenlabs_settings
from settings.mongo import mongo_settings
from settings.worker import worker_settings
from worker.executors import EXECUTORS

import logging
from logging_config import setup_logging

setup_logging("worker")
logger = logging.getLogger(__name__)

mongo_service: MongoService = None
elevenlabs_service: ElevenLabsService = None

_stopping = False


def _connect() -> None:
    global mongo_service, elevenlabs_service

    mongo_service = MongoService(
        host=mongo_settings.mongodb_host,
        port=mongo_settings.mongodb_port,
        username=mongo_settings.mongodb_username,
        password=mongo_settings.mongodb_password,
        database=mongo_settings.mongodb_database,
    )
    mongo_service.connect()

    api_keys = [key.strip() for key in elevenlabs_settings.elevenlabs_api_keys.split(",") if key.strip()]
    elevenlabs_service = ElevenLabsService(api_keys)


def _handle_stop(signum, frame) -> None:
    global _stopping
    if _stopping:
        return
    _stopping = True
    logger.info("收到退出信号 %s，当前任务结束后退出", signum)


def _install_signal_handlers() -> None:
    for signal_name in ("SIGINT", "SIGTERM", "SIGBREAK"):
        signal_value = getattr(signal, signal_name, None)
        if signal_value is None:
            continue
        try:
            signal.signal(signal_value, _handle_stop)
        except (ValueError, OSError):
            logger.debug("无法注册 %s 的信号处理器", signal_name)


def _now() -> datetime:
    return datetime.utcnow()


def _claim_task() -> Optional[dict]:
    now = _now()
    return mongo_service.find_one_and_update(
        AUDIO_TASKS_COLLECTION,
        {
            "status": TaskStatus.PENDING.value,
            "is_deleted": False,
            "type": {"$in": [task_type.value for task_type in EXECUTORS]},
        },
        {
            "$set": {
                "status": TaskStatus.PROCESSING.value,
                "update_time": now,
            }
        },
        sort=[("create_time", 1)],
    )


def _write_success(subtask: dict, result_text: str) -> None:
    mongo_service.update_document(
        AUDIO_TASKS_COLLECTION,
        {"subtask_id": subtask["subtask_id"], "is_deleted": False},
        {
            "$set": {
                "status": TaskStatus.SUCCESS.value,
                "result.result_text": result_text,
                "update_time": _now(),
            }
        },
    )


def _write_failed(subtask: dict, reason: str) -> None:
    mongo_service.update_document(
        AUDIO_TASKS_COLLECTION,
        {"subtask_id": subtask["subtask_id"], "is_deleted": False},
        {
            "$set": {
                "status": TaskStatus.FAILED.value,
                "result.result_text": reason,
                "update_time": _now(),
            }
        },
    )


def _run_once() -> bool:
    subtask = _claim_task()
    if subtask is None:
        return False

    logger.info(
        "领取任务, subtask_id=%s, task_id=%s, type=%s",
        subtask["subtask_id"],
        subtask["task_id"],
        subtask["type"],
    )

    try:
        task_type = TaskType(subtask["type"])
        executor = EXECUTORS[task_type]
        if task_type == TaskType.ASMR_BACKEND_MUSIC:
            pass
        else:
            raise ValueError(f"任务类型 {task_type.value!r} 没有注册执行器")
        _write_success(subtask, result_text)
        logger.info("任务处理成功, subtask_id=%s, result=%s", subtask["subtask_id"], result_text)
    except Exception as exc:
        logger.exception("任务处理失败, subtask_id=%s", subtask["subtask_id"])
        _write_failed(subtask, str(exc))

    return True


def _close() -> None:
    if mongo_service is not None:
        mongo_service.close()


def run_worker() -> None:
    _connect()
    _install_signal_handlers()
    logger.info("worker 启动, poll_interval=%ss", worker_settings.worker_poll_interval)

    try:
        while not _stopping:
            if not _run_once():
                time.sleep(worker_settings.worker_poll_interval)
    finally:
        _close()
        logger.info("worker 已退出")


if __name__ == "__main__":
    run_worker()
