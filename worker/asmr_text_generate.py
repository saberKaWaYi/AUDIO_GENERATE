import subprocess
from pathlib import Path

from models.schemas_task import ASMRGenerateAudioResult
from services.fish_audio_service import FishAudioNotFoundError
from settings.worker import worker_settings

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


def _relative_audio_path(user_id: int, subtask_id: str) -> str:
    return str(Path(ASMR_SUBDIR) / str(user_id) / f"{subtask_id}.mp3")


def _audio_path(user_id: int, subtask_id: str) -> Path:
    return Path(worker_settings.audio_data_dir) / _relative_audio_path(user_id, subtask_id)


def _probe_duration_ms(file_path: Path) -> int:
    result = subprocess.run(
        [FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(file_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe 读取音频时长失败：{result.stderr.strip()}")
    return round(float(result.stdout.strip()) * 1000)


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

    file_path = _audio_path(subtask["user_id"], subtask["subtask_id"])
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(audio)
    duration_ms = _probe_duration_ms(file_path)
    payload = ASMRGenerateAudioResult(
        duration_ms=duration_ms,
        relative_path=_relative_audio_path(subtask["user_id"], subtask["subtask_id"]),
    )
    return GenerateOutcome(result_text=payload.model_dump_json())
