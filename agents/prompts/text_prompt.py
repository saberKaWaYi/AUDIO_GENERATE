from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def get_text_system_prompt() -> str:
    return (Path(__file__).resolve().parent / "text_prompt.txt").read_text(encoding="utf-8")
