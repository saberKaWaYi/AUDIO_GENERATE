from pydantic import Field

from settings.base import EnvSettings


class WorkerSettings(EnvSettings):

    worker_debug: bool | None = Field(default=None, alias="WORKER_DEBUG")
    worker_poll_interval: float = Field(default=5.0, alias="WORKER_POLL_INTERVAL")
    music_data_dir: str = Field(default="data", alias="MUSIC_DATA_DIR")


worker_settings = WorkerSettings()
