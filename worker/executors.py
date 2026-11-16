from pathlib import Path

from models.schemas_task import TaskType
from settings.worker import worker_settings


def run_music(subtask: dict, audio: bytes) -> str:
    output_dir = Path(worker_settings.music_data_dir) / subtask["task_id"] / "music"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{subtask['subtask_id']}.mp3"
    path.write_bytes(audio)
    return path.as_posix()


EXECUTORS = {
    TaskType.ASMR_BACKEND_MUSIC: run_music,
}
