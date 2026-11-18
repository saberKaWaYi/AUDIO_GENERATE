from pydantic import Field

from settings.base import EnvSettings


class DeepSeekSettings(EnvSettings):

    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    deepseek_model: str = Field(default="deepseek-flash", alias="DEEPSEEK_MODEL")
    deepseek_temperature: float = Field(default=0.7, alias="DEEPSEEK_TEMPERATURE")
    deepseek_max_tokens: int = Field(default=393216, alias="DEEPSEEK_MAX_TOKENS")
    deepseek_timeout: float = Field(default=600.0, alias="DEEPSEEK_TIMEOUT")
    deepseek_max_retries: int = Field(default=3, alias="DEEPSEEK_MAX_RETRIES")


deepseek_settings = DeepSeekSettings()
