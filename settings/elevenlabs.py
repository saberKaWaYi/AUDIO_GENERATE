from pydantic import Field

from settings.base import EnvSettings


class ElevenLabsSettings(EnvSettings):

    elevenlabs_base_url: str = Field(default="https://api.elevenlabs.io", alias="ELEVENLABS_BASE_URL")
    elevenlabs_api_keys: str = Field(default="", alias="ELEVENLABS_API_KEYS")
    elevenlabs_music_model_id: str = Field(default="music_v2_5", alias="ELEVENLABS_MUSIC_MODEL_ID")
    elevenlabs_sound_model_id: str = Field(default="eleven_text_to_sound_v3", alias="ELEVENLABS_SOUND_MODEL_ID")
    elevenlabs_timeout: float = Field(default=600.0, alias="ELEVENLABS_TIMEOUT")


elevenlabs_settings = ElevenLabsSettings()
