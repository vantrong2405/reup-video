FROM node:20-bookworm

USER root

RUN apt-get update && \
    apt-get install -y \
        python3 python3-dev python3-pip python3-venv \
        ffmpeg rclone yt-dlp \
        build-essential cmake \
        libjpeg-dev libpng-dev libwebp-dev libtiff-dev \
        libopenblas-dev liblapack-dev \
        git && \
    npm install -g n8n && \
    pip3 install --no-cache-dir --break-system-packages --upgrade pip && \
    pip3 install --no-cache-dir --break-system-packages \
        numpy \
        opencv-python-headless \
        ultralytics \
        torch \
        torchvision \
        pillow \
        requests \
        matplotlib \
        scipy \
        pyyaml && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

USER node

ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV N8N_USER_FOLDER=/home/node/.n8n

WORKDIR /home/node
