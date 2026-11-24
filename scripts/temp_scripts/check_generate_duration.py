import os
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import quote_plus

from pymongo import MongoClient

AUDIO_TASKS = "audio_tasks"
FFPROBE_BIN = "ffprobe"


def probe_duration(file_path: Path) -> float:
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
        raise RuntimeError(f"ffprobe 失败：{result.stderr.strip()}")
    return float(result.stdout.strip())


def main() -> None:
    host = os.environ["MONGODB_HOST"]
    port = int(os.environ["MONGODB_PORT"])
    username = os.environ["MONGODB_USERNAME"]
    password = os.environ["MONGODB_PASSWORD"]
    database = os.environ["MONGODB_DATABASE"]
    audio_data_dir = Path(os.environ.get("AUDIO_DATA_DIR", "data"))

    uri = f"mongodb://{quote_plus(username)}:{quote_plus(password)}@{host}:{port}"
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = client[database]
    docs = list(
        db[AUDIO_TASKS].find(
            {"type": "ASMR_TEXT_GENERATE", "is_deleted": False},
            {
                "subtask_id": 1,
                "task_id": 1,
                "user_id": 1,
                "status": 1,
                "info.start_time": 1,
                "info.end_time": 1,
                "result.result_text": 1,
            },
        )
    )
    client.close()

    status_count = Counter(doc["status"] for doc in docs)
    print("=== ASMR_TEXT_GENERATE 时长校验 ===")
    print(f"未删除总数：{len(docs)}")
    print("状态分布：" + ", ".join(f"{k}={v}" for k, v in sorted(status_count.items())))
    print(f"音频根目录：{audio_data_dir.resolve()}")

    exceeded = []
    unreadable = []
    checked = 0
    for doc in docs:
        if doc["status"] != "success":
            continue
        checked += 1
        info = doc["info"]
        limit = info["end_time"] - info["start_time"]
        relative_path = doc["result"]["result_text"]
        file_path = audio_data_dir / relative_path
        try:
            duration = probe_duration(file_path)
        except (OSError, RuntimeError, ValueError) as exc:
            unreadable.append((doc, limit, str(exc)))
            continue
        if duration > limit:
            exceeded.append((doc, limit, duration, relative_path))

    print(f"可校验(success)：{checked}")
    print(f"符合：{checked - len(exceeded) - len(unreadable)}")
    print(f"超时长：{len(exceeded)}")
    print(f"无法读取：{len(unreadable)}")

    if exceeded:
        print("\n=== 超时长（真实时长 > 区间，可用重新生成按钮重跑）===")
        for index, (doc, limit, duration, relative_path) in enumerate(exceeded, 1):
            print(
                f"[{index}] subtask_id={doc['subtask_id']} task_id={doc['task_id']} "
                f"user_id={doc['user_id']} 区间={limit}s 真实={duration:.2f}s 路径={relative_path}"
            )

    if unreadable:
        print("\n=== 无法读取（文件缺失 / ffprobe 异常）===")
        for index, (doc, limit, reason) in enumerate(unreadable, 1):
            print(
                f"[{index}] subtask_id={doc['subtask_id']} task_id={doc['task_id']} "
                f"user_id={doc['user_id']} 区间={limit}s 原因={reason}"
            )


if __name__ == "__main__":
    main()
