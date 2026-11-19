from datetime import datetime

from pydantic import BaseModel, Field

AUDIO_USERS_COLLECTION = "audio_users"
AUDIO_USER_IDENTITIES_COLLECTION = "audio_user_identities"
AUDIO_COUNTERS_COLLECTION = "audio_counters"

USER_ID_COUNTER_KEY = "user_id"


class AudioUser(BaseModel):
    user_id: int
    email: str | None
    name: str | None
    picture: str | None
    create_time: datetime
    update_time: datetime


class UserIdentity(BaseModel):
    identity_id: str = Field(min_length=1)
    user_id: int
    provider: str = Field(min_length=1)
    provider_user_id: str = Field(min_length=1)
    email: str | None
    create_time: datetime


class AudioCounter(BaseModel):
    key: str = Field(min_length=1)
    value: int = Field(ge=0)


AUDIO_USER_INDEXES: list[dict] = [
    {"field": [("user_id", 1)], "unique": True},
]

AUDIO_USER_IDENTITY_INDEXES: list[dict] = [
    {"field": [("provider", 1), ("provider_user_id", 1)], "unique": True},
    {"field": [("user_id", 1)], "unique": False},
]
