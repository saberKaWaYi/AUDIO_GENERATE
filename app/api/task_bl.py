import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.api.task_req import CreateTaskRequest
from app.api.task_res import (
    CreateTaskResponse,
    ReleaseTaskResponse,
    TaskQueryResponse,
    TaskSubtaskResponse,
    UpdateTextResponse,
)
from models.schemas_task import (
    ASMRGenerateAudioResult,
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


def query_task(mongo, task_id: str, user_id: int) -> TaskQueryResponse | None:
    query = {"task_id": task_id, "user_id": user_id, "is_deleted": False}
    docs = mongo.find_documents(
        AUDIO_TASKS_COLLECTION,
        query,
        sort=[("create_time", 1)],
        fields=(
            "subtask_id",
            "type",
            "info",
            "status",
            "result",
            "create_time",
            "update_time",
            "is_public",
        ),
    )
    if not docs:
        return None

    subtasks = [
        TaskSubtaskResponse(
            subtask_id=doc["subtask_id"],
            type=doc["type"],
            info=doc["info"],
            status=doc["status"],
            result=doc["result"],
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


def get_task_audio(mongo, user_id: int, subtask_id: str) -> tuple[str, bytes] | None:
    doc = mongo.find_one(
        AUDIO_TASKS_COLLECTION,
        {
            "subtask_id": subtask_id,
            "user_id": user_id,
            "type": TaskType.ASMR_TEXT_GENERATE.value,
            "status": TaskStatus.SUCCESS.value,
            "is_deleted": False,
        },
        fields=("result.result_text",),
    )
    if doc is None:
        return None
    payload = ASMRGenerateAudioResult.model_validate_json(doc["result"]["result_text"])
    file_path = Path(worker_settings.audio_data_dir) / payload.relative_path
    return file_path.name, file_path.read_bytes()


def list_tasks(mongo, user_id: int) -> list[dict]:
    return mongo.find_documents(
        AUDIO_TASKS_COLLECTION,
        {"user_id": user_id, "type": TaskType.ASMR_TEXT.value, "is_deleted": False},
        sort=[("create_time", -1)],
        fields=("task_id", "info.title", "status", "is_public", "create_time"),
    )


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


def refresh_task(mongo, user_id: int, subtask_id: str) -> ReleaseTaskResponse | None:
    query = {"subtask_id": subtask_id, "user_id": user_id, "is_deleted": False}
    doc = mongo.find_one(AUDIO_TASKS_COLLECTION, query, fields=("status", "type", "task_id"))
    if doc is None:
        return None
    status = TaskStatus(doc["status"])
    if status not in (TaskStatus.SUCCESS, TaskStatus.FAILED):
        raise ValueError(f"子任务状态不支持刷新：{status.value}")

    if TaskType(doc["type"]) == TaskType.ASMR_TEXT:
        generated_query = {
            "task_id": doc["task_id"],
            "type": TaskType.ASMR_TEXT_GENERATE.value,
            "is_deleted": False,
        }
        generated = mongo.find_documents(
            AUDIO_TASKS_COLLECTION,
            generated_query,
            fields=("status",),
        )
        if any(TaskStatus(item["status"]) == TaskStatus.SUCCESS for item in generated):
            raise ValueError("已有生成子任务成功，不能刷新对白任务")
        if generated:
            mongo.delete_documents(AUDIO_TASKS_COLLECTION, generated_query)

    modified = mongo.update_document(
        AUDIO_TASKS_COLLECTION,
        query,
        {"$set": {"status": TaskStatus.PENDING.value, "update_time": datetime.utcnow()}},
    )
    if modified != 1:
        raise RuntimeError("刷新子任务时更新数量异常")
    return ReleaseTaskResponse(subtask_id=subtask_id, status=TaskStatus.PENDING)


def update_subtask_text(mongo, user_id: int, subtask_id: str, text: str) -> UpdateTextResponse | None:
    if not text.strip():
        raise ValueError("修改文本不能为空")

    query = {
        "subtask_id": subtask_id,
        "user_id": user_id,
        "type": TaskType.ASMR_TEXT_GENERATE.value,
        "is_deleted": False,
    }
    doc = mongo.find_one(AUDIO_TASKS_COLLECTION, query, fields=("status", "task_id", "info"))
    if doc is None:
        return None
    if TaskStatus(doc["status"]) != TaskStatus.DEBUG:
        raise ValueError(f"只有 debug 状态的生成子任务能修改文本：{doc['status']}")

    info = doc["info"]
    parent_query = {
        "task_id": doc["task_id"],
        "user_id": user_id,
        "type": TaskType.ASMR_TEXT.value,
        "is_deleted": False,
    }
    parent = mongo.find_one(AUDIO_TASKS_COLLECTION, parent_query, fields=("result.result_text",))
    if parent is None:
        raise ValueError("找不到 ASMR_TEXT 主任务")
    segments = json.loads(parent["result"]["result_text"])
    target = None
    for segment in segments:
        if (
            segment["index"] == info["index"]
            and segment["reference_id"] == info["reference_id"]
        ):
            target = segment
            break
    if target is None:
        raise ValueError("主任务中找不到对应的片段")
    target["text"] = text
    updated_result_text = json.dumps(segments, ensure_ascii=False)

    mongo.update_document(
        AUDIO_TASKS_COLLECTION,
        parent_query,
        {"$set": {"result.result_text": updated_result_text, "update_time": datetime.utcnow()}},
    )
    mongo.update_document(
        AUDIO_TASKS_COLLECTION,
        query,
        {"$set": {"info.text": text, "status": TaskStatus.DEBUG.value, "update_time": datetime.utcnow()}},
    )
    return UpdateTextResponse(subtask_id=subtask_id, status=TaskStatus.DEBUG)


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


def set_task_public(mongo, user_id: int, task_id: str, is_public: bool) -> bool:
    return mongo.update_documents(
        AUDIO_TASKS_COLLECTION,
        {"task_id": task_id, "user_id": user_id, "is_deleted": False},
        {"$set": {"is_public": is_public, "update_time": datetime.utcnow()}},
    ) > 0


def delete_task(mongo, user_id: int, task_id: str) -> bool:
    return mongo.update_documents(
        AUDIO_TASKS_COLLECTION,
        {"task_id": task_id, "user_id": user_id, "is_deleted": False},
        {"$set": {"is_deleted": True, "update_time": datetime.utcnow()}},
    ) > 0
