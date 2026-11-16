import json

from pydantic import BaseModel, ConfigDict, Field

from agents.prompts.music_prompt import get_music_system_prompt
from services.llm_service import LLMResult, chat, parse_json
from settings_config import settings


class MusicTrack(BaseModel):
    model_config = ConfigDict(strict=True)

    prompt: str = Field(min_length=1)
    duration_seconds: int = Field(gt=0)


class MusicTracks(BaseModel):
    tracks: list[MusicTrack] = Field(min_length=1)


class MusicOutcome:
    def __init__(self, llm_result: LLMResult, tracks: list[MusicTrack]):
        self.llm_result = llm_result
        self.tracks = tracks


def build_user_content(subtask: dict, characters: list[dict]) -> str:
    payload = {
        "info": subtask["info"],
        "characters": characters,
    }
    return json.dumps(payload, ensure_ascii=False, default=str)


def run_music(subtask: dict, characters: list[dict]) -> MusicOutcome:
    api_key = settings.deepseek_api_key.strip()
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 未配置")
    system_prompt = get_music_system_prompt()
    if not system_prompt.strip():
        raise ValueError("music_prompt.txt 未填写")

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
