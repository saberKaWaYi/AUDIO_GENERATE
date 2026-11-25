from datetime import datetime
from uuid import uuid4

from app.api.task_req import CreateTaskRequest
from app.api.task_res import CreateTaskResponse, ReleaseTaskResponse, TaskQueryResponse, TaskSubtaskResponse
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
