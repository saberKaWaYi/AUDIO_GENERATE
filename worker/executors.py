from pathlib import Path

from agents.music import run_music
from agents.text import run_text
from models.schemas_task import TaskType
from settings.worker import worker_settings

SUBMUSIC_SUCCESS = "Submusic Success"


def save_submusic(subtask: dict, audio: bytes) -> str:
    output_dir = Path(worker_settings.music_data_dir) / subtask["task_id"] / "music"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{subtask['subtask_id']}.mp3"
    path.write_bytes(audio)
    return path.as_posix()


def run_submusic(subtask: dict) -> str:
    from worker.runner import elevenlabs_service

    info = subtask["info"]
    audio = elevenlabs_service.compose_music(info["prompt"], info["duration_seconds"] * 1000)
    save_submusic(subtask, audio)
    return SUBMUSIC_SUCCESS


EXECUTORS = {
    TaskType.ASMR_TEXT: run_text,
    TaskType.ASMR_BACKEND_MUSIC: run_music,
    TaskType.ASMR_BACKEND_SUBMUSIC: run_submusic,
}
