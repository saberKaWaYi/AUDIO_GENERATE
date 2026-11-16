from typing import Literal

from pydantic import Field

from settings.base import EnvSettings

LogServiceName = Literal["web", "worker"]


class CommonSettings(EnvSettings):
    debug: bool = Field(default=False, alias="DEBUG")


common_settings = CommonSettings()
