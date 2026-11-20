from pydantic import BaseModel


class UserInfoResponse(BaseModel):

    user_id: int
    email: str | None
    name: str | None
    picture: str | None


class AuthConfigResponse(BaseModel):

    google_client_id: str
    email_enabled: bool
