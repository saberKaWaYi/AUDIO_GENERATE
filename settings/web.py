from pydantic import Field

from settings.base import EnvSettings


class WebSettings(EnvSettings):

    web_debug: bool | None = Field(default=None, alias="WEB_DEBUG")
    web_name: str = Field(default="Audio Generate Web Service", alias="WEB_NAME")
    web_version: str = Field(default="1.0", alias="WEB_VERSION")
    web_api_key: str = Field(default="", alias="BACKEND_API_KEY")


web_settings = WebSettings()
