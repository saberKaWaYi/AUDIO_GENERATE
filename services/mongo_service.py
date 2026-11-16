from typing import Optional
from urllib.parse import quote_plus

from pymongo import MongoClient

import logging

logger = logging.getLogger(__name__)


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

    def find_one(self, collection: str, query: dict) -> Optional[dict]:
        return self._collection(collection).find_one(query, {"_id": 0})

    def find_documents(
        self,
        collection: str,
        query: dict,
        sort: Optional[list] = None,
        skip: int = 0,
        limit: int = 0,
    ) -> list[dict]:
        cursor = self._collection(collection).find(query, {"_id": 0})
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def count_documents(self, collection: str, query: dict) -> int:
        return self._collection(collection).count_documents(query)

    def update_document(self, collection: str, query: dict, update: dict) -> int:
        result = self._collection(collection).update_one(query, update)
        logger.info("Updated %d document(s) in %s.%s", result.modified_count, self.database, collection)
        return result.modified_count

    def _db(self):
        if self._client is None:
            raise RuntimeError("MongoDB 未就绪")
        return self._client[self.database]

    def _collection(self, collection: str):
        return self._db()[collection]
