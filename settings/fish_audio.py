from pydantic import Field

from settings.base import EnvSettings


class FishAudioSettings(EnvSettings):

    fish_audio_base_url: str = Field(default="https://api.fish.audio", alias="FISH_AUDIO_BASE_URL")
    fish_audio_api_key: str = Field(default="", alias="FISH_AUDIO_API_KEY")
    fish_audio_timeout: float = Field(default=30.0, alias="FISH_AUDIO_TIMEOUT")


fish_audio_settings = FishAudioSettings()
