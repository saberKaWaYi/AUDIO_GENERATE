import math
import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.api.character_req import InsertCharacterRequest
from app.api.character_res import (
    CharacterResponse,
    CharacterListResponse,
    InsertCharacterResponse,
    CreateCharacterResponse,
)
from models.schemas_character import (
    AUDIO_CHARACTERS_COLLECTION,
    AudioCharacter,
    FishModelEntity,
)
from models.schemas_work import AUDIO_WORKS_COLLECTION, WORK_TYPE_TTS, AudioWork
from services.fish_audio_service import FishAudioError, FishAudioNotFoundError
from settings.worker import worker_settings

MIN_DURATION_SECONDS = 30.0
MAX_DURATION_SECONDS = 180.0
MAX_TTS_TEXT_LENGTH = 500
WORK_SUBDIR = "works"
AUDIO_SUFFIXES = (".mp3",)
AUDIO_CONTENT_TYPES = ("audio/mpeg", "audio/mp3", "application/octet-stream")
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")
IMAGE_CONTENT_TYPES = ("image/jpeg", "image/png", "application/octet-stream")


def _match_suffix(name: str, suffixes: tuple[str, ...]) -> bool:
    lowered = name.lower()
    return any(lowered.endswith(suffix) for suffix in suffixes)


def _validate_uploads(
    voices: list[tuple[str, bytes, str]],
    cover_image: tuple[str, bytes, str] | None,
    duration_seconds: float,
) -> None:
    if not math.isfinite(duration_seconds):
        raise ValueError("总时长必须是有限数值")
    if not MIN_DURATION_SECONDS <= duration_seconds <= MAX_DURATION_SECONDS:
        raise ValueError("参考音频总时长必须在 30 到 180 秒之间")
    for name, content, content_type in voices:
        if not content:
            raise ValueError(f"参考音频内容为空：{name}")
        if not _match_suffix(name, AUDIO_SUFFIXES):
            raise ValueError(f"参考音频仅支持 MP3：{name}")
        if content_type not in AUDIO_CONTENT_TYPES:
            raise ValueError(f"参考音频类型不支持：{name}")
    if cover_image is not None:
        name, content, content_type = cover_image
        if not content:
            raise ValueError(f"封面照片内容为空：{name}")
        if not _match_suffix(name, IMAGE_SUFFIXES):
            raise ValueError(f"封面照片仅支持 JPG/PNG：{name}")
        if content_type not in IMAGE_CONTENT_TYPES:
            raise ValueError(f"封面照片类型不支持：{name}")


def _upsert_character(mongo, user_id: int, entity: FishModelEntity) -> tuple[bool, datetime]:
    now = datetime.utcnow()
    character = AudioCharacter(
        user_id=user_id,
        **entity.model_dump(),
        create_time=now,
        update_time=now,
        is_deleted=False,
    )
    document = character.model_dump(mode="json")
    query = {"user_id": user_id, "reference_id": entity.reference_id, "is_deleted": False}

    created = mongo.find_one(AUDIO_CHARACTERS_COLLECTION, query, fields=("reference_id",)) is None
    if created:
        mongo.insert_document(AUDIO_CHARACTERS_COLLECTION, document)
    else:
        fields = {
            key: value
            for key, value in document.items()
            if key not in ("user_id", "reference_id", "create_time")
        }
        mongo.update_document(AUDIO_CHARACTERS_COLLECTION, query, {"$set": fields})

    return created, now


def insert_character(mongo, fish, user_id: int, payload: InsertCharacterRequest) -> InsertCharacterResponse:
    reference_id = payload.reference_id.strip()
    if not reference_id:
        raise ValueError("reference_id 不能为空")

    entity = FishModelEntity.model_validate(fish.get_model(reference_id))
    if not entity.title.strip():
        raise FishAudioError("上游角色 title 为空")
    if entity.reference_id != reference_id:
        raise FishAudioError("上游角色 ID 与请求不一致")

    created, now = _upsert_character(mongo, user_id, entity)

    return InsertCharacterResponse(
        reference_id=reference_id,
        title=entity.title,
        created=created,
        update_time=now,
    )


def create_character(
    mongo,
    fish,
    user_id: int,
    title: str,
    voices: list[tuple[str, bytes, str]],
    cover_image: tuple[str, bytes, str] | None,
    description: str | None,
    duration_seconds: float,
) -> CreateCharacterResponse:
    title = title.strip()
    if not title:
        raise ValueError("title 不能为空")
    if not voices:
        raise ValueError("至少需要 1 个参考音频")
    if len(voices) > 20:
        raise ValueError("参考音频最多 20 个")
    _validate_uploads(voices, cover_image, duration_seconds)

    entity = FishModelEntity.model_validate(
        fish.create_model(
            title=title,
            voices=voices,
            cover_image=cover_image,
            description=description,
        )
    )
    if not entity.title.strip():
        raise FishAudioError("上游角色 title 为空")

    created, now = _upsert_character(mongo, user_id, entity)

    return CreateCharacterResponse(
        reference_id=entity.reference_id,
        title=entity.title,
        state=entity.state,
        visibility=entity.visibility,
        cover_image=entity.cover_image,
        created=created,
        update_time=now,
    )


def delete_character(mongo, user_id: int, reference_id: str) -> bool:
    reference_id = reference_id.strip()
    if not reference_id:
        raise ValueError("reference_id 不能为空")
    query = {"user_id": user_id, "reference_id": reference_id, "is_deleted": False}
    return mongo.update_document(AUDIO_CHARACTERS_COLLECTION, query, {"$set": {"is_deleted": True}}) > 0


