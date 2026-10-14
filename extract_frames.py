"""Trích frame từ các video để gán nhãn bằng LabelImg.

Ví dụ:
    python extract_frames.py
    python extract_frames.py --sample-fps 2
    python extract_frames.py --input Video_Wine_Bottle --output dataset_raw/images
"""

import argparse
import re
import sys
from pathlib import Path

import cv2


VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".m4v"}
DEFAULT_EXCLUDES = ("labeled", "annotated", "predict", "result", "copy")


def natural_sort_key(path):
    """Sắp xếp video_2 trước video_10."""
    return [
        int(part) if part.isdigit() else part.casefold()
        for part in re.split(r"(\d+)", path.name)
    ]


def safe_folder_name(name):
    """Thay các ký tự không hợp lệ trong tên thư mục Windows."""
    return re.sub(r'[<>:"/\\|?*]+', "_", name).strip()


def save_jpeg(path, frame, quality):
    """Lưu được cả đường dẫn có ký tự Unicode trên Windows."""
    success, encoded = cv2.imencode(
        ".jpg",
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, quality],
    )
    if not success:
        return False

    encoded.tofile(str(path))
    return True


def extract_video(
    video_path,
    output_root,
    sample_fps,
    start_seconds,
    end_seconds,
    jpeg_quality,
    min_sharpness,
):
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        return {"saved": 0, "existing": 0, "blurred": 0, "error": "cannot open"}

    source_fps = capture.get(cv2.CAP_PROP_FPS)
    if source_fps <= 0:
        source_fps = 30.0

    frame_step = max(1, round(source_fps / sample_fps))
    start_frame = max(0, round(start_seconds * source_fps))
    end_frame = None
    if end_seconds is not None:
        end_frame = round(end_seconds * source_fps)

    capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    video_output = output_root / safe_folder_name(video_path.stem)
    video_output.mkdir(parents=True, exist_ok=True)

    saved = 0
    existing = 0
    blurred = 0
    frame_index = start_frame

    while True:
        success, frame = capture.read()
        if not success:
            break
        if end_frame is not None and frame_index >= end_frame:
            break

        relative_index = frame_index - start_frame
        if relative_index % frame_step == 0:
            if min_sharpness > 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
                if sharpness < min_sharpness:
                    blurred += 1
                    frame_index += 1
                    continue

            image_name = f"{video_path.stem}_f{frame_index:07d}.jpg"
            image_path = video_output / image_name

            # Không ghi đè nếu chạy script nhiều lần.
            if image_path.exists():
                existing += 1
            elif save_jpeg(image_path, frame, jpeg_quality):
                saved += 1

        frame_index += 1

    capture.release()
    return {"saved": saved, "existing": existing, "blurred": blurred, "error": None}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract video frames for YOLO labeling with LabelImg."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("Video_Wine_Bottle"),
        help="Thư mục chứa video.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dataset_raw/images"),
        help="Thư mục lưu frame ảnh.",
    )
    parser.add_argument(
        "--labels-output",
        type=Path,
        default=None,
        help="Thư mục lưu nhãn. Mặc định: thư mục labels nằm cạnh images.",
    )
    parser.add_argument(
        "--sample-fps",
        type=float,
        default=1.0,
        help="Số frame cần lấy trong một giây video. Mặc định: 1.",
    )
    parser.add_argument(
        "--start",
        type=float,
        default=0.0,
        help="Bỏ qua số giây đầu mỗi video.",
    )
    parser.add_argument(
        "--end",
        type=float,
        default=None,
        help="Dừng lấy frame tại giây này của mỗi video.",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=95,
        help="Chất lượng JPEG từ 1 đến 100. Mặc định: 95.",
    )
    parser.add_argument(
        "--min-sharpness",
        type=float,
        default=0.0,
        help="Bỏ ảnh quá mờ. 0 = tắt lọc; có thể thử 50-100.",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=list(DEFAULT_EXCLUDES),
        help="Bỏ video nếu tên chứa một trong các từ này.",
    )
    return parser.parse_args()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args()
    if args.sample_fps <= 0:
        raise ValueError("--sample-fps phải lớn hơn 0")
    if not 1 <= args.quality <= 100:
        raise ValueError("--quality phải nằm trong khoảng 1-100")
    if not args.input.is_dir():
        raise FileNotFoundError(f"Không tìm thấy thư mục video: {args.input}")

    excluded_words = tuple(word.casefold() for word in args.exclude)
    all_videos = sorted(
        (
            path
            for path in args.input.iterdir()
            if path.is_file() and path.suffix.casefold() in VIDEO_EXTENSIONS
        ),
        key=natural_sort_key,
    )
    videos = [
        path
        for path in all_videos
        if not any(word in path.name.casefold() for word in excluded_words)
    ]
    skipped_names = [path.name for path in all_videos if path not in videos]

    if not videos:
        raise RuntimeError("Không tìm thấy video phù hợp để trích frame.")

    labels_output = args.labels_output or (args.output.parent / "labels")
    args.output.mkdir(parents=True, exist_ok=True)
    labels_output.mkdir(parents=True, exist_ok=True)
    for video_path in videos:
        (labels_output / safe_folder_name(video_path.stem)).mkdir(
            parents=True, exist_ok=True
        )

    print(f"Input : {args.input.resolve()}")
    print(f"Images: {args.output.resolve()}")
    print(f"Labels: {labels_output.resolve()}")
    print(f"Sample: {args.sample_fps:g} frame/giây")
    if skipped_names:
        print("Bỏ qua:", ", ".join(skipped_names))
    print()

    total_saved = 0
    total_existing = 0
    total_blurred = 0

    for index, video_path in enumerate(videos, start=1):
        result = extract_video(
            video_path=video_path,
            output_root=args.output,
            sample_fps=args.sample_fps,
            start_seconds=args.start,
            end_seconds=args.end,
            jpeg_quality=args.quality,
            min_sharpness=args.min_sharpness,
        )

        if result["error"]:
            print(f"[{index}/{len(videos)}] LỖI {video_path.name}: {result['error']}")
            continue

        total_saved += result["saved"]
        total_existing += result["existing"]
        total_blurred += result["blurred"]
        print(
            f"[{index}/{len(videos)}] {video_path.name}: "
            f"mới={result['saved']}, đã có={result['existing']}, "
            f"bỏ mờ={result['blurred']}"
        )

    print()
    print(f"Hoàn tất: {total_saved} ảnh mới")
    print(f"Đã tồn tại: {total_existing} ảnh")
    print(f"Bỏ vì mờ: {total_blurred} ảnh")


if __name__ == "__main__":
    main()
