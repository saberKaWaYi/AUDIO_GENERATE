import json

from agents.prompts.text_prompt import get_text_system_prompt
from services.llm_service import chat, parse_json
from settings_config import settings
from tools.agent_tools import _load_characters, build_user_content

REQUIRED_FIELDS = {"start_time", "end_time", "reference_id", "text"}


class TextOutcome:
    def __init__(self, result_text: str, prompt_tokens: int, completion_tokens: int):
        self.result_text = result_text
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


def _validate_segments(data: list) -> None:
    if not isinstance(data, list):
        raise ValueError("模型返回的 segments 不是数组")
    if len(data) == 0:
        raise ValueError("模型返回的 segments 为空")
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"第 {index} 个片段不是对象")
        missing = REQUIRED_FIELDS - set(item)
        if missing:
            raise ValueError(f"第 {index} 个片段缺少字段：{sorted(missing)}")
        extra = set(item) - REQUIRED_FIELDS
        if extra:
            raise ValueError(f"第 {index} 个片段多余字段：{sorted(extra)}")
        for field in ("start_time", "end_time"):
            if type(item[field]) is not int or item[field] < 0:
                raise ValueError(f"第 {index} 个片段 {field} 必须是非负整数")
        for field in ("reference_id", "text"):
            if not isinstance(item[field], str) or not item[field]:
                raise ValueError(f"第 {index} 个片段 {field} 必须是非空字符串")
        if item["end_time"] <= item["start_time"]:
            raise ValueError(
                f"第 {index} 个片段 end_time 必须大于 start_time："
                f"{item['start_time']} -> {item['end_time']}"
            )


def run_text(subtask: dict) -> TextOutcome:
    api_key = settings.deepseek_api_key.strip()
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 未配置")
    system_prompt = get_text_system_prompt()
    if not system_prompt.strip():
        raise ValueError("text_prompt.txt 提示词未填写")

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

    valid_reference_ids = {character["reference_id"] for character in characters}
    for segment in segments:
        if segment["reference_id"] not in valid_reference_ids:
            raise ValueError(f"片段引用了不存在的角色 ID：{segment['reference_id']}")

    vocal_by_reference: dict[str, list[dict]] = {}
    for segment in segments:
        vocal_by_reference.setdefault(segment["reference_id"], []).append(segment)
    for reference_id, group in vocal_by_reference.items():
        ordered = sorted(group, key=lambda segment: segment["start_time"])
        for previous, current in zip(ordered, ordered[1:]):
            if current["start_time"] < previous["end_time"]:
                raise ValueError(
                    f"角色 {reference_id} 的人声片段时间重叠："
                    f"{previous['start_time']}-{previous['end_time']} 与 "
                    f"{current['start_time']}-{current['end_time']}"
                )

    total_seconds = subtask["info"]["duration_minutes"] * 60
    max_end_time = max(segment["end_time"] for segment in segments)
    if max_end_time > total_seconds:
        raise ValueError(f"片段结束时间超出作品总时长：{max_end_time} > {total_seconds}")

    return TextOutcome(
        json.dumps({"segments": segments}, ensure_ascii=False),
        result.prompt_tokens,
        result.completion_tokens,
    )
