import csv
import os
import time
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import cv2
from ultralytics import YOLO

from app_ui import AppUI


# ==================== CẤU HÌNH NHANH ====================
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "Train_hoten" / "wine_colors" / "weights" / "best.pt"
CLASSES = ("green", "red", "yellow")

MODEL_CONFIDENCE = 0.70
MODEL_IMAGE_SIZE = 320
VIDEO_FRAME_STEP = 3
COUNTING_LINE_RATIO = 0.95
CLASS_CONFIRM_FRAMES = 2
# ========================================================


class AppActions:
    """Chứa trạng thái và toàn bộ xử lý của chương trình."""

    def __init__(self, root):
        self.root = root

        # Trạng thái hệ thống
        self.logged_in = False
        self.running = False
        self.after_id = None
        self.start_time = None
        self.first_detection_time = None
        self.just_reset = False

        # Bộ đếm
        self.counts = {name: 0 for name in CLASSES}
        self.total_count = 0

        # Video
        self.video_path = None
        self.capture = None
        self.source_fps = 30.0
        self.frame_delay_ms = 100

        # YOLO và tracking
        self.model = None
        self.counted_track_keys = set()
        self.track_class_states = {}
        self.tracking_frame_number = 0

        self.ui = AppUI(root, self, CLASSES)
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)
        self.load_model()

    # -------------------- MODEL --------------------
    def load_model(self):
        try:
            if not MODEL_PATH.is_file():
                raise FileNotFoundError(f"Không tìm thấy model:\n{MODEL_PATH}")

            self.model = YOLO(os.fspath(MODEL_PATH))
            names = self.model.names
            model_classes = tuple(names[index] for index in sorted(names))

            if model_classes != CLASSES:
                raise ValueError(
                    f"Class model {model_classes} không khớp {CLASSES}."
                )

            self.ui.status_var.set("Model đã sẵn sàng")
        except Exception as error:
            self.model = None
            self.ui.status_var.set("Không thể nạp model")
            messagebox.showerror("Model", str(error))

    def reset_tracking(self):
        """Reset ByteTrack và dữ liệu đếm ID cho một lần chạy mới."""
        predictor = getattr(self.model, "predictor", None)
        if predictor is not None and hasattr(predictor, "trackers"):
            for tracker in predictor.trackers:
                tracker.reset()

        self.counted_track_keys.clear()
        self.track_class_states.clear()
        self.tracking_frame_number = 0

    # -------------------- LOGIN --------------------
    def login(self):
        username = self.ui.username_var.get().strip()
        password = self.ui.password_var.get()

        if username == "admin" and password == "123":
            self.logged_in = True
            self.ui.set_logged_in(True)
            self.ui.status_var.set("Đăng nhập thành công")
        else:
            messagebox.showerror("Login", "Username hoặc Password không đúng.")

    # -------------------- VIDEO --------------------
    def import_video(self):
        if self.running:
            messagebox.showwarning("Import Video", "Hãy Stop trước khi đổi video.")
            return

        file_path = filedialog.askopenfilename(
            title="Chọn một video",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.m4v"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return

        video_path = Path(file_path).resolve()
        preview = cv2.VideoCapture(os.fspath(video_path))
        success, frame = preview.read() if preview.isOpened() else (False, None)
        fps = preview.get(cv2.CAP_PROP_FPS)
        preview.release()

        if not success:
            messagebox.showerror("Import Video", "Không thể đọc video đã chọn.")
            return

        self.video_path = video_path
        self.source_fps = fps if fps > 0 else 30.0
        self.update_frame_delay()

        self.draw_counting_line(frame)
        self.ui.show_frame(frame)
        self.ui.status_var.set("Đã nạp video. Nhấn Start để chạy.")

    def open_video(self):
        self.release_video()
        self.capture = cv2.VideoCapture(os.fspath(self.video_path))

        if not self.capture.isOpened():
            self.release_video()
            return False

        fps = self.capture.get(cv2.CAP_PROP_FPS)
        self.source_fps = fps if fps > 0 else 30.0
        self.update_frame_delay()
        self.reset_tracking()
        return True

    def update_frame_delay(self):
        # Ví dụ video 30 FPS, step 3: hiển thị 1 frame sau mỗi 100 ms.
        self.frame_delay_ms = max(
            1, round(1000 * VIDEO_FRAME_STEP / self.source_fps)
        )

    def process_next_frame(self):
        if not self.running or self.capture is None:
            return

        callback_start = time.perf_counter()
        success, frame = self.capture.read()
        if not success:
            self.finish_video()
            return

        try:
            display_frame = self.detect_and_count(frame)
        except Exception as error:
            self.running = False
            self.after_id = None
            self.release_video()
            self.ui.status_var.set("Lỗi khi chạy model")
            messagebox.showerror("YOLO", str(error))
            return

        # CPU không xử lý kịp mọi frame: bỏ bớt frame để giữ đúng tốc độ video.
        for _ in range(VIDEO_FRAME_STEP - 1):
            if not self.capture.grab():
                break

        self.ui.show_frame(display_frame)
        self.update_timer()

        processing_ms = (time.perf_counter() - callback_start) * 1000
        delay = max(1, self.frame_delay_ms - int(processing_ms))
        self.after_id = self.root.after(delay, self.process_next_frame)

    def release_video(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None

    # -------------------- NHẬN DIỆN VÀ ĐẾM --------------------
    def detect_and_count(self, frame):
        self.tracking_frame_number += 1
        result = self.model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=MODEL_CONFIDENCE,
            imgsz=MODEL_IMAGE_SIZE,
            verbose=False,
        )[0]

        display_frame = result.plot(line_width=2)
        boxes = result.boxes

        if boxes is not None and len(boxes) > 0:
            self.mark_first_detection()

        if boxes is not None and boxes.id is not None:
            line_x = int(frame.shape[1] * COUNTING_LINE_RATIO)
            coordinates = boxes.xyxy.cpu().tolist()
            class_ids = boxes.cls.int().cpu().tolist()
            track_ids = boxes.id.int().cpu().tolist()

            for box, class_id, track_id in zip(
                coordinates, class_ids, track_ids
            ):
                x1, _, x2, _ = box
                class_name = self.model.names[class_id]
                touches_line = x1 <= line_x <= x2
                class_is_stable = self.update_class_state(track_id, class_name)
                count_key = (track_id, class_name)

                if (
                    touches_line
                    and class_is_stable
                    and count_key not in self.counted_track_keys
                ):
                    self.register_count(class_name)
                    self.counted_track_keys.add(count_key)

        self.draw_counting_line(display_frame)
        return display_frame

    def update_class_state(self, track_id, class_name):
        """True khi cùng class xuất hiện đủ số frame liên tiếp."""
        state = self.track_class_states.get(track_id)
        is_next_frame = (
            state is not None
            and state["last_seen"] == self.tracking_frame_number - 1
        )

        if state is None or state["class_name"] != class_name or not is_next_frame:
            state = {
                "class_name": class_name,
                "frames": 1,
                "last_seen": self.tracking_frame_number,
            }
            self.track_class_states[track_id] = state
        else:
            state["frames"] += 1
            state["last_seen"] = self.tracking_frame_number

        return state["frames"] >= CLASS_CONFIRM_FRAMES

    def register_count(self, class_name):
        if not self.running:
            return

        self.counts[class_name] += 1
        self.total_count = sum(self.counts.values())
        self.ui.show_counts(self.counts, self.total_count)

        if self.total_count % 10 == 0:
            self.save_record("AUTO_10")

    def draw_counting_line(self, frame):
        height, width = frame.shape[:2]
        line_x = int(width * COUNTING_LINE_RATIO)
        color = (0, 255, 255)

        cv2.line(frame, (line_x, 0), (line_x, height), color, 3)
        cv2.putText(
            frame,
            "COUNTING LINE",
            (min(line_x + 10, max(10, width - 190)), 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
            cv2.LINE_AA,
        )

    # -------------------- BUTTON --------------------
    def start(self):
        if self.running:
            messagebox.showinfo("Start", "Hệ thống đang hoạt động.")
            return
        if self.model is None:
            messagebox.showerror("Start", "Model chưa được nạp.")
            return
        if self.video_path is None:
            messagebox.showwarning("Start", "Bạn chưa Import Video.")
            return

        self.clear_session()
        if not self.open_video():
            messagebox.showerror("Start", "Không thể mở video đã chọn.")
            return

        self.running = True
        self.just_reset = False
        self.start_time = datetime.now()
        self.ui.status_var.set("Hệ thống đang hoạt động")
        self.after_id = self.root.after(0, self.process_next_frame)

    def stop(self):
        if not self.running:
            messagebox.showinfo("Stop", "Hệ thống đang dừng hoạt động.")
            return
        if not messagebox.askyesno("Stop", "Bạn có muốn Stop hệ thống không?"):
            return

        self.running = False
        self.cancel_after()
        self.release_video()
        self.save_record("STOP")
        self.ui.status_var.set("Hệ thống đang dừng")

    def reset(self):
        if self.just_reset:
            messagebox.showinfo("Reset", "Hệ thống đã reset.")
            return
        if not messagebox.askyesno("Reset", "Bạn có muốn Reset hệ thống không?"):
            return

        self.clear_session()
        self.just_reset = True
        if self.running:
            self.start_time = datetime.now()
        self.ui.status_var.set("Đã reset, dữ liệu không được lưu")

    def finish_video(self):
        self.running = False
        self.after_id = None
        self.release_video()
        self.save_record("END_VIDEO")
        self.ui.status_var.set("Đã chạy xong video được chọn")

    def clear_session(self):
        self.counts = {name: 0 for name in CLASSES}
        self.total_count = 0
        self.first_detection_time = None
        self.counted_track_keys.clear()
        self.track_class_states.clear()
        self.tracking_frame_number = 0

        self.ui.show_counts(self.counts, self.total_count)
        self.ui.timer_var.set("Thời gian: 00:00:00")
        self.ui.first_detection_var.set("First detection: --")

    # -------------------- TIME VÀ DATA --------------------
    def mark_first_detection(self):
        if not self.running or self.first_detection_time is not None:
            return

        self.first_detection_time = datetime.now()
        elapsed = (self.first_detection_time - self.start_time).total_seconds()
        self.ui.first_detection_var.set(f"First detection: {elapsed:.2f} giây")

    def update_timer(self):
        elapsed_seconds = int((datetime.now() - self.start_time).total_seconds())
        hours = elapsed_seconds // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60
        self.ui.timer_var.set(
            f"Thời gian: {hours:02}:{minutes:02}:{seconds:02}"
        )

    def save_record(self, reason):
        values = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            *(self.counts[name] for name in CLASSES),
            self.total_count,
            reason,
        )
        self.ui.add_record(values)

        # Khi thi SQL Server: gọi insert_record_to_database(values) tại đây.

    def export_data(self):
        file_path = filedialog.asksaveasfilename(
            title="Chọn nơi lưu dữ liệu",
            defaultextension=".csv",
            filetypes=[("CSV file", "*.csv")],
        )
        if not file_path:
            return

        headings, rows = self.ui.get_table_data()
        with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(headings)
            writer.writerows(rows)

        messagebox.showinfo("Export Data", "Xuất dữ liệu thành công.")

    # -------------------- ĐÓNG APP --------------------
    def cancel_after(self):
        if self.after_id is not None:
            try:
                self.root.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

    def close_app(self):
        self.running = False
        self.cancel_after()
        self.release_video()
        self.root.destroy()
