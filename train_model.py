"""Train YOLO11n cho ba lớp green, red, yellow.

Chạy mặc định:
    python train_model.py

Ví dụ training ngắn hơn:
    python train_model.py --epochs 20 --imgsz 512
"""

import argparse

from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(description="Train wine bottle detector")
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--name", default="wine_colors")
    return parser.parse_args()


def main():
    args = parse_args()
    model = YOLO("yolo11n.pt")

    model.train(
        data="dataset_yolo/data.yaml",
        epochs=args.epochs,
        patience=15,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=0,
        cache=True,
        seed=42,
        deterministic=True,
        project="Train_hoten",
        name=args.name,
        exist_ok=False,
        # Các lớp khác nhau chủ yếu ở màu, nên không đổi màu quá mạnh.
        hsv_h=0.005,
        hsv_s=0.30,
        hsv_v=0.20,
        degrees=2.0,
        translate=0.10,
        scale=0.30,
        fliplr=0.50,
        flipud=0.0,
        plots=True,
    )


if __name__ == "__main__":
    main()
