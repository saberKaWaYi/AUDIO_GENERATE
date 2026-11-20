from pydantic import Field

from settings.base import EnvSettings


class AuthSettings(EnvSettings):

    google_client_id: str = Field(default="", alias="GOOGLE_CLIENT_ID")
    session_secret: str = Field(default="", alias="SESSION_SECRET")
    session_ttl_seconds: int = Field(default=604800, alias="SESSION_TTL_SECONDS")
    session_cookie_secure: bool = Field(
        default=False, alias="SESSION_COOKIE_SECURE"
    )


auth_settings = AuthSettings()
