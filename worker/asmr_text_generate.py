import subprocess
from pathlib import Path

from services.fish_audio_service import FishAudioNotFoundError
from settings.worker import worker_settings

WORK_SUBDIR = "works"
ASMR_SUBDIR = "ASMR"
FFPROBE_BIN = "ffprobe"


class GenerateOutcome:
    def __init__(self, result_text: str):
        self.result_text = result_text


def _get_fish():
    from worker.runner import fish_service

    if fish_service is None:
        raise RuntimeError("Fish service 尚未初始化，无法生成音频")
    return fish_service


def _store_audio(user_id: int, task_id: str, subtask_id: str, audio: bytes) -> str:
    file_path = Path(worker_settings.audio_data_dir) / WORK_SUBDIR / str(user_id) / ASMR_SUBDIR / task_id / f"{subtask_id}.mp3"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(audio)
    return str(Path(WORK_SUBDIR) / str(user_id) / ASMR_SUBDIR / task_id / file_path.name)


def _probe_duration(file_path: Path) -> float:
    result = subprocess.run(
        [FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(file_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe 读取音频时长失败：{result.stderr.strip()}")
    return float(result.stdout.strip())


def run_generate(subtask: dict) -> GenerateOutcome:
    info = subtask["info"]
    reference_id = info["reference_id"]
    text = info["text"]
    if not reference_id:
        raise ValueError("片段角色不能为空")
    if not text:
        raise ValueError("片段文本不能为空")

    try:
        audio = _get_fish().synthesize(text, reference_id)
    except FishAudioNotFoundError as exc:
        raise ValueError(f"音色不可用：{reference_id}") from exc
    relative_path = _store_audio(subtask["user_id"], subtask["task_id"], subtask["subtask_id"], audio)
    file_path = Path(worker_settings.audio_data_dir) / relative_path
    duration = _probe_duration(file_path)
    limit = info["end_time"] - info["start_time"]
    if duration > limit:
        raise ValueError(f"音频真实时长 {duration:.2f}s 超过片段区间 {limit}s")
    return GenerateOutcome(result_text=relative_path)
