import os
from pathlib import Path
from urllib.parse import quote_plus

from bson import json_util
from pymongo import MongoClient

COLLECTIONS = (
    "audio_users",
    "audio_user_identities",
    "audio_counters",
    "audio_characters",
    "audio_tasks",
)

INPUT_PATH = Path(__file__).resolve().parent.parent / "seed" / "account_data.json"


def main() -> None:
    host = os.environ["MONGODB_HOST"]
    port = int(os.environ["MONGODB_PORT"])
    username = os.environ["MONGODB_USERNAME"]
    password = os.environ["MONGODB_PASSWORD"]
    database = os.environ["MONGODB_DATABASE"]

    raw = INPUT_PATH.read_text(encoding="utf-8")
    payload = json_util.loads(raw)

    uri = f"mongodb://{quote_plus(username)}:{quote_plus(password)}@{host}:{port}"
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = client[database]

    for name in COLLECTIONS:
        documents = payload[name]
        db[name].delete_many({})
        if documents:
            db[name].insert_many(documents)
        print(f"{name}: {len(documents)}")

    client.close()


if __name__ == "__main__":
    main()
