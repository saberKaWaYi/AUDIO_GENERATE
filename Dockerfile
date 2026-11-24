FROM python:3.12.3-slim AS base

WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

FROM base AS web
CMD ["python", "main.py", "web", "--host", "0.0.0.0", "--port", "8002", "--no-reload"]

FROM base AS worker
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
CMD ["python", "main.py", "worker"]
