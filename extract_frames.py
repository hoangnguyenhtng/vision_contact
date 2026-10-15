"""Chọn một video và trích frame để gán nhãn bằng LabelImg."""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog

import cv2


SAMPLE_FPS = 2  # Số ảnh lấy trong một giây video
DATASET_NAME = "bot"
IMAGE_ROOT = Path("dataset_raw/images")
LABEL_ROOT = Path("dataset_raw/labels")


def choose_video():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Chọn video để lấy ảnh",
        filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")],
    )
    root.destroy()
    return Path(file_path) if file_path else None


def main():
    video_path = choose_video()
    if video_path is None:
        return

    image_dir = IMAGE_ROOT / DATASET_NAME
    label_dir = LABEL_ROOT / DATASET_NAME
    image_dir.mkdir(parents=True, exist_ok=True)
    label_dir.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError("Không thể mở video.")

    video_fps = capture.get(cv2.CAP_PROP_FPS)
    video_fps = video_fps if video_fps > 0 else 30
    frame_step = max(1, round(video_fps / SAMPLE_FPS))

    frame_index = 0
    saved_count = 0

    while True:
        success, frame = capture.read()
        if not success:
            break

        if frame_index % frame_step == 0:
            file_name = f"{video_path.stem}_{frame_index:06d}.jpg"
            if cv2.imwrite(str(image_dir / file_name), frame):
                saved_count += 1

        frame_index += 1

    capture.release()
    print(f"Saved {saved_count} images to: {image_dir.resolve()}")
    print(f"Save YOLO labels to: {label_dir.resolve()}")


if __name__ == "__main__":
    main()
