from pathlib import Path

from agents.music import run_music
from agents.text import run_text
from models.schemas_task import TaskType
from settings.worker import worker_settings

SUBMUSIC_SUCCESS = "Submusic Success"
PERSON_SUCCESS = "Person Success"
ENVIRONMENT_SUCCESS = "Environment Success"


def save_submusic(subtask: dict, audio: bytes) -> str:
    output_dir = Path(worker_settings.music_data_dir) / subtask["task_id"] / "music"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{subtask['subtask_id']}.mp3"
    path.write_bytes(audio)
    return path.as_posix()


def save_text_audio(subtask: dict, audio: bytes) -> str:
    output_dir = Path(worker_settings.music_data_dir) / subtask["task_id"] / "text"
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


def run_person(subtask: dict) -> str:
    from worker.runner import fish_audio_service

    info = subtask["info"]
    audio = fish_audio_service.synthesize(info["type_prompt"], info["reference_id"])
    save_text_audio(subtask, audio)
    return PERSON_SUCCESS


def run_environment(subtask: dict) -> str:
    from worker.runner import elevenlabs_service

    info = subtask["info"]
    duration_seconds = (info["end_time"] - info["start_time"]) / info["polling_count"]
    loop = info["type"] == "environmental_sound"
    audio = elevenlabs_service.compose_sound(info["type_prompt"], duration_seconds, loop)
    save_text_audio(subtask, audio)
    return ENVIRONMENT_SUCCESS


EXECUTORS = {
    TaskType.ASMR_TEXT: run_text,
    TaskType.ASMR_BACKEND_MUSIC: run_music,
    TaskType.ASMR_BACKEND_SUBMUSIC: run_submusic,
    TaskType.ASMR_MUSIC_PERSON: run_person,
    TaskType.ASMR_MUSIC_ENVIRONMENT: run_environment,
}
