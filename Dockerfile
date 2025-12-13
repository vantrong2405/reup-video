# syntax=docker/dockerfile:1.6

ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-slim-bookworm

ENV TZ=Asia/Ho_Chi_Minh \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    TORCH_HOME=/home/app/.cache/torch \
    HF_HOME=/home/app/.cache/huggingface \
    ULTRALYTICS_CACHE_DIR=/home/app/.cache/ultralytics

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    ffmpeg \
    rclone \
    yt-dlp \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN pip install --no-cache-dir \
    torch==2.2.2+cpu \
    torchvision==0.17.2+cpu \
    --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    celery \
    redis \
    numpy \
    scipy \
    pillow \
    pyyaml \
    requests \
    python-multipart \
    opencv-python-headless \
    ultralytics==8.2.0

RUN useradd -m -u 1000 app && \
    mkdir -p /home/app/.cache && \
    chown -R app:app /home/app

USER app
WORKDIR /home/app

COPY --chown=app:app ./src /home/app/src

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
