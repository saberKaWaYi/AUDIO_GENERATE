import json
from datetime import datetime
from uuid import NAMESPACE_URL, uuid5

from models.schemas_task import (
    ASMRTextGenerateInfo,
    ASMRTextGenerateResult,
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
