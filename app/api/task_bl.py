from datetime import datetime
from uuid import uuid4

from app.api.task_req import CreateTaskRequest
from app.api.task_res import CreateTaskResponse, TaskQueryResponse, TaskSubtaskResponse
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
    task_id: str, request: CreateTaskRequest, task_type: TaskType, now: datetime
) -> AudioTask:
    return AudioTask(
        task_id=task_id,
        subtask_id=uuid4().hex,
        user_id=request.user_id,
        type=task_type,
        info=_new_info(request, task_type),
        status=TaskStatus.DEBUG,
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

    return CreateTaskResponse(task_id=task_id, status=task.status)


def query_task(mongo, task_id: str, user_id: int) -> TaskQueryResponse | None:
    query = {"task_id": task_id, "user_id": user_id, "is_deleted": False}
    docs = mongo.find_documents(AUDIO_TASKS_COLLECTION, query, sort=[("create_time", 1)])
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
    )
