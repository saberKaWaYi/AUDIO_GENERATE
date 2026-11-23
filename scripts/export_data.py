from pathlib import Path
import os
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

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "seed" / "account_data.json"


def main() -> None:
    host = os.environ["MONGODB_HOST"]
    port = int(os.environ["MONGODB_PORT"])
    username = os.environ["MONGODB_USERNAME"]
    password = os.environ["MONGODB_PASSWORD"]
    database = os.environ["MONGODB_DATABASE"]

    uri = f"mongodb://{quote_plus(username)}:{quote_plus(password)}@{host}:{port}"
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = client[database]

    payload = {}
    for name in COLLECTIONS:
        payload[name] = list(db[name].find({}))

    client.close()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json_util.dumps(payload, json_options=json_util.RELAXED_JSON_OPTIONS, indent=2),
        encoding="utf-8",
    )

    for name in COLLECTIONS:
        print(f"{name}: {len(payload[name])}")


if __name__ == "__main__":
    main()
