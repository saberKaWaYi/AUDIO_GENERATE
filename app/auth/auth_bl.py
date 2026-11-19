from app.auth.auth_service import (
    PROVIDER_GOOGLE,
    find_or_create_user,
    verify_google_credential,
)
from models.schemas_user import AudioUser


def login_with_google(mongo, credential: str) -> AudioUser:
    payload = verify_google_credential(credential)
    sub = payload["sub"]
    if not isinstance(sub, str) or not sub:
        raise ValueError("Google 身份 sub 异常")

    email = payload.get("email")
    if email is not None and not isinstance(email, str):
        raise ValueError("Google 身份 email 异常")
    name = payload.get("name")
    if name is not None and not isinstance(name, str):
        raise ValueError("Google 身份 name 异常")
    picture = payload.get("picture")
    if picture is not None and not isinstance(picture, str):
        raise ValueError("Google 身份 picture 异常")

    return find_or_create_user(
        mongo,
        PROVIDER_GOOGLE,
        sub,
        email,
        name,
        picture,
    )
