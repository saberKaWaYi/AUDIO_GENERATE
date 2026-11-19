from pydantic import Field

from settings.base import EnvSettings


class AuthSettings(EnvSettings):

    google_client_id: str = Field(default="", alias="GOOGLE_CLIENT_ID")
    session_secret: str = Field(default="", alias="SESSION_SECRET")
    session_ttl_seconds: int = Field(default=604800, alias="SESSION_TTL_SECONDS")
    allowed_origins: str = Field(
        default="http://localhost:8002", alias="ALLOWED_ORIGINS"
    )


auth_settings = AuthSettings()
