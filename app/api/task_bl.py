from datetime import datetime
from uuid import uuid4

from app.api.task_req import CreateTaskRequest
from app.api.task_res import (
    CreateTaskResponse,
    ReleaseTaskResponse,
    TaskListResponse,
    TaskListItem,
    TaskQueryResponse,
    TaskSubtaskResponse,
)
from models.schemas_task import (
    AUDIO_TASKS_COLLECTION,
    ASMRBackendMusicInfo,
    ASMRBackendMusicResult,
    ASMRTextInfo,
    ASMRTextResult,
    AudioTask,
    TaskInfo,
    TaskResult,
    TaskStatus,
    TaskType,
)
from settings_config import settings


def _new_info(request: CreateTaskRequest, task_type: TaskType) -> TaskInfo:
    if task_type == TaskType.ASMR_TEXT:
        return ASMRTextInfo(
            title=request.title,
            reference_ids=request.reference_ids,
            theme=request.theme,
            duration_minutes=request.duration_minutes,
            language=request.language,
        )
    if task_type == TaskType.ASMR_BACKEND_MUSIC:
        return ASMRBackendMusicInfo(
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
    if task_type == TaskType.ASMR_BACKEND_MUSIC:
        return ASMRBackendMusicResult(result_text="", prompt_tokens=0, completion_tokens=0)
    raise ValueError(f"不支持的任务类型：{task_type}")


def _new_task(
    task_id: str, request: CreateTaskRequest, task_type: TaskType, now: datetime
) -> AudioTask:
    return AudioTask(
        task_id=task_id,
        subtask_id=uuid4().hex,
        user_id=request.user_id,
        type=task_type,
        info=_new_info(request, task_type),
        status=TaskStatus.DEBUG if settings.debug else TaskStatus.PENDING,
        result=_new_result(task_type),
        create_time=now,
        update_time=now,
        is_deleted=False,
    )


def create_task(mongo, request: CreateTaskRequest) -> CreateTaskResponse:
    if not request.title.strip():
        raise ValueError("作品标题不能为空")
    if not request.theme.strip():
        raise ValueError("创作主题不能为空")

    now = datetime.utcnow()
    task_id = uuid4().hex
    task = _new_task(task_id, request, request.type, now)
    mongo.insert_document(AUDIO_TASKS_COLLECTION, task.model_dump(mode="json"))

    if request.background_music:
        music_task = _new_task(task_id, request, TaskType.ASMR_BACKEND_MUSIC, now)
        mongo.insert_document(AUDIO_TASKS_COLLECTION, music_task.model_dump(mode="json"))

    return CreateTaskResponse(task_id=task_id, status=task.status)


def release_task(mongo, subtask_id: str) -> ReleaseTaskResponse | None:
    query = {"subtask_id": subtask_id, "is_deleted": False}
    doc = mongo.find_one(AUDIO_TASKS_COLLECTION, query)
    if doc is None:
        return None
    if TaskStatus(doc["status"]) != TaskStatus.DEBUG:
        raise ValueError(f"任务不处于 debug 状态，无法放行：{doc['status']}")

    modified = mongo.update_document(
        AUDIO_TASKS_COLLECTION,
        query,
        {
            "$set": {
                "status": TaskStatus.PENDING.value,
                "update_time": datetime.utcnow(),
            }
        },
    )
    if modified != 1:
        raise RuntimeError("放行任务时更新数量异常")
    return ReleaseTaskResponse(subtask_id=subtask_id, status=TaskStatus.PENDING)


def _build_task_response(task_id: str, docs: list[dict]) -> TaskQueryResponse:
    subtasks = [
        TaskSubtaskResponse(
            subtask_id=doc["subtask_id"],
            type=doc["type"],
            info=doc["info"],
            status=doc["status"],
            result=doc["result"],
            create_time=doc["create_time"],
            update_time=doc["update_time"],
        )
        for doc in docs
    ]
    return TaskQueryResponse(
        task_id=task_id,
        user_id=docs[0]["user_id"],
        status=docs[0]["status"],
        subtasks=subtasks,
        create_time=docs[0]["create_time"],
        update_time=docs[0]["update_time"],
    )


def query_task(mongo, task_id: str, user_id: int) -> TaskQueryResponse | None:
    query = {"task_id": task_id, "user_id": user_id, "is_deleted": False}
    docs = mongo.find_documents(AUDIO_TASKS_COLLECTION, query, sort=[("create_time", 1)])
    if not docs:
        return None
    return _build_task_response(task_id, docs)


def query_task_detail(mongo, task_id: str) -> TaskQueryResponse | None:
    query = {"task_id": task_id, "is_deleted": False}
    docs = mongo.find_documents(AUDIO_TASKS_COLLECTION, query, sort=[("create_time", 1)])
    if not docs:
        return None
    return _build_task_response(task_id, docs)


def list_tasks(mongo) -> TaskListResponse:
    docs = mongo.find_documents(AUDIO_TASKS_COLLECTION, {"is_deleted": False})
    groups: dict[str, list[dict]] = {}
    for doc in docs:
        groups.setdefault(doc["task_id"], []).append(doc)

    items = [
        TaskListItem(
            task_id=task_id,
            user_id=subtasks[0]["user_id"],
            status=TaskStatus(subtasks[0]["status"]),
            subtask_count=len(subtasks),
            create_time=subtasks[0]["create_time"],
            update_time=subtasks[0]["update_time"],
        )
        for task_id, subtasks in groups.items()
    ]
    items.sort(key=lambda item: item.create_time, reverse=True)
    return TaskListResponse(items=items, total=len(items))
