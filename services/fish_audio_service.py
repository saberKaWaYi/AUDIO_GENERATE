import httpx

from settings.fish_audio import fish_audio_settings

import logging

logger = logging.getLogger(__name__)


class FishAudioError(Exception):
    pass


class FishAudioNotFoundError(LookupError):
    pass


class FishAudioConfigError(RuntimeError):
    pass


class FishAudioService:

    def synthesize(self, text: str, reference_id: str) -> bytes:
        api_key = fish_audio_settings.fish_audio_api_key.strip()
        if not api_key:
            raise FishAudioConfigError("FISH_AUDIO_API_KEY 未配置")

        url = f"{fish_audio_settings.fish_audio_base_url.rstrip('/')}/v1/tts"
        try:
            response = httpx.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "model": "s2.1-pro",
                },
                json={
                    "text": text,
                    "reference_id": reference_id,
                    "format": "mp3",
                    "mp3_bitrate": 192,
                    "condition_on_previous_chunks": True,
                },
                timeout=fish_audio_settings.fish_audio_timeout,
            )
        except httpx.HTTPError as e:
            logger.exception("Fish Audio TTS request failed, reference_id=%s", reference_id)
            raise FishAudioError("Fish Audio TTS 请求失败") from e

        if response.status_code in (401, 403):
            raise FishAudioConfigError("Fish Audio 密钥无效")
        if response.status_code == 404:
            raise FishAudioNotFoundError(f"上游无此角色：{reference_id}")
        if not response.is_success:
            raise FishAudioError(f"Fish Audio TTS 返回 {response.status_code}")

        if not response.content:
            raise FishAudioError("Fish Audio TTS 返回的音频为空")
        content_type = response.headers.get("content-type", "")
        if "audio" not in content_type:
            raise FishAudioError("Fish Audio TTS 返回体不是音频")
        return response.content

    def create_model(
        self,
        title: str,
        voices: list[tuple[str, bytes, str]],
        cover_image: tuple[str, bytes, str] | None = None,
        description: str | None = None,
        visibility: str = "private",
    ) -> dict:
        api_key = fish_audio_settings.fish_audio_api_key.strip()
        if not api_key:
            raise FishAudioConfigError("FISH_AUDIO_API_KEY 未配置")

        url = f"{fish_audio_settings.fish_audio_base_url.rstrip('/')}/model"
        data = {
            "type": "tts",
            "title": title,
            "train_mode": "fast",
            "visibility": visibility,
        }
        if description is not None:
            data["description"] = description

        files = [("voices", (name, content, content_type)) for name, content, content_type in voices]
        if cover_image is not None:
            name, content, content_type = cover_image
            files.append(("cover_image", (name, content, content_type)))

        try:
            response = httpx.post(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                data=data,
                files=files,
                timeout=fish_audio_settings.fish_audio_timeout,
            )
        except httpx.HTTPError as e:
            logger.error("Fish Audio create model request failed, title=%s", title)
            raise FishAudioError("Fish Audio 创建音色请求失败") from e

        if response.status_code in (401, 403):
            raise FishAudioConfigError("Fish Audio 密钥无效")
        if not response.is_success:
            raise FishAudioError(f"Fish Audio 创建音色返回 {response.status_code}")

        try:
            return response.json()
        except ValueError as e:
            raise FishAudioError("Fish Audio 创建音色返回体不是合法 JSON") from e

    def get_model(self, reference_id: str) -> dict:
        api_key = fish_audio_settings.fish_audio_api_key.strip()
        if not api_key:
            raise FishAudioConfigError("FISH_AUDIO_API_KEY 未配置")

        url = f"{fish_audio_settings.fish_audio_base_url.rstrip('/')}/model/{reference_id}"
        try:
            response = httpx.get(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=fish_audio_settings.fish_audio_timeout,
            )
        except httpx.HTTPError as e:
            logger.error("Fish Audio request failed, reference_id=%s", reference_id)
            raise FishAudioError("Fish Audio 请求失败") from e

        if response.status_code == 404:
            raise FishAudioNotFoundError(f"上游无此角色：{reference_id}")
        if response.status_code in (401, 403):
            raise FishAudioConfigError("Fish Audio 密钥无效")
        if not response.is_success:
            raise FishAudioError(f"Fish Audio 返回 {response.status_code}")

        try:
            return response.json()
        except ValueError as e:
            raise FishAudioError("Fish Audio 返回体不是合法 JSON") from e
