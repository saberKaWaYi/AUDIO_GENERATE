import subprocess
import tempfile
from pathlib import Path

FFMPEG_BIN = "ffmpeg"


class AudioMergeError(Exception):
    pass


def merge_segments(segments: list[tuple[int, str]], total_seconds: int) -> bytes:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "merged.mp3"
        command = [FFMPEG_BIN, "-hide_banner", "-loglevel", "error"]
        for _, file_path in segments:
            command.extend(["-i", file_path])
        filters = []
        labels = []
        for index, (start_time, _) in enumerate(segments):
            label = f"[a{index}]"
            filters.append(f"[{index}:a]adelay={start_time * 1000}{label}")
            labels.append(label)
        filters.append(
            "".join(labels)
            + f"amix=inputs={len(segments)}:duration=longest:normalize=0,apad,atrim=0:{total_seconds}[out]"
        )
        command.extend(
            [
                "-filter_complex",
                ";".join(filters),
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
