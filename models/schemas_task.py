from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

AUDIO_TASKS_COLLECTION = "audio_tasks"


class TaskLanguage(str, Enum):
    ZH = "zh"
    JA = "ja"
    EN = "en"
    KO = "ko"


class TaskType(str, Enum):
    ASMR_TEXT = "ASMR_TEXT"
    ASMR_BACKEND_MUSIC = "ASMR_BACKEND_MUSIC"
    ASMR_BACKEND_SUBMUSIC = "ASMR_BACKEND_SUBMUSIC"


class TaskStatus(str, Enum):
    DEBUG = "debug"
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


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
    duration_minutes: int
    language: TaskLanguage


class ASMRBackendSubMusicInfo(BaseModel):
    prompt: str = Field(min_length=1)
    duration_seconds: int = Field(ge=3, le=180)


TaskInfo = ASMRTextInfo | ASMRBackendMusicInfo | ASMRBackendSubMusicInfo


class ASMRTextResult(BaseModel):
    result_text: str
    prompt_tokens: int
    completion_tokens: int


class ASMRBackendMusicResult(BaseModel):
    result_text: str
    prompt_tokens: int
    completion_tokens: int


class ASMRBackendSubMusicResult(BaseModel):
    result_text: str


TaskResult = ASMRTextResult | ASMRBackendMusicResult | ASMRBackendSubMusicResult


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
