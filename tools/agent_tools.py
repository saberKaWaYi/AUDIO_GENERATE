import json

from models.schemas_character import AUDIO_CHARACTERS_COLLECTION
from services.mongo_service import MongoService

CHARACTER_FIELDS = ("reference_id", "title", "tags", "languages")


def _get_mongo() -> MongoService:
    from worker.runner import mongo_service

    if mongo_service is None:
        raise RuntimeError("Mongo service 尚未初始化，无法读取角色数据")
    return mongo_service


def _load_character(user_id: int, reference_id: str) -> dict:
    doc = _get_mongo().find_one(
        AUDIO_CHARACTERS_COLLECTION,
        {"user_id": user_id, "reference_id": reference_id, "is_deleted": False},
        fields=("title", "cover_image"),
    )
    if doc is None:
        raise ValueError(f"音色不存在或已删除：{reference_id}")
    return doc


def _load_characters(subtask: dict) -> list[dict]:
    reference_ids = subtask["info"]["reference_ids"]
    docs = _get_mongo().find_documents(
        AUDIO_CHARACTERS_COLLECTION,
        {
            "user_id": subtask["user_id"],
            "reference_id": {"$in": reference_ids},
            "is_deleted": False,
        },
        fields=CHARACTER_FIELDS,
    )
    if len(docs) != len(reference_ids):
        raise ValueError(
            f"角色数量不匹配：请求 {len(reference_ids)} 个，查到 {len(docs)} 个"
        )
    return [{field: doc[field] for field in CHARACTER_FIELDS} for doc in docs]


def build_user_content(subtask: dict, characters: list[dict]) -> str:
    payload = {
        "info": subtask["info"],
        "characters": characters,
    }
    return json.dumps(payload, ensure_ascii=False, default=str)
