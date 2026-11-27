import json
from datetime import datetime
from uuid import NAMESPACE_URL, uuid5

from models.schemas_task import (
    ASMRTextGenerateInfo,
    ASMRTextGenerateResult,
    ASMRTimePlanInfo,
    ASMRTimePlanResult,
    AUDIO_TASKS_COLLECTION,
    AudioTask,
    TaskStatus,
    TaskType,
)

_NAMESPACE = uuid5(NAMESPACE_URL, "audio_generate_task")


def _now() -> datetime:
    return datetime.utcnow()


def _generate_subtask_id(task_id: str, parent_subtask_id: str, index: int) -> str:
    return uuid5(_NAMESPACE, f"{task_id}:{parent_subtask_id}:generate:{index}").hex


def _time_plan_subtask_id(task_id: str) -> str:
    return uuid5(_NAMESPACE, f"{task_id}:time_plan").hex


def dispatch_generate_tasks(mongo, parent: dict, result_text: str) -> int:
    dialogue = json.loads(result_text)

    now = _now()
    tasks: list[AudioTask] = []
    for item in dialogue:
        info = ASMRTextGenerateInfo(
            index=item["index"],
            reference_id=item["reference_id"],
            text=item["text"],
        )
        tasks.append(
            AudioTask(
                task_id=parent["task_id"],
                subtask_id=_generate_subtask_id(parent["task_id"], parent["subtask_id"], item["index"]),
                user_id=parent["user_id"],
                type=TaskType.ASMR_TEXT_GENERATE,
                info=info,
                status=TaskStatus.DEBUG,
                result=ASMRTextGenerateResult(result_text=""),
                create_time=now,
                update_time=now,
                is_deleted=False,
            )
        )

    existing = mongo.find_documents(
        AUDIO_TASKS_COLLECTION,
        {"subtask_id": {"$in": [task.subtask_id for task in tasks]}},
        fields=("subtask_id",),
    )
    existing_ids = {doc["subtask_id"] for doc in existing}
    documents = [task.model_dump(mode="json") for task in tasks if task.subtask_id not in existing_ids]
    created = len(documents)
    if created:
        mongo.insert_documents(AUDIO_TASKS_COLLECTION, documents)
    return created


def dispatch_time_plan_if_done(mongo, task_id: str) -> bool:
    docs = mongo.find_documents(
        AUDIO_TASKS_COLLECTION,
        {
            "task_id": task_id,
            "type": TaskType.ASMR_TEXT_GENERATE.value,
            "is_deleted": False,
        },
        fields=("status",),
    )
    if not docs:
        raise ValueError("找不到 ASMR_TEXT_GENERATE 子任务")
    if any(TaskStatus(item["status"]) != TaskStatus.SUCCESS for item in docs):
        return False

    subtask_id = _time_plan_subtask_id(task_id)
    if mongo.find_one(AUDIO_TASKS_COLLECTION, {"subtask_id": subtask_id}, fields=("subtask_id",)) is not None:
        return False

    parent = mongo.find_one(
        AUDIO_TASKS_COLLECTION,
        {
            "task_id": task_id,
            "type": TaskType.ASMR_TEXT.value,
            "is_deleted": False,
        },
        fields=("info", "result.result_text", "user_id"),
    )
    if parent is None:
        raise ValueError("找不到 ASMR_TEXT 主任务")
    parent_info = parent["info"]
    source_result_text = parent["result"]["result_text"]
    if not source_result_text:
        raise ValueError("ASMR_TEXT 主任务没有可用的结果文本")
    now = _now()
    info = ASMRTimePlanInfo(
        title=parent_info["title"],
        reference_ids=parent_info["reference_ids"],
        theme=parent_info["theme"],
        duration_minutes=parent_info["duration_minutes"],
        language=parent_info["language"],
        source_result_text=source_result_text,
    )
    task = AudioTask(
        task_id=task_id,
        subtask_id=subtask_id,
        user_id=parent["user_id"],
        type=TaskType.ASMR_TIME_PLAN,
        info=info,
        status=TaskStatus.DEBUG,
        result=ASMRTimePlanResult(result_text="", prompt_tokens=0, completion_tokens=0),
        create_time=now,
        update_time=now,
        is_deleted=False,
    )
    mongo.insert_document(AUDIO_TASKS_COLLECTION, task.model_dump(mode="json"))
    return True
