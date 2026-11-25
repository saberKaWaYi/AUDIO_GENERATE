import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from uuid import uuid4

import jwt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from settings.auth import auth_settings
from settings.email import email_settings
from models.schemas_user import (
    AUDIO_COUNTERS_COLLECTION,
    AUDIO_EMAIL_CODES_COLLECTION,
    AUDIO_USER_IDENTITIES_COLLECTION,
    AUDIO_USERS_COLLECTION,
    USER_ID_COUNTER_KEY,
    AudioCounter,
    AudioUser,
    EmailCode,
    UserIdentity,
)

SESSION_COOKIE_NAME = "session"

PROVIDER_GOOGLE = "google"
PROVIDER_EMAIL = "email"

EMAIL_CODE_SEND_INTERVAL_SECONDS = 60


def verify_google_credential(credential: str) -> dict:
    client_id = auth_settings.google_client_id.strip()
    if not client_id:
        raise RuntimeError("GOOGLE_CLIENT_ID 未配置")
    return id_token.verify_oauth2_token(
        credential, google_requests.Request(), audience=client_id
    )


def generate_email_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def deliver_email_code(email: str, code: str) -> None:
    host = email_settings.smtp_host.strip()
    user = email_settings.smtp_user.strip()
    password = email_settings.smtp_password.strip()
    if not host or not user or not password:
        raise RuntimeError("SMTP 邮箱配置未完整")
    ttl_minutes = email_settings.email_code_ttl_seconds // 60
    message = EmailMessage()
    message["Subject"] = "Your AI AUDIO verification code"
    message["From"] = user
    message["To"] = email
    message.set_content(
        "Hello,\n\n"
        f"Your verification code for AI AUDIO is {code}.\n\n"
        f"This code will expire in {ttl_minutes} minutes. "
        "If you did not request this code, you can safely ignore this email.\n\n"
        "— The AI AUDIO Team"
    )
    with smtplib.SMTP_SSL(host, email_settings.smtp_port, timeout=10) as smtp:
        smtp.login(user, password)
        smtp.send_message(message)


def save_email_code(mongo, email: str, code: str) -> None:
    now = datetime.utcnow()
    record = EmailCode(
        email=email,
        code=code,
        expire_time=now + timedelta(seconds=email_settings.email_code_ttl_seconds),
        used=False,
        create_time=now,
    )
    mongo.update_documents(
        AUDIO_EMAIL_CODES_COLLECTION,
        {"email": email, "used": False},
        {"$set": {"used": True}},
    )
    mongo.insert_document(AUDIO_EMAIL_CODES_COLLECTION, record.model_dump(mode="json"))


def verify_email_code(mongo, email: str, code: str) -> None:
    doc = mongo.find_one(
        AUDIO_EMAIL_CODES_COLLECTION,
        {"email": email, "code": code, "used": False},
        fields=("email", "code", "expire_time", "used", "create_time"),
    )
    if doc is None:
        raise ValueError("验证码错误或已失效")
    record = EmailCode.model_validate(doc)
    if record.expire_time < datetime.utcnow():
        raise ValueError("验证码已过期")
    mongo.update_documents(
        AUDIO_EMAIL_CODES_COLLECTION,
        {"email": email, "code": code, "used": False},
        {"$set": {"used": True}},
    )


def next_user_id(mongo) -> int:
    counter = mongo.find_one_and_update(
        AUDIO_COUNTERS_COLLECTION,
        {"key": USER_ID_COUNTER_KEY},
        {"$inc": {"value": 1}},
    )
    if counter is None:
        raise RuntimeError("用户 ID 计数器未初始化")
    return AudioCounter.model_validate(counter).value + 1


def get_user(mongo, user_id: int) -> AudioUser | None:
    doc = mongo.find_one(
        AUDIO_USERS_COLLECTION,
        {"user_id": user_id},
        fields=("user_id", "email", "name", "picture", "create_time", "update_time"),
    )
    if doc is None:
        return None
    return AudioUser.model_validate(doc)


def find_or_create_user(
    mongo,
    provider: str,
    provider_user_id: str,
    email: str | None,
    name: str | None,
    picture: str | None,
) -> AudioUser:
    identity = mongo.find_one(
        AUDIO_USER_IDENTITIES_COLLECTION,
        {"provider": provider, "provider_user_id": provider_user_id},
        fields=("user_id",),
    )
    if identity is not None:
        user = get_user(mongo, identity["user_id"])
        if user is None:
            raise RuntimeError("登录方式关联的用户不存在")
        return user

    now = datetime.utcnow()
    user_id = next_user_id(mongo)
    user = AudioUser(
        user_id=user_id,
        email=email,
        name=name,
        picture=picture,
        create_time=now,
        update_time=now,
    )
    identity_doc = UserIdentity(
        identity_id=uuid4().hex,
        user_id=user_id,
        provider=provider,
        provider_user_id=provider_user_id,
        email=email,
        create_time=now,
    )
    mongo.insert_document(AUDIO_USERS_COLLECTION, user.model_dump(mode="json"))
    mongo.insert_document(
        AUDIO_USER_IDENTITIES_COLLECTION, identity_doc.model_dump(mode="json")
    )
    return user


def sign_session(user_id: int) -> str:
    secret = auth_settings.session_secret.strip()
    if not secret:
        raise RuntimeError("SESSION_SECRET 未配置")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(seconds=auth_settings.session_ttl_seconds),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_session(token: str) -> int:
    secret = auth_settings.session_secret.strip()
    if not secret:
        raise RuntimeError("SESSION_SECRET 未配置")
    payload = jwt.decode(token, secret, algorithms=["HS256"])
    sub = payload["sub"]
    if not isinstance(sub, str):
        raise ValueError("会话中的用户 ID 类型异常")
    user_id = int(sub)
    return user_id


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


def reject_gmail_email(email: str) -> None:
    if email.strip().lower().endswith("@gmail.com"):
        raise ValueError("请走谷歌邮箱登录")


def ensure_send_interval(mongo, email: str) -> None:
    cutoff = (
        datetime.utcnow() - timedelta(seconds=EMAIL_CODE_SEND_INTERVAL_SECONDS)
    ).isoformat()
    recent = mongo.count_documents(
        AUDIO_EMAIL_CODES_COLLECTION,
        {"email": email, "create_time": {"$gte": cutoff}},
    )
    if recent > 0:
        raise ValueError("发送过于频繁，请稍后再试")


def send_email_login_code(mongo, email: str) -> None:
    reject_gmail_email(email)
    ensure_send_interval(mongo, email)
    code = generate_email_code()
    save_email_code(mongo, email, code)
    deliver_email_code(email, code)


def login_with_email(mongo, email: str, code: str) -> AudioUser:
    reject_gmail_email(email)
    verify_email_code(mongo, email, code)
    return find_or_create_user(
        mongo,
        PROVIDER_EMAIL,
        email,
        email,
        None,
        None,
    )
