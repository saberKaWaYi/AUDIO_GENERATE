from app.auth.auth_service import (
    PROVIDER_EMAIL,
    PROVIDER_GOOGLE,
    deliver_email_code,
    find_or_create_user,
    generate_email_code,
    save_email_code,
    verify_email_code,
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


def send_email_login_code(mongo, email: str) -> None:
    code = generate_email_code()
    save_email_code(mongo, email, code)
    deliver_email_code(email, code)


def login_with_email(mongo, email: str, code: str) -> AudioUser:
    verify_email_code(mongo, email, code)
    return find_or_create_user(
        mongo,
        PROVIDER_EMAIL,
        email,
        email,
        None,
        None,
    )
