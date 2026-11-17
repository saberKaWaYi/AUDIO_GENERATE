import json

from pydantic import BaseModel, ConfigDict, Field

from agents.prompts.music_prompt import get_music_system_prompt
from models.schemas_character import AUDIO_CHARACTERS_COLLECTION
from services.llm_service import LLMResult, chat, parse_json
from services.mongo_service import MongoService
from settings_config import settings


class MusicTrack(BaseModel):
    model_config = ConfigDict(strict=True)

    prompt: str = Field(min_length=1)
    duration_seconds: int = Field(ge=3, le=180)


class MusicTracks(BaseModel):
    tracks: list[MusicTrack] = Field(min_length=1)


class MusicOutcome:
    def __init__(self, llm_result: LLMResult, tracks: list[MusicTrack]):
        self.llm_result = llm_result
        self.tracks = tracks


CHARACTER_FIELDS = ("reference_id", "title", "tags", "languages")


def _get_mongo() -> MongoService:
    from worker.runner import mongo_service

    if mongo_service is None:
        raise RuntimeError("Mongo service 尚未初始化，无法读取角色数据")
    return mongo_service


def _load_characters(subtask: dict) -> list[dict]:
    reference_ids = subtask["info"]["reference_ids"]
    docs = _get_mongo().find_documents(
        AUDIO_CHARACTERS_COLLECTION,
        {
            "user_id": subtask["user_id"],
            "reference_id": {"$in": reference_ids},
            "is_deleted": False,
        },
    )
    if len(docs) != len(reference_ids):
        raise ValueError(
            f"角色数量不匹配：请求 {len(reference_ids)} 个，查到 {len(docs)} 个"
        )
    return [{field: doc[field] for field in CHARACTER_FIELDS} for doc in docs]


def build_user_content(subtask: dict, characters: list[dict]) -> str:
    payload = {
        "info": subtask["info"],
        "characters": characters,
    }
    return json.dumps(payload, ensure_ascii=False, default=str)


def run_music(subtask: dict) -> MusicOutcome:
    api_key = settings.deepseek_api_key.strip()
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 未配置")
    system_prompt = get_music_system_prompt()
    if not system_prompt.strip():
        raise ValueError("music_prompt.txt 未填写")

    characters = _load_characters(subtask)
    result = chat(
        base_url=settings.deepseek_base_url,
        api_key=api_key,
        model=settings.deepseek_model,
        system=system_prompt,
        user=build_user_content(subtask, characters),
        temperature=settings.deepseek_temperature,
        max_tokens=settings.deepseek_max_tokens,
        max_retries=settings.deepseek_max_retries,
        timeout=settings.deepseek_timeout,
    )

    tracks = MusicTracks.model_validate(parse_json(result.raw_text))
    return MusicOutcome(result, tracks.tracks)
