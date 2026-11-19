from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from settings.auth import auth_settings
from models.schemas_user import (
    AUDIO_COUNTERS_COLLECTION,
    AUDIO_USER_IDENTITIES_COLLECTION,
    AUDIO_USERS_COLLECTION,
    USER_ID_COUNTER_KEY,
    AudioCounter,
    AudioUser,
    UserIdentity,
)

SESSION_COOKIE_NAME = "session"

PROVIDER_GOOGLE = "google"


def verify_google_credential(credential: str) -> dict:
    client_id = auth_settings.google_client_id.strip()
    if not client_id:
        raise RuntimeError("GOOGLE_CLIENT_ID 未配置")
    return id_token.verify_oauth2_token(
        credential, google_requests.Request(), audience=client_id
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
    doc = mongo.find_one(AUDIO_USERS_COLLECTION, {"user_id": user_id})
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
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(seconds=auth_settings.session_ttl_seconds),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_session(token: str) -> int:
    secret = auth_settings.session_secret.strip()
    if not secret:
        raise RuntimeError("SESSION_SECRET 未配置")
    payload = jwt.decode(token, secret, algorithms=["HS256"])
    user_id = payload["sub"]
    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise ValueError("会话中的用户 ID 类型异常")
    return user_id
