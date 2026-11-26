import subprocess
import tempfile
from pathlib import Path

FFMPEG_BIN = "ffmpeg"
FFPROBE_BIN = "ffprobe"


class AudioMergeError(Exception):
    pass


def probe_duration_ms(file_path: Path) -> int:
    result = subprocess.run(
        [
            FFPROBE_BIN,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(file_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe 读取音频时长失败：{result.stderr.strip()}")
    return round(float(result.stdout.strip()) * 1000)


def merge_segments(file_paths: list[str]) -> bytes:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "merged.mp3"
        command = [FFMPEG_BIN, "-hide_banner", "-loglevel", "error"]
        for file_path in file_paths:
            command.extend(["-i", file_path])
        inputs = "".join(f"[{index}:a]" for index in range(len(file_paths)))
        filter_complex = f"{inputs}concat=n={len(file_paths)}:v=0:a=1[out]"
        command.extend(
            [
                "-filter_complex",
                filter_complex,
                "-map",
                "[out]",
                "-c:a",
                "libmp3lame",
                "-y",
                str(output_path),
            ]
        )
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise AudioMergeError(f"ffmpeg 拼接失败：{result.stderr.strip()}")
        return output_path.read_bytes()
