#!/bin/bash

set -e

DATASET_PATH="${1:-dataset_yolo}"
MODEL="${2:-yolov8s.pt}"
EPOCHS="${3:-50}"
IMGSZ="${4:-640}"
BATCH="${5:-16}"
DEVICE="${6:-}"

if [ ! -d "$DATASET_PATH" ]; then
    echo "Error: Dataset directory not found: $DATASET_PATH" >&2
    echo "Usage: train_yolo.sh <dataset_path> [model] [epochs] [imgsz] [batch] [device]" >&2
    echo "Example: train_yolo.sh dataset_yolo yolov8s.pt 50 640 16 0" >&2
    exit 1
fi

DATA_YAML="$DATASET_PATH/data.yaml"
if [ ! -f "$DATA_YAML" ]; then
    echo "Error: data.yaml not found in $DATASET_PATH" >&2
    exit 1
fi

echo "=========================================="
echo "YOLO TRAINING SCRIPT"
echo "=========================================="
echo "Dataset: $DATASET_PATH"
echo "Model: $MODEL"
echo "Epochs: $EPOCHS"
echo "Image Size: $IMGSZ"
echo "Batch: $BATCH"
if [ -n "$DEVICE" ]; then
    echo "Device: GPU $DEVICE"
    DEVICE_ARG="device=$DEVICE"
else
    echo "Device: CPU"
    DEVICE_ARG=""
fi
echo "=========================================="
echo ""

if [ -n "$DEVICE_ARG" ]; then
    yolo detect train \
        data="$DATA_YAML" \
        model="$MODEL" \
        epochs="$EPOCHS" \
        imgsz="$IMGSZ" \
        batch="$BATCH" \
        $DEVICE_ARG
else
    yolo detect train \
        data="$DATA_YAML" \
        model="$MODEL" \
        epochs="$EPOCHS" \
        imgsz="$IMGSZ" \
        batch="$BATCH"
fi

echo ""
echo "=========================================="
echo "Training completed!"
echo "=========================================="
echo "Best model: runs/detect/train/weights/best.pt"
echo "Last model: runs/detect/train/weights/last.pt"
echo ""
echo "To copy model to n8n:"
echo "  cp runs/detect/train/weights/best.pt ./models/best.pt"
echo "=========================================="
