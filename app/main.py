from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles

from settings.mongo import mongo_settings
from settings.web import web_settings
from logging_config import setup_logging

setup_logging("web")

from services.mongo_service import MongoService
from services.fish_audio_service import FishAudioService
from models.schemas_character import AUDIO_CHARACTERS_COLLECTION, AUDIO_CHARACTER_INDEXES
from models.schemas_task import AUDIO_TASKS_COLLECTION, AUDIO_TASK_INDEXES
from app.api import character, task

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

    yield

    mongo.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title=web_settings.web_name,
        version=web_settings.web_version,
        debug=web_settings.web_debug,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def verify_api_key(api_key: str = Depends(api_key_header)):
    expected = web_settings.web_api_key.strip()
    if not expected:
        raise HTTPException(status_code=503, detail="BACKEND_API_KEY 未配置")
    if not api_key or api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key


app = create_app()
app.include_router(
    character.router, prefix="/api", tags=["character"], dependencies=[Depends(verify_api_key)]
)
app.include_router(
    task.router, prefix="/api", tags=["task"], dependencies=[Depends(verify_api_key)]
)
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