def list_characters(
    mongo,
    user_id: int,
    page: int,
    page_size: int,
    keyword: str | None,
    tag: str | None,
    state: str | None,
    reference_id: str | None,
) -> CharacterListResponse:
    query: dict = {"user_id": user_id, "is_deleted": False}

    if keyword and keyword.strip():
        query["title"] = {"$regex": re.escape(keyword.strip()), "$options": "i"}
    if tag and tag.strip():
        query["tags"] = tag.strip()
    if state and state.strip():
        query["state"] = state.strip()
    if reference_id and reference_id.strip():
        query["reference_id"] = reference_id.strip()

    total = mongo.count_documents(AUDIO_CHARACTERS_COLLECTION, query)
    docs = mongo.find_documents(
        AUDIO_CHARACTERS_COLLECTION,
        query,
        sort=[("update_time", -1)],
        skip=(page - 1) * page_size,
        limit=page_size,
        fields=(
            "user_id",
            "reference_id",
            "title",
            "description",
            "cover_image",
            "type",
            "train_mode",
            "state",
            "visibility",
            "tags",
            "languages",
            "default_text",
            "source",
            "created_at",
            "updated_at",
            "create_time",
            "update_time",
            "is_public",
        ),
    )

    return CharacterListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[CharacterResponse(**doc) for doc in docs],
    )


def _work_file_path(user_id: int, work_id: str) -> Path:
    return Path(worker_settings.audio_data_dir) / WORK_SUBDIR / str(user_id) / f"{work_id}.mp3"


def _store_work(mongo, user_id: int, reference_id: str, cover_image: str, title: str, text: str, audio: bytes, is_public: bool) -> AudioWork:
    now = datetime.utcnow()
    work_id = uuid4().hex
    file_path = _work_file_path(user_id, work_id)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(audio)
    work = AudioWork(
        work_id=work_id,
        user_id=user_id,
        work_type=WORK_TYPE_TTS,
        title=title,
        reference_id=reference_id,
        cover_image=cover_image,
        text=text,
        file_name=file_path.name,
        relative_path=str(Path(WORK_SUBDIR) / str(user_id) / file_path.name),
        file_size=len(audio),
        content_type="audio/mpeg",
        is_public=is_public,
        create_time=now,
        update_time=now,
        is_deleted=False,
    )
    mongo.insert_document(AUDIO_WORKS_COLLECTION, work.model_dump(mode="json"))
    return work


def synthesize_tts(mongo, fish, user_id: int, reference_id: str, text: str, is_public: bool) -> bytes:
    reference_id = reference_id.strip()
    text = text.strip()
    if not reference_id:
        raise ValueError("音色不能为空")
    if not text:
        raise ValueError("文本内容不能为空")
    if len(text) > MAX_TTS_TEXT_LENGTH:
        raise ValueError(f"文本不能超过 {MAX_TTS_TEXT_LENGTH} 字")

    character = mongo.find_one(
        AUDIO_CHARACTERS_COLLECTION,
        {"user_id": user_id, "reference_id": reference_id, "is_deleted": False},
        fields=("cover_image", "title"),
    )
    if character is None:
        raise FishAudioNotFoundError("音色不存在或已删除")

    try:
        audio = fish.synthesize(text, reference_id)
    except FishAudioNotFoundError as e:
        raise FishAudioNotFoundError("音色不可用") from e

    _store_work(mongo, user_id, reference_id, character["cover_image"], character["title"], text, audio, is_public)
    return audio


def list_works(mongo, query: dict) -> list[dict]:
    return mongo.find_documents(
        AUDIO_WORKS_COLLECTION,
        query,
        sort=[("create_time", -1)],
        fields=("work_id", "work_type", "title", "cover_image", "text", "file_size", "is_public", "create_time"),
    )


def set_work_public(mongo, user_id: int, work_id: str, is_public: bool) -> bool:
    return mongo.update_document(
        AUDIO_WORKS_COLLECTION,
        {"work_id": work_id, "user_id": user_id, "is_deleted": False},
        {"$set": {"is_public": is_public, "update_time": datetime.utcnow()}},
    ) > 0


def delete_work(mongo, user_id: int, work_id: str) -> bool:
    query = {"work_id": work_id, "user_id": user_id, "is_deleted": False}
    doc = mongo.find_one(AUDIO_WORKS_COLLECTION, query, fields=("relative_path",))
    if doc is None:
        return False
    file_path = Path(worker_settings.audio_data_dir) / doc["relative_path"]
    file_path.unlink(missing_ok=True)
    mongo.update_document(
        AUDIO_WORKS_COLLECTION,
        query,
        {"$set": {"is_deleted": True, "update_time": datetime.utcnow()}},
    )
    return True


def get_work_audio(mongo, work_id: str, user_id: int, public_only: bool) -> tuple[str, bytes] | None:
    query = {"work_id": work_id, "is_deleted": False}
    if public_only:
        query["is_public"] = True
    else:
        query["user_id"] = user_id
    doc = mongo.find_one(AUDIO_WORKS_COLLECTION, query, fields=("file_name", "relative_path"))
    if doc is None:
        return None
    file_path = Path(worker_settings.audio_data_dir) / doc["relative_path"]
    return doc["file_name"], file_path.read_bytes()
