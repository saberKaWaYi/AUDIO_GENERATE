from datetime import datetime
from enum import Enum

from pydantic import BaseModel

AUDIO_TASKS_COLLECTION = "audio_tasks"


class TaskLanguage(str, Enum):
    ZH = "zh"
    JA = "ja"
    EN = "en"
    KO = "ko"


class TaskType(str, Enum):
    ASMR_TEXT = "ASMR_TEXT"
    ASMR_BACKEND_MUSIC = "ASMR_BACKEND_MUSIC"


class TaskStatus(str, Enum):
    PENDING = "pending"


class ASMRTextInfo(BaseModel):
    title: str
    reference_ids: list[str]
    theme: str
    duration_minutes: int
    language: TaskLanguage


class ASMRBackendMusicInfo(BaseModel):
    title: str
    reference_ids: list[str]
    theme: str


TaskInfo = ASMRTextInfo | ASMRBackendMusicInfo


class ASMRTextResult(BaseModel):
    result_text: str
    prompt_tokens: int
    completion_tokens: int


class ASMRBackendMusicResult(BaseModel):
    result_text: str
    prompt_tokens: int
    completion_tokens: int


TaskResult = ASMRTextResult | ASMRBackendMusicResult


class AudioTask(BaseModel):
    task_id: str
    subtask_id: str
    user_id: int
    type: TaskType
    info: TaskInfo
    status: TaskStatus
    result: TaskResult
    create_time: datetime
    update_time: datetime
    is_deleted: bool


AUDIO_TASK_INDEXES: list[dict] = [
    {"field": "subtask_id", "unique": True},
    {"field": "task_id", "unique": False},
    {"field": [("user_id", 1), ("create_time", -1)], "unique": False},
    {"field": "status", "unique": False},
]
