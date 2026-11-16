from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

AUDIO_CHARACTERS_COLLECTION = "audio_characters"


class FishModelEntity(BaseModel):
    model_config = ConfigDict(strict=True)

    reference_id: str = Field(alias="_id", min_length=1)
    type: str
    title: str
    state: str
    description: str
    cover_image: str
    train_mode: str
    tags: list[str]
    languages: list[str]
    visibility: str
    default_text: str
    source: str | None
    created_at: str
    updated_at: str


class AudioCharacter(BaseModel):

    user_id: int
    reference_id: str
    title: str
    description: str
    cover_image: str
    type: str
    train_mode: str
    state: str
    visibility: str
    tags: list[str]
    languages: list[str]
    default_text: str
    source: str | None
    created_at: str
    updated_at: str

    create_time: datetime
    update_time: datetime
    is_deleted: bool


AUDIO_CHARACTER_INDEXES: list[dict] = [
    {"field": [("user_id", 1), ("reference_id", 1)], "unique": True},
    {"field": [("user_id", 1), ("update_time", -1)], "unique": False},
]
