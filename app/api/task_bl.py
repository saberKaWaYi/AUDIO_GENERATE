from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.api.task_req import CreateTaskRequest
from app.api.task_res import CreateTaskResponse, ReleaseTaskResponse, TaskQueryResponse, TaskSubtaskResponse
from models.schemas_character import AUDIO_CHARACTERS_COLLECTION
from models.schemas_task import (
    ASMRTextInfo,
    ASMRTextResult,
    AUDIO_TASKS_COLLECTION,
    AudioTask,
    TaskInfo,
    TaskResult,
    TaskStatus,
    TaskType,
)
from settings.worker import worker_settings


def _new_info(request: CreateTaskRequest, task_type: TaskType) -> TaskInfo:
    if task_type == TaskType.ASMR_TEXT:
        return ASMRTextInfo(
            title=request.title,
            reference_ids=request.reference_ids,
            theme=request.theme,
            duration_minutes=request.duration_minutes,
            language=request.language,
        )
    raise ValueError(f"不支持的任务类型：{task_type}")


def _new_result(task_type: TaskType) -> TaskResult:
    if task_type == TaskType.ASMR_TEXT:
        return ASMRTextResult(result_text="", prompt_tokens=0, completion_tokens=0)
    raise ValueError(f"不支持的任务类型：{task_type}")


def _new_task(
    task_id: str, user_id: int, request: CreateTaskRequest, task_type: TaskType, now: datetime
) -> AudioTask:
    return AudioTask(
        task_id=task_id,
        subtask_id=uuid4().hex,
        user_id=user_id,
        type=task_type,
        info=_new_info(request, task_type),
        status=TaskStatus.DEBUG,
        result=_new_result(task_type),
        create_time=now,
        update_time=now,
        is_deleted=False,
    )


def list_tasks(mongo, user_id: int) -> list[dict]:
    return mongo.find_documents(
        AUDIO_TASKS_COLLECTION,
        {"user_id": user_id, "type": TaskType.ASMR_TEXT.value, "is_deleted": False},
        sort=[("create_time", -1)],
        fields=("task_id", "info.title", "type", "status", "is_public", "create_time"),
    )


def set_task_public(mongo, user_id: int, task_id: str, is_public: bool) -> bool:
    return mongo.update_documents(
        AUDIO_TASKS_COLLECTION,
        {"task_id": task_id, "user_id": user_id, "is_deleted": False},
        {"$set": {"is_public": is_public, "update_time": datetime.utcnow()}},
    ) > 0


def release_task(mongo, user_id: int, subtask_id: str) -> ReleaseTaskResponse | None:
    query = {"subtask_id": subtask_id, "user_id": user_id, "is_deleted": False}
    doc = mongo.find_one(AUDIO_TASKS_COLLECTION, query, fields=("status",))
    if doc is None:
        return None
    if TaskStatus(doc["status"]) != TaskStatus.DEBUG:
        raise ValueError(f"子任务不处于 debug 状态，无法放行：{doc['status']}")

    modified = mongo.update_document(
        AUDIO_TASKS_COLLECTION,
        query,
        {"$set": {"status": TaskStatus.PENDING.value, "update_time": datetime.utcnow()}},
    )
    if modified != 1:
        raise RuntimeError("放行子任务时更新数量异常")
    return ReleaseTaskResponse(subtask_id=subtask_id, status=TaskStatus.PENDING)


def delete_task(mongo, user_id: int, task_id: str) -> bool:
    return mongo.update_documents(
        AUDIO_TASKS_COLLECTION,
        {"task_id": task_id, "user_id": user_id, "is_deleted": False},
        {"$set": {"is_deleted": True, "update_time": datetime.utcnow()}},
    ) > 0


def create_task(mongo, user_id: int, request: CreateTaskRequest) -> CreateTaskResponse:
    if not request.title.strip():
        raise ValueError("作品标题不能为空")
    if not request.theme.strip():
        raise ValueError("创作主题不能为空")

    now = datetime.utcnow()
    task_id = uuid4().hex
    task = _new_task(task_id, user_id, request, request.type, now)
    mongo.insert_document(AUDIO_TASKS_COLLECTION, task.model_dump(mode="json"))

    return CreateTaskResponse(task_id=task_id, status=task.status)


def _load_cover_images(mongo, user_id: int, docs: list[dict]) -> dict[str, str | None]:
    covers: dict[str, str | None] = {doc["subtask_id"]: None for doc in docs}
    reference_ids = [
        doc["info"]["reference_id"]
        for doc in docs
        if doc["type"] == TaskType.ASMR_TEXT_GENERATE.value
    ]
    if not reference_ids:
        return covers
    characters = mongo.find_documents(
        AUDIO_CHARACTERS_COLLECTION,
        {
            "user_id": user_id,
            "reference_id": {"$in": reference_ids},
            "is_deleted": False,
        },
        fields=("reference_id", "cover_image"),
    )
    cover_by_reference = {char["reference_id"]: char["cover_image"] for char in characters}
    for doc in docs:
        if doc["type"] != TaskType.ASMR_TEXT_GENERATE.value:
            continue
        reference_id = doc["info"]["reference_id"]
        if reference_id in cover_by_reference:
            covers[doc["subtask_id"]] = cover_by_reference[reference_id]
    return covers


def query_task(mongo, task_id: str, user_id: int) -> TaskQueryResponse | None:
    query = {"task_id": task_id, "user_id": user_id, "is_deleted": False}
    docs = mongo.find_documents(AUDIO_TASKS_COLLECTION, query, sort=[("create_time", 1)])
    if not docs:
        return None

    covers = _load_cover_images(mongo, user_id, docs)
    subtasks = [
        TaskSubtaskResponse(
            subtask_id=doc["subtask_id"],
            type=doc["type"],
            info=doc["info"],
            status=doc["status"],
            result=doc["result"],
            cover_image=covers[doc["subtask_id"]],
            create_time=doc["create_time"],
            update_time=doc["update_time"],
            is_public=doc["is_public"],
        )
        for doc in docs
    ]
    return TaskQueryResponse(
        task_id=task_id,
        user_id=user_id,
        status=docs[0]["status"],
        subtasks=subtasks,
        create_time=docs[0]["create_time"],
        update_time=docs[0]["update_time"],
        is_public=docs[0]["is_public"],
    )


def release_tasks_batch(mongo, user_id: int, task_id: str, task_type: TaskType) -> int:
    return mongo.update_documents(
        AUDIO_TASKS_COLLECTION,
        {
            "task_id": task_id,
            "user_id": user_id,
            "type": task_type.value,
            "status": TaskStatus.DEBUG.value,
            "is_deleted": False,
        },
        {"$set": {"status": TaskStatus.PENDING.value, "update_time": datetime.utcnow()}},
    )


def get_task_audio(mongo, user_id: int, subtask_id: str) -> tuple[str, bytes] | None:
    doc = mongo.find_one(
        AUDIO_TASKS_COLLECTION,
        {
            "subtask_id": subtask_id,
            "user_id": user_id,
            "status": TaskStatus.SUCCESS.value,
            "is_deleted": False,
        },
        fields=("result.result_text",),
    )
    if doc is None:
        return None
    relative_path = doc["result"]["result_text"]
    file_path = Path(worker_settings.audio_data_dir) / relative_path
    return file_path.name, file_path.read_bytes()
