from pydantic import Field

from settings.base import EnvSettings


class MongoSettings(EnvSettings):

    mongodb_host: str = Field(default="127.0.0.1", alias="MONGODB_HOST")
    mongodb_port: int = Field(default=27017, alias="MONGODB_PORT")
    mongodb_username: str = Field(default="", alias="MONGODB_USERNAME")
    mongodb_password: str = Field(default="", alias="MONGODB_PASSWORD")
    mongodb_database: str = Field(default="audio_generate", alias="MONGODB_DATABASE")


mongo_settings = MongoSettings()
