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
    ASMR_TEXT_GENERATE = "ASMR_TEXT_GENERATE"
    ASMR_TIME_PLAN = "ASMR_TIME_PLAN"


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


class ASMRTextGenerateInfo(BaseModel):
    index: int
    reference_id: str
    text: str


class ASMRTimePlanInfo(BaseModel):
    title: str
    reference_ids: list[str]
    theme: str
    duration_minutes: int
    language: TaskLanguage
    source_result_text: str


TaskInfo = ASMRTextInfo | ASMRTextGenerateInfo | ASMRTimePlanInfo


class ASMRTextResult(BaseModel):
    result_text: str
    prompt_tokens: int
    completion_tokens: int


class ASMRTextGenerateResult(BaseModel):
    result_text: str


class ASMRGenerateAudioResult(BaseModel):
    duration_ms: int
    relative_path: str


class ASMRTimePlanResult(BaseModel):
    result_text: str
    prompt_tokens: int
    completion_tokens: int


TaskResult = ASMRTextResult | ASMRTextGenerateResult | ASMRTimePlanResult


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
    is_public: bool = False


AUDIO_TASK_INDEXES: list[dict] = [
    {"field": "subtask_id", "unique": True},
    {"field": "task_id", "unique": False},
    {"field": [("user_id", 1), ("create_time", -1)], "unique": False},
    {"field": "status", "unique": False},
]
