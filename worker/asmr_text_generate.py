from datetime import datetime
from pathlib import Path
from uuid import uuid4

from models.schemas_work import AUDIO_WORKS_COLLECTION, WORK_TYPE_TTS, AudioWork
from services.fish_audio_service import FishAudioNotFoundError
from settings.worker import worker_settings
from tools.agent_tools import _get_mongo, _load_character

WORK_SUBDIR = "works"


class GenerateOutcome:
    def __init__(self, result_text: str):
        self.result_text = result_text


def _get_fish():
    from worker.runner import fish_service

    if fish_service is None:
        raise RuntimeError("Fish service 尚未初始化，无法生成音频")
    return fish_service


def _store_work(mongo, user_id: int, reference_id: str, character: dict, text: str, audio: bytes) -> AudioWork:
    now = datetime.utcnow()
    work_id = uuid4().hex
    file_path = Path(worker_settings.audio_data_dir) / WORK_SUBDIR / str(user_id) / f"{work_id}.mp3"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(audio)
    work = AudioWork(
        work_id=work_id,
        user_id=user_id,
        work_type=WORK_TYPE_TTS,
        title=character["title"],
        reference_id=reference_id,
        cover_image=character["cover_image"],
        text=text,
        file_name=file_path.name,
        relative_path=str(Path(WORK_SUBDIR) / str(user_id) / file_path.name),
        file_size=len(audio),
        content_type="audio/mpeg",
        is_public=False,
        create_time=now,
        update_time=now,
        is_deleted=False,
    )
    mongo.insert_document(AUDIO_WORKS_COLLECTION, work.model_dump(mode="json"))
    return work


def run_generate(subtask: dict) -> GenerateOutcome:
    info = subtask["info"]
    reference_id = info["reference_id"]
    text = info["text"]
    if not reference_id:
        raise ValueError("片段角色不能为空")
    if not text:
        raise ValueError("片段文本不能为空")

    mongo = _get_mongo()
    character = _load_character(subtask["user_id"], reference_id)
    try:
        audio = _get_fish().synthesize(text, reference_id)
    except FishAudioNotFoundError as exc:
        raise ValueError(f"音色不可用：{reference_id}") from exc
    work = _store_work(mongo, subtask["user_id"], reference_id, character, text, audio)
    return GenerateOutcome(result_text=work.relative_path)
