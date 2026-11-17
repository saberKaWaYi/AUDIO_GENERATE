import json
import time
from dataclasses import dataclass

import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMResult:
    raw_text: str
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
    duration_ms: int
    call_count: int


_clients: dict[tuple[str, str], object] = {}


def _get_client(base_url: str, api_key: str):
    cache_key = (base_url, api_key)
    client = _clients.get(cache_key)
    if client is None:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=base_url)
        _clients[cache_key] = client
    return client


def parse_json(raw_text: str) -> dict:
    data = json.loads(raw_text)
    if not isinstance(data, dict):
        raise ValueError("模型返回不是合法的 JSON 对象")
    return data


def chat(
    *,
    base_url: str,
    api_key: str,
    model: str,
    system: str,
    user: str,
    temperature: float,
    max_tokens: int,
    max_retries: int,
    timeout: float,
) -> LLMResult:
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})

    started = time.monotonic()
    attempts = max(max_retries, 0) + 1
    prompt_tokens = completion_tokens = 0
    finish_reason = ""

    client = _get_client(base_url, api_key)
    attempts_used = 0
    for attempt in range(1, attempts + 1):
        try:
            attempts_used = attempt
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                extra_body={"thinking": {"type": "enabled"}},
            )
            choice = response.choices[0]
            usage = getattr(response, "usage", None)
            prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
            completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
            finish_reason = str(getattr(choice, "finish_reason", "") or "")
            raw_text = choice.message.content
            if raw_text is None:
                raise ValueError(f"模型未返回内容：finish_reason={finish_reason!r}")
            break
        except Exception as exc:
            if attempt < attempts:
                wait_seconds = 2 ** (attempt - 1)
                logger.warning(
                    "模型调用失败，%s 秒后再重试（第 %s/%s 次）：%s",
                    wait_seconds,
                    attempt,
                    attempts - 1,
                    exc,
                )
                time.sleep(wait_seconds)
                continue
            raise

    return LLMResult(
        raw_text=raw_text,
        finish_reason=finish_reason,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        duration_ms=int((time.monotonic() - started) * 1000),
        call_count=attempts_used,
    )
