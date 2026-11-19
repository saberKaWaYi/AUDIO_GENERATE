import re
from datetime import datetime

from app.api.character_req import InsertCharacterRequest
from app.api.character_res import (
    CharacterResponse,
    CharacterListResponse,
    InsertCharacterResponse,
)
from models.schemas_character import (
    AUDIO_CHARACTERS_COLLECTION,
    AudioCharacter,
    FishModelEntity,
)
from services.fish_audio_service import FishAudioError


def insert_character(mongo, fish, user_id: int, payload: InsertCharacterRequest) -> InsertCharacterResponse:
    reference_id = payload.reference_id.strip()
    if not reference_id:
        raise ValueError("reference_id 不能为空")

    entity = FishModelEntity.model_validate(fish.get_model(reference_id))
    if not entity.title.strip():
        raise FishAudioError("上游角色 title 为空")
    if entity.reference_id != reference_id:
        raise FishAudioError("上游角色 ID 与请求不一致")

    now = datetime.utcnow()
    character = AudioCharacter(
        user_id=user_id,
        **entity.model_dump(),
        create_time=now,
        update_time=now,
        is_deleted=False,
    )
    document = character.model_dump(mode="json")
    query = {"user_id": user_id, "reference_id": reference_id, "is_deleted": False}

    created = mongo.find_one(AUDIO_CHARACTERS_COLLECTION, query) is None
    if created:
        mongo.insert_document(AUDIO_CHARACTERS_COLLECTION, document)
    else:
        fields = {
            key: value
            for key, value in document.items()
            if key not in ("user_id", "reference_id", "create_time")
        }
        mongo.update_document(AUDIO_CHARACTERS_COLLECTION, query, {"$set": fields})

    return InsertCharacterResponse(
        reference_id=reference_id,
        title=entity.title,
        created=created,
        update_time=now,
    )


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
    )

    return CharacterListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[CharacterResponse(**doc) for doc in docs],
    )
