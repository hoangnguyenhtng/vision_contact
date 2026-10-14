"""Tạo dataset YOLO train/val từ bộ ảnh và nhãn đã chuẩn hóa.

Vì dữ liệu hiện tại đến từ một video, script chia theo thời gian trong từng lớp:
80% frame đầu của mỗi lớp vào train, 20% frame cuối vào validation.
"""

import csv
import math
import shutil
import sys
from collections import defaultdict
from pathlib import Path


IMAGE_SOURCE = Path("dataset_raw/images/bot")
LABEL_SOURCE = Path("dataset_raw/labels/bot")
CLASSES_FILE = Path("dataset_raw/classes.txt")
OUTPUT_ROOT = Path("dataset_yolo")
VAL_RATIO = 0.20


def read_class_signature(label_path):
    class_ids = {
        int(line.split()[0])
        for line in label_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    if len(class_ids) != 1:
        raise ValueError(
            f"{label_path.name} phải chứa đúng một lớp, nhận được: {class_ids}"
        )
    return next(iter(class_ids))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if not IMAGE_SOURCE.is_dir():
        raise FileNotFoundError(f"Thiếu thư mục ảnh: {IMAGE_SOURCE}")
    if not LABEL_SOURCE.is_dir():
        raise FileNotFoundError(f"Thiếu thư mục nhãn: {LABEL_SOURCE}")

    class_names = CLASSES_FILE.read_text(encoding="utf-8").splitlines()
    grouped_images = defaultdict(list)

    for image_path in sorted(IMAGE_SOURCE.glob("*.jpg")):
        label_path = LABEL_SOURCE / f"{image_path.stem}.txt"
        if not label_path.exists():
            raise FileNotFoundError(f"Ảnh thiếu nhãn: {image_path.name}")
        class_id = read_class_signature(label_path)
        if not 0 <= class_id < len(class_names):
            raise ValueError(f"Class ID không hợp lệ trong {label_path.name}")
        grouped_images[class_id].append(image_path)

    expected_ids = set(range(len(class_names)))
    if set(grouped_images) != expected_ids:
        raise ValueError(
            f"Thiếu lớp. Mong đợi {expected_ids}, nhận được {set(grouped_images)}"
        )

    split_rows = []
    split_counts = {"train": 0, "val": 0}
    class_split_counts = defaultdict(lambda: {"train": 0, "val": 0})

    for class_id, image_paths in sorted(grouped_images.items()):
        val_count = max(1, math.ceil(len(image_paths) * VAL_RATIO))
        train_count = len(image_paths) - val_count

        for index, image_path in enumerate(image_paths):
            split = "train" if index < train_count else "val"
            label_path = LABEL_SOURCE / f"{image_path.stem}.txt"
            image_destination = OUTPUT_ROOT / "images" / split / image_path.name
            label_destination = OUTPUT_ROOT / "labels" / split / label_path.name

            image_destination.parent.mkdir(parents=True, exist_ok=True)
            label_destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(image_path, image_destination)
            shutil.copy2(label_path, label_destination)

            split_counts[split] += 1
            class_split_counts[class_id][split] += 1
            split_rows.append(
                {
                    "image": image_path.name,
                    "class_id": class_id,
                    "class_name": class_names[class_id],
                    "split": split,
                }
            )

    data_yaml = OUTPUT_ROOT / "data.yaml"
    absolute_root = OUTPUT_ROOT.resolve().as_posix()
    names_yaml = "\n".join(
        f"  {class_id}: {class_name}"
        for class_id, class_name in enumerate(class_names)
    )
    data_yaml.write_text(
        f"path: {absolute_root}\n"
        "train: images/train\n"
        "val: images/val\n\n"
        "names:\n"
        f"{names_yaml}\n",
        encoding="utf-8",
    )

    manifest_path = OUTPUT_ROOT / "split_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file, fieldnames=("image", "class_id", "class_name", "split")
        )
        writer.writeheader()
        writer.writerows(split_rows)

    print(f"Dataset: {OUTPUT_ROOT.resolve()}")
    print(f"Train  : {split_counts['train']} ảnh")
    print(f"Val    : {split_counts['val']} ảnh")
    for class_id, class_name in enumerate(class_names):
        counts = class_split_counts[class_id]
        print(
            f"  {class_id} {class_name}: "
            f"train={counts['train']}, val={counts['val']}"
        )
    print(f"YAML   : {data_yaml.resolve()}")


if __name__ == "__main__":
    main()
