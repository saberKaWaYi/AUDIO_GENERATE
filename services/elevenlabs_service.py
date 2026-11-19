import httpx

from settings.elevenlabs import elevenlabs_settings

import logging

logger = logging.getLogger(__name__)


class ElevenLabsError(Exception):
    pass


class ElevenLabsAuthError(ElevenLabsError):
    pass


class ElevenLabsExhaustedError(ElevenLabsError):
    pass


class ElevenLabsConfigError(RuntimeError):
    pass


class ElevenLabsService:

    def __init__(self, api_keys: list[str]):
        if not api_keys:
            raise ElevenLabsConfigError("ELEVENLABS_API_KEYS 未配置")
        self._api_keys = api_keys
        self._exhausted: set[str] = set()

    def compose_music(self, prompt: str, music_length_ms: int = 30000) -> bytes:
        for api_key in self._api_keys:
            if api_key in self._exhausted:
                continue
            try:
                return self._compose_music(prompt, api_key, music_length_ms)
            except ElevenLabsExhaustedError:
                self._exhausted.add(api_key)
                logger.warning("ElevenLabs 账号额度耗尽，切换下一个，key=%s***", api_key[:8])
        raise ElevenLabsExhaustedError("所有 ElevenLabs 账号额度已耗尽")

    def compose_sound(self, text: str, duration_seconds: float, loop: bool) -> bytes:
        for api_key in self._api_keys:
            if api_key in self._exhausted:
                continue
            try:
                return self._compose_sound(text, api_key, duration_seconds, loop)
            except ElevenLabsExhaustedError:
                self._exhausted.add(api_key)
                logger.warning("ElevenLabs 账号额度耗尽，切换下一个，key=%s***", api_key[:8])
        raise ElevenLabsExhaustedError("所有 ElevenLabs 账号额度已耗尽")

    def _compose_music(self, prompt: str, api_key: str, music_length_ms: int) -> bytes:
        url = f"{elevenlabs_settings.elevenlabs_base_url.rstrip('/')}/v1/music"
        try:
            response = httpx.post(
                url,
                headers={"xi-api-key": api_key, "Content-Type": "application/json"},
                json={
                    "prompt": prompt,
                    "model_id": elevenlabs_settings.elevenlabs_music_model_id,
                    "music_length_ms": music_length_ms,
                    "force_instrumental": True,
                },
                timeout=elevenlabs_settings.elevenlabs_timeout,
            )
        except httpx.HTTPError as e:
            logger.error("ElevenLabs music request failed")
            raise ElevenLabsError("ElevenLabs 音乐请求失败") from e

        if response.status_code in (402, 429):
            raise ElevenLabsExhaustedError(f"ElevenLabs 账号额度或配额不足：HTTP {response.status_code}")
        if response.status_code in (401, 403):
            raise ElevenLabsAuthError("ElevenLabs 密钥无效")
        if not response.is_success:
            raise ElevenLabsError(f"ElevenLabs 返回 {response.status_code}")

        if not response.content:
            raise ElevenLabsError("ElevenLabs 返回的音频为空")
        content_type = response.headers.get("content-type", "")
        if "audio" not in content_type:
            raise ElevenLabsError("ElevenLabs 返回体不是音频")
        return response.content

    def _compose_sound(self, text: str, api_key: str, duration_seconds: float, loop: bool) -> bytes:
        url = f"{elevenlabs_settings.elevenlabs_base_url.rstrip('/')}/v1/sound-generation"
        try:
            response = httpx.post(
                url,
                params={"output_format": "mp3_44100_192"},
                headers={"xi-api-key": api_key, "Content-Type": "application/json"},
                json={
                    "text": text,
                    "duration_seconds": duration_seconds,
                    "loop": loop,
                    "model_id": elevenlabs_settings.elevenlabs_sound_model_id,
                },
                timeout=elevenlabs_settings.elevenlabs_timeout,
            )
        except httpx.HTTPError as e:
            logger.error("ElevenLabs sound request failed")
            raise ElevenLabsError("ElevenLabs 音效请求失败") from e

        if response.status_code in (402, 429):
            raise ElevenLabsExhaustedError(f"ElevenLabs 账号额度或配额不足：HTTP {response.status_code}")
        if response.status_code in (401, 403):
            raise ElevenLabsAuthError("ElevenLabs 密钥无效")
        if not response.is_success:
            raise ElevenLabsError(f"ElevenLabs 返回 {response.status_code}")

        if not response.content:
            raise ElevenLabsError("ElevenLabs 返回的音频为空")
        content_type = response.headers.get("content-type", "")
        if "audio" not in content_type:
            raise ElevenLabsError("ElevenLabs 返回体不是音频")
        return response.content
