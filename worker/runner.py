import signal
import time
from datetime import datetime
from typing import Optional
from uuid import uuid4

from agents.music import MusicOutcome
from models.schemas_task import (
    ASMRBackendSubMusicInfo,
    ASMRBackendSubMusicResult,
    AUDIO_TASKS_COLLECTION,
    AudioTask,
    TaskStatus,
    TaskType,
)
from services.elevenlabs_service import ElevenLabsService
from services.mongo_service import MongoService
from settings.elevenlabs import elevenlabs_settings
from settings.mongo import mongo_settings
from settings.worker import worker_settings
from worker.executors import EXECUTORS, SUBMUSIC_SUCCESS

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


def _write_music_success(subtask: dict, outcome: MusicOutcome) -> None:
    mongo_service.update_document(
        AUDIO_TASKS_COLLECTION,
        {"subtask_id": subtask["subtask_id"], "is_deleted": False},
        {
            "$set": {
                "status": TaskStatus.SUCCESS.value,
                "result.prompt_tokens": outcome.llm_result.prompt_tokens,
                "result.completion_tokens": outcome.llm_result.completion_tokens,
                "update_time": _now(),
            }
        },
    )


def _insert_submusic_tasks(subtask: dict, outcome: MusicOutcome) -> None:
    now = _now()
    for track in outcome.tracks:
        task = AudioTask(
            task_id=subtask["task_id"],
            subtask_id=uuid4().hex,
            user_id=subtask["user_id"],
            type=TaskType.ASMR_BACKEND_SUBMUSIC,
            info=ASMRBackendSubMusicInfo(
                prompt=track.prompt,
                duration_seconds=track.duration_seconds,
            ),
            status=TaskStatus.PENDING,
            result=ASMRBackendSubMusicResult(result_text=""),
            create_time=now,
            update_time=now,
            is_deleted=False,
        )
        mongo_service.insert_document(AUDIO_TASKS_COLLECTION, task.model_dump(mode="json"))
        logger.info("插入 SUBMUSIC 任务, subtask_id=%s", task.subtask_id)


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
        executor = EXECUTORS.get(task_type)
        if executor is None:
            raise ValueError(f"任务类型 {task_type.value!r} 没有注册执行器")

        outcome = executor(subtask)
        if task_type == TaskType.ASMR_BACKEND_MUSIC:
            if not isinstance(outcome, MusicOutcome):
                raise ValueError(f"MUSIC 执行器返回类型错误：{type(outcome).__name__}")
            _insert_submusic_tasks(subtask, outcome)
            _write_music_success(subtask, outcome)
            logger.info(
                "MUSIC 规划成功, subtask_id=%s, tracks=%d",
                subtask["subtask_id"],
                len(outcome.tracks),
            )
        elif task_type == TaskType.ASMR_BACKEND_SUBMUSIC:
            if outcome != SUBMUSIC_SUCCESS:
                raise ValueError(f"SUBMUSIC 执行器返回了非预期结果：{outcome!r}")
            _write_success(subtask, outcome)
            logger.info("SUBMUSIC 生成成功, subtask_id=%s", subtask["subtask_id"])
        else:
            raise ValueError(f"任务类型 {task_type.value!r} 没有闭合结果处理")
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
