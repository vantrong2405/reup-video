#!/usr/bin/env python3

import sys
from pathlib import Path
import yaml


def validate_dataset(dataset_path):
    dataset_path = Path(dataset_path)

    if not dataset_path.exists():
        print(f"Error: Dataset path not found: {dataset_path}", file=sys.stderr)
        sys.exit(1)

    data_yaml = dataset_path / "data.yaml"
    if not data_yaml.exists():
        print(f"Error: data.yaml not found in {dataset_path}", file=sys.stderr)
        sys.exit(1)

    with open(data_yaml, 'r') as f:
        config = yaml.safe_load(f)

    print("=" * 60)
    print("DATASET VALIDATION REPORT")
    print("=" * 60)

    errors = []
    warnings = []

    train_images = dataset_path / config.get('train', 'train/images')
    train_labels = dataset_path / train_images.parent / 'labels'
    valid_images = dataset_path / config.get('valid', 'valid/images')
    valid_labels = dataset_path / valid_images.parent / 'labels'

    print(f"\n1. Checking data.yaml...")
    print(f"   Path: {config.get('path', 'N/A')}")
    print(f"   Train: {config.get('train', 'N/A')}")
    print(f"   Valid: {config.get('valid', 'N/A')}")
    print(f"   Classes: {config.get('nc', 'N/A')}")
    print(f"   Names: {config.get('names', 'N/A')}")

    if config.get('nc') != 1:
        errors.append(f"Number of classes should be 1, got {config.get('nc')}")

    if 'names' not in config or 0 not in config['names']:
        errors.append("Class 'logo' (id=0) not found in names")
    elif config['names'].get(0) != 'logo':
        warnings.append(f"Class name at id=0 is '{config['names'].get(0)}', expected 'logo'")

    print(f"\n2. Checking training set...")
    if not train_images.exists():
        errors.append(f"Training images directory not found: {train_images}")
    else:
        train_img_files = list(train_images.glob('*.jpg')) + list(train_images.glob('*.png'))
        train_label_files = list(train_labels.glob('*.txt')) if train_labels.exists() else []

        print(f"   Images: {len(train_img_files)}")
        print(f"   Labels: {len(train_label_files)}")

        if len(train_img_files) == 0:
            errors.append("No training images found")
        elif len(train_img_files) < 50:
            warnings.append(f"Only {len(train_img_files)} training images (recommended: 100+)")

        if len(train_label_files) != len(train_img_files):
            errors.append(f"Mismatch: {len(train_img_files)} images but {len(train_label_files)} labels")

        missing_labels = []
        for img_file in train_img_files[:10]:
            label_file = train_labels / (img_file.stem + '.txt')
            if not label_file.exists():
                missing_labels.append(img_file.name)

        if missing_labels:
            errors.append(f"Missing labels for images: {', '.join(missing_labels[:5])}")

    print(f"\n3. Checking validation set...")
    if not valid_images.exists():
        errors.append(f"Validation images directory not found: {valid_images}")
    else:
        valid_img_files = list(valid_images.glob('*.jpg')) + list(valid_images.glob('*.png'))
        valid_label_files = list(valid_labels.glob('*.txt')) if valid_labels.exists() else []

        print(f"   Images: {len(valid_img_files)}")
        print(f"   Labels: {len(valid_label_files)}")

        if len(valid_img_files) == 0:
            errors.append("No validation images found")
        elif len(valid_img_files) < 10:
            warnings.append(f"Only {len(valid_img_files)} validation images (recommended: 20+)")

        if len(valid_label_files) != len(valid_img_files):
            errors.append(f"Mismatch: {len(valid_img_files)} images but {len(valid_label_files)} labels")

    print(f"\n4. Checking label format...")
    if train_labels.exists():
        sample_label = list(train_labels.glob('*.txt'))[0] if list(train_labels.glob('*.txt')) else None
        if sample_label:
            with open(sample_label, 'r') as f:
                lines = f.readlines()
                if lines:
                    parts = lines[0].strip().split()
                    if len(parts) != 5:
                        errors.append(f"Invalid label format in {sample_label.name}: expected 5 values, got {len(parts)}")
                    else:
                        try:
                            class_id, cx, cy, w, h = map(float, parts)
                            if not (0 <= cx <= 1 and 0 <= cy <= 1 and 0 <= w <= 1 and 0 <= h <= 1):
                                errors.append(f"Label values must be normalized (0-1) in {sample_label.name}")
                            if class_id != 0:
                                warnings.append(f"Class ID in {sample_label.name} is {int(class_id)}, expected 0")
                        except ValueError:
                            errors.append(f"Invalid label values in {sample_label.name}")

    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)

    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"   - {error}")

    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"   - {warning}")

    if not errors and not warnings:
        print("\n✅ Dataset is valid and ready for training!")
        return 0
    elif not errors:
        print("\n⚠️  Dataset has warnings but can be used for training")
        return 0
    else:
        print("\n❌ Dataset has errors. Please fix them before training.")
        return 1


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_dataset.py <dataset_path>", file=sys.stderr)
        print("Example: validate_dataset.py dataset_yolo", file=sys.stderr)
        sys.exit(1)

    dataset_path = sys.argv[1]
    exit_code = validate_dataset(dataset_path)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
