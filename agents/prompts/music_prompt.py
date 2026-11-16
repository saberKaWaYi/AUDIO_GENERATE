from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def get_music_system_prompt() -> str:
    return (Path(__file__).resolve().parent / "music_prompt.txt").read_text(encoding="utf-8")
