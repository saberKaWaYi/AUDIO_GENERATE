from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from settings.mongo import mongo_settings
from settings.web import web_settings
from logging_config import setup_logging

setup_logging("web")

from services.mongo_service import MongoService
from services.fish_audio_service import FishAudioService
from models.schemas_character import AUDIO_CHARACTERS_COLLECTION, AUDIO_CHARACTER_INDEXES
from models.schemas_task import AUDIO_TASKS_COLLECTION, AUDIO_TASK_INDEXES
from models.schemas_user import (
    AUDIO_COUNTERS_COLLECTION,
    AUDIO_EMAIL_CODES_COLLECTION,
    AUDIO_EMAIL_CODE_INDEXES,
    AUDIO_USER_IDENTITIES_COLLECTION,
    AUDIO_USER_IDENTITY_INDEXES,
    AUDIO_USERS_COLLECTION,
    AUDIO_USER_INDEXES,
    USER_ID_COUNTER_KEY,
    AudioCounter,
)
from app.api import character, task
from app.auth import auth

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo = MongoService(
        host=mongo_settings.mongodb_host,
        port=mongo_settings.mongodb_port,
        username=mongo_settings.mongodb_username,
        password=mongo_settings.mongodb_password,
        database=mongo_settings.mongodb_database,
    )
    app.state.mongo = mongo
    app.state.fish = FishAudioService()

    mongo.connect()
    mongo.create_collection(AUDIO_CHARACTERS_COLLECTION)
    for index in AUDIO_CHARACTER_INDEXES:
        mongo.create_index(AUDIO_CHARACTERS_COLLECTION, index["field"], index["unique"])

    mongo.create_collection(AUDIO_TASKS_COLLECTION)
    for index in AUDIO_TASK_INDEXES:
        mongo.create_index(AUDIO_TASKS_COLLECTION, index["field"], index["unique"])

    mongo.create_collection(AUDIO_USERS_COLLECTION)
    for index in AUDIO_USER_INDEXES:
        mongo.create_index(AUDIO_USERS_COLLECTION, index["field"], index["unique"])

    mongo.create_collection(AUDIO_USER_IDENTITIES_COLLECTION)
    for index in AUDIO_USER_IDENTITY_INDEXES:
        mongo.create_index(AUDIO_USER_IDENTITIES_COLLECTION, index["field"], index["unique"])

    mongo.create_collection(AUDIO_COUNTERS_COLLECTION)
    if mongo.find_one(AUDIO_COUNTERS_COLLECTION, {"key": USER_ID_COUNTER_KEY}) is None:
        counter = AudioCounter(key=USER_ID_COUNTER_KEY, value=0)
        mongo.insert_document(AUDIO_COUNTERS_COLLECTION, counter.model_dump(mode="json"))

    mongo.create_collection(AUDIO_EMAIL_CODES_COLLECTION)
    for index in AUDIO_EMAIL_CODE_INDEXES:
        mongo.create_index(AUDIO_EMAIL_CODES_COLLECTION, index["field"], index["unique"])

    yield

    mongo.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title=web_settings.web_name,
        version=web_settings.web_version,
        debug=web_settings.web_debug,
        lifespan=lifespan,
    )
    allowed_origins = [
        origin.strip()
        for origin in web_settings.allowed_origins.split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


app = create_app()
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(character.router, prefix="/api", tags=["character"])
app.include_router(task.router, prefix="/api", tags=["task"])
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
