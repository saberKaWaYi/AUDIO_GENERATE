from datetime import datetime

from pydantic import BaseModel, Field

AUDIO_WORKS_COLLECTION = "audio_works"

WORK_TYPE_TTS = "tts"


class AudioWork(BaseModel):
    work_id: str = Field(min_length=1)
    user_id: int
    work_type: str = Field(min_length=1)
    title: str = Field(min_length=1)
    reference_id: str
    cover_image: str
    text: str
    file_name: str
    relative_path: str
    file_size: int
    content_type: str
    is_public: bool = False
    create_time: datetime
    update_time: datetime
    is_deleted: bool = False


AUDIO_WORK_INDEXES: list[dict] = [
    {"field": [("work_id", 1)], "unique": True},
    {"field": [("work_type", 1), ("is_public", 1), ("create_time", -1)], "unique": False},
    {"field": [("user_id", 1), ("create_time", -1)], "unique": False},
]
