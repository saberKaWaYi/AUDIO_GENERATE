from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from agents.prompts.text_prompt import get_text_system_prompt
from services.llm_service import LLMResult, chat, parse_json
from settings_config import settings
from tools.agent_tools import _load_characters, build_user_content

VALID_TYPES = {
    "human_speech",
    "non_verbal_human_sound",
    "action_generated_sound",
    "environmental_sound",
}

REQUIRED_FIELDS = {
    "start_time",
    "end_time",
    "type",
    "reference_id",
    "type_prompt",
    "polling_count",
}


class TextSegment(BaseModel):
    model_config = ConfigDict(strict=True)

    start_time: int = Field(ge=0)
    end_time: int = Field(ge=0)
    type: str
    reference_id: str | None
    type_prompt: str = Field(min_length=1)
    polling_count: int | None

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in VALID_TYPES:
            raise ValueError(f"不支持的片段类型：{value}")
        return value

    @model_validator(mode="after")
    def validate_time_range(self) -> "TextSegment":
        if self.end_time <= self.start_time:
            raise ValueError(
                f"end_time 必须大于 start_time：{self.start_time} -> {self.end_time}"
            )
        return self

    @model_validator(mode="after")
    def validate_reference(self) -> "TextSegment":
        if self.type in {"human_speech", "non_verbal_human_sound"} and self.reference_id is None:
            raise ValueError(f"{self.type} 必须指定 reference_id")
        if self.type in {"action_generated_sound", "environmental_sound"} and self.reference_id is not None:
            raise ValueError(f"{self.type} 的 reference_id 必须为 None")
        return self

    @model_validator(mode="after")
    def validate_polling_count(self) -> "TextSegment":
        if self.type in {"human_speech", "non_verbal_human_sound"}:
            if self.polling_count is not None:
                raise ValueError(f"{self.type} 的 polling_count 必须为 None")
        elif self.polling_count is None:
            raise ValueError(f"{self.type} 必须指定 polling_count")
        elif self.polling_count < 1:
            raise ValueError(f"{self.type} 的 polling_count 必须为正整数：{self.polling_count}")
        return self


class TextTimeline(BaseModel):
    model_config = ConfigDict(strict=True)

    segments: list[TextSegment] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_vocal_overlap(self) -> "TextTimeline":
        vocal_by_reference: dict[str, list[TextSegment]] = {}
        for segment in self.segments:
            if segment.type in {"human_speech", "non_verbal_human_sound"}:
                vocal_by_reference.setdefault(segment.reference_id, []).append(segment)
        for reference_id, segments in vocal_by_reference.items():
            ordered = sorted(segments, key=lambda segment: segment.start_time)
            for previous, current in zip(ordered, ordered[1:]):
                if current.start_time < previous.end_time:
                    raise ValueError(
                        f"角色 {reference_id} 的人声片段时间重叠："
                        f"{previous.start_time}-{previous.end_time} 与 "
                        f"{current.start_time}-{current.end_time}"
                    )
        return self


class TextOutcome:
    def __init__(self, llm_result: LLMResult, segments: list[TextSegment]):
        self.llm_result = llm_result
        self.segments = segments


def _validate_segments(data: list) -> None:
    if not isinstance(data, list):
        raise ValueError("模型返回的 segments 不是数组")
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"第 {index} 个片段不是对象")
        missing = REQUIRED_FIELDS - set(item)
        if missing:
            raise ValueError(f"第 {index} 个片段缺少字段：{sorted(missing)}")


def run_text(subtask: dict) -> TextOutcome:
    api_key = settings.deepseek_api_key.strip()
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 未配置")
    system_prompt = get_text_system_prompt()
    if not system_prompt.strip():
        raise ValueError("text_prompt.txt 未填写")

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

    payload = parse_json(result.raw_text)
    if "segments" not in payload:
        raise ValueError("模型返回缺少 segments")
    segments = payload["segments"]
    _validate_segments(segments)
    timeline = TextTimeline.model_validate({"segments": segments})
    valid_reference_ids = {character["reference_id"] for character in characters}
    for segment in timeline.segments:
        if segment.reference_id is not None and segment.reference_id not in valid_reference_ids:
            raise ValueError(f"片段引用了不存在的角色 ID：{segment.reference_id}")
    total_seconds = subtask["info"]["duration_minutes"] * 60
    max_end_time = max(segment.end_time for segment in timeline.segments)
    if max_end_time > total_seconds:
        raise ValueError(
            f"片段结束时间超出作品总时长：{max_end_time} > {total_seconds}"
        )
    return TextOutcome(result, timeline.segments)
