"""Trích ảnh từ một video để gán nhãn."""

from pathlib import Path

import cv2


VIDEO_PATH = "Video_Wine_Bottle/yellow_1.mp4"  # Sửa đường dẫn video tại đây
OUTPUT_DIR = Path("dataset_raw/images/bot")
FRAME_STEP = 15  # Cứ 15 frame lấy 1 ảnh


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(VIDEO_PATH)
    if not capture.isOpened():
        raise RuntimeError("Cannot open video")

    frame_index = 0
    saved_count = 0

    while True:
        success, frame = capture.read()
        if not success:
            break

        image_path = OUTPUT_DIR / f"frame_{frame_index:06d}.jpg"
        if cv2.imwrite(str(image_path), frame):
            saved_count += 1

        for _ in range(FRAME_STEP - 1):
            if not capture.grab():
                break

        frame_index += FRAME_STEP

    capture.release()
    print(f"Saved {saved_count} images to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
