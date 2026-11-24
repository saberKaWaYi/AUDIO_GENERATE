from typing import Optional
from urllib.parse import quote_plus

from pymongo import MongoClient, ReturnDocument

import logging

logger = logging.getLogger(__name__)


def _projection(fields: tuple[str, ...] | None) -> dict:
    if fields is None:
        return {"_id": 0}
    return {"_id": 0, **{field: 1 for field in fields}}


class MongoService:

    def __init__(
        self,
        host: str,
        port: int,
        username: str = "",
        password: str = "",
        database: str = "audio_generate",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self._client: Optional[MongoClient] = None

    def connect(self) -> None:
        if self.username:
            uri = f"mongodb://{quote_plus(self.username)}:{quote_plus(self.password)}@{self.host}:{self.port}"
        else:
            uri = f"mongodb://{self.host}:{self.port}"
        self._client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.ping()
        logger.info("MongoDB connected, host=%s, port=%s, database=%s", self.host, self.port, self.database)

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
            logger.info("MongoDB connection closed")

    def ping(self) -> None:
        self._db().command("ping")

    def create_collection(self, collection: str) -> None:
        db = self._db()
        if collection not in db.list_collection_names():
            db.create_collection(collection)
            logger.info("Created collection: %s.%s", self.database, collection)

    def create_index(self, collection: str, field: str | list, unique: bool = True) -> None:
        self._collection(collection).create_index(field, unique=unique)
        logger.info("Created index on %s.%s (unique=%s)", self.database, collection, unique)

    def insert_document(self, collection: str, document: dict) -> str:
        result = self._collection(collection).insert_one(document)
        logger.info("Inserted one document into %s.%s", self.database, collection)
        return str(result.inserted_id)

    def insert_documents(self, collection: str, documents: list[dict]) -> int:
        result = self._collection(collection).insert_many(documents)
        logger.info("Inserted %d documents into %s.%s", len(result.inserted_ids), self.database, collection)
        return len(result.inserted_ids)

    def find_one(self, collection: str, query: dict, fields: tuple[str, ...] | None = None) -> Optional[dict]:
        return self._collection(collection).find_one(query, _projection(fields))

    def find_documents(
        self,
        collection: str,
        query: dict,
        sort: Optional[list] = None,
        skip: int = 0,
        limit: int = 0,
        fields: tuple[str, ...] | None = None,
    ) -> list[dict]:
        cursor = self._collection(collection).find(query, _projection(fields))
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def find_one_and_update(
        self,
        collection: str,
        query: dict,
        update: dict,
        sort: Optional[list] = None,
    ) -> Optional[dict]:
        return self._collection(collection).find_one_and_update(
            query,
            update,
            projection={"_id": 0},
            sort=sort,
            return_document=ReturnDocument.BEFORE,
        )

    def count_documents(self, collection: str, query: dict) -> int:
        return self._collection(collection).count_documents(query)

    def update_document(self, collection: str, query: dict, update: dict) -> int:
        result = self._collection(collection).update_one(query, update)
        logger.info("Updated %d document(s) in %s.%s", result.modified_count, self.database, collection)
        return result.modified_count

    def update_documents(self, collection: str, query: dict, update: dict) -> int:
        result = self._collection(collection).update_many(query, update)
        logger.info("Updated %d document(s) in %s.%s", result.modified_count, self.database, collection)
        return result.modified_count

    def _db(self):
        if self._client is None:
            raise RuntimeError("MongoDB 未就绪")
        return self._client[self.database]

    def _collection(self, collection: str):
        return self._db()[collection]
