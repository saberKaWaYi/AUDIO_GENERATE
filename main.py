import argparse

import uvicorn


def run_web(host: str = "0.0.0.0", port: int = 8002, reload: bool = True):
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)


def run_worker():
    from worker.runner import run_worker as worker_main

    worker_main()


def main():
    parser = argparse.ArgumentParser(description="AUDIO_GENERATE")
    parser.add_argument("command", choices=["web", "worker"], help="运行模式: web(启动API服务) / worker(启动任务处理)")
    parser.add_argument("--host", default="0.0.0.0", help="Web服务主机地址")
    parser.add_argument("--port", type=int, default=8002, help="Web服务端口")
    parser.add_argument("--no-reload", action="store_true", help="禁用热重载")

    args = parser.parse_args()

    if args.command == "web":
        run_web(host=args.host, port=args.port, reload=not args.no_reload)
    elif args.command == "worker":
        run_worker()


if __name__ == "__main__":
    main()
