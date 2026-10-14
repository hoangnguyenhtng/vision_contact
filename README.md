# Vision Production Counting

Sườn ôn tập bài thi Vision: nhận diện và đếm chai theo màu bằng YOLO11, ByteTrack và Tkinter.

## Cài đặt trên Windows

```powershell
git clone https://github.com/hoangnguyenhtng/vision_contact.git
cd vision_contact
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Tài khoản demo:

```text
Username: admin
Password: 123
```

Chọn `Video_Wine_Bottle/yellow_1.mp4` để chạy thử.

## Cấu trúc cần học

```text
main.py          Chỉ khởi động Tkinter và AppActions
app_ui.py        Chỉ dựng/cập nhật giao diện
app_actions.py   Video, YOLO, tracking, đếm và nút bấm
```

Các thông số thường chỉnh nằm ở đầu `app_actions.py`:

```python
MODEL_CONFIDENCE = 0.70
MODEL_IMAGE_SIZE = 320
VIDEO_FRAME_STEP = 3
COUNTING_LINE_RATIO = 0.95
CLASS_CONFIRM_FRAMES = 2
```

Xem kế hoạch luyện 120 phút tại `HUONG_DAN_LUYEN_THI.md`.

## Chuẩn bị và train lại model

Bộ dữ liệu gán nhãn nằm trong:

```text
dataset_raw/images/bot
dataset_raw/labels/bot
dataset_raw/classes.txt
```

Tạo train/validation dataset rồi train:

```powershell
python prepare_yolo_dataset.py
python train_model.py
```

YOLO sẽ tự tải model nền `yolo11n.pt`. Checkpoint tốt nhất được ghi vào thư mục `Train_hoten/<ten_lan_train>/weights/best.pt`.

## Các file không đưa lên Git

- Toàn bộ video dung lượng lớn, chỉ giữ một video mẫu.
- `dataset_yolo` vì có thể tạo lại bằng script.
- `runs`, `Train_smoke`, cache Python và checkpoint `last.pt`.
- SQL Server chưa được tích hợp; vị trí nối database đã được đánh dấu trong `save_record()`.
