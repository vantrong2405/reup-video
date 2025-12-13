# syntax=docker/dockerfile:1.6

ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-slim-bookworm

# =====================
# ENV
# =====================
ENV TZ=Asia/Ho_Chi_Minh \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    TORCH_HOME=/home/app/.cache/torch \
    HF_HOME=/home/app/.cache/huggingface \
    ULTRALYTICS_CACHE_DIR=/home/app/.cache/ultralytics \
    N8N_USER_FOLDER=/home/app/.n8n

# =====================
# System deps
# =====================
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    ffmpeg \
    rclone \
    yt-dlp \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# =====================
# n8n (PIN VERSION)
# =====================
ARG N8N_VERSION=1.48.1
RUN npm install -g n8n@${N8N_VERSION} semver

# =====================
# Python deps (PIN CORE)
# =====================
RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
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
      ultralytics==8.2.0 \
      torch==2.2.2+cpu \
      torchvision==0.17.2+cpu \
      --index-url https://download.pytorch.org/whl/cpu

# =====================
# User
# =====================
RUN useradd -m -u 1000 app && \
    mkdir -p /home/app/.cache /home/app/.n8n && \
    chown -R app:app /home/app

USER app
WORKDIR /home/app

# =====================
# Source
# =====================
COPY --chown=app:app ./src /home/app/src

EXPOSE 5678 8000

CMD ["n8n"]
