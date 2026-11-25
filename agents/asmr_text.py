import json

from agents.prompts.asmr_text_prompt import get_text_system_prompt
from services.llm_service import chat
from settings_config import settings
from tools.agent_tools import _load_characters, build_user_content

REQUIRED_FIELDS = {"index", "reference_id", "text"}


class TextOutcome:
    def __init__(self, result_text: str, prompt_tokens: int, completion_tokens: int):
        self.result_text = result_text
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


def _validate_dialogue(data: list) -> None:
    if not isinstance(data, list):
        raise ValueError("模型返回的对白不是数组")
    if len(data) == 0:
        raise ValueError("模型返回的对白为空")
    for position, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"第 {position} 条对白不是对象")
        missing = REQUIRED_FIELDS - set(item)
        if missing:
            raise ValueError(f"第 {position} 条对白缺少字段：{sorted(missing)}")
        extra = set(item) - REQUIRED_FIELDS
        if extra:
            raise ValueError(f"第 {position} 条对白多余字段：{sorted(extra)}")
        if type(item["index"]) is not int or item["index"] < 1:
            raise ValueError(f"第 {position} 条对白 index 必须是正整数")
        if not isinstance(item["reference_id"], str) or not item["reference_id"]:
            raise ValueError(f"第 {position} 条对白 reference_id 必须是非空字符串")
        if not isinstance(item["text"], str) or not item["text"]:
            raise ValueError(f"第 {position} 条对白 text 必须是非空字符串")


def run_text(subtask: dict) -> TextOutcome:
    api_key = settings.deepseek_api_key.strip()
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 未配置")
    system_prompt = get_text_system_prompt()
    if not system_prompt.strip():
        raise ValueError("asmr_text_prompt.txt 提示词未填写")

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

    dialogue = json.loads(result.raw_text)
    _validate_dialogue(dialogue)

    valid_reference_ids = {character["reference_id"] for character in characters}
    for item in dialogue:
        if item["reference_id"] not in valid_reference_ids:
            raise ValueError(f"对白引用了不存在的角色 ID：{item['reference_id']}")

    return TextOutcome(
        result_text=result.raw_text,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
    )
