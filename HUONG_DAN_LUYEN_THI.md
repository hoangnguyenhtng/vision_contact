# Sườn luyện thi Vision trong 2 giờ

## 1. Cấu trúc phải nhớ

```text
main.py
    └── tạo Tk() và gọi AppActions

app_actions.py
    ├── cấu hình model
    ├── trạng thái chương trình
    ├── login, import, start, stop, reset
    ├── vòng lặp đọc video
    ├── YOLO + ByteTrack + logic đếm
    └── lưu bảng và export CSV

app_ui.py
    ├── tạo các Zone
    ├── tạo widget
    └── các hàm cập nhật ảnh, số đếm và bảng
```

Quy tắc tách code:

- `AppUI` không đọc video, không chạy YOLO và không tính bộ đếm.
- `AppActions` không tạo widget bằng `grid()` hoặc `pack()`.
- `main.py` không chứa logic.

## 2. Thứ tự viết bài trong 120 phút

### 0–10 phút: tạo sườn

1. Tạo `main.py`, `app_ui.py`, `app_actions.py`.
2. Viết constants: model path, classes, confidence, image size, line ratio.
3. Viết `AppActions.__init__()` và `AppUI.__init__()`.

### 10–35 phút: dựng giao diện

Viết theo thứ tự:

1. Camera Zone.
2. Login Zone.
3. Control Zone.
4. Counting Zone.
5. Table Zone.

Chạy thử ngay. Chưa cần model.

### 35–50 phút: login và trạng thái nút

1. Login `admin / 123`.
2. Chưa login chỉ cho Export.
3. Kiểm tra Start, Stop, Reset và Import được enable sau login.

### 50–65 phút: import và phát một video

1. `askopenfilename()`.
2. `cv2.VideoCapture()`.
3. Đọc frame bằng `read()`.
4. Dùng `root.after()` gọi frame tiếp theo.
5. Hiển thị frame bằng PIL/ImageTk.

### 65–85 phút: thêm model và tracking

1. Nạp model đúng một lần trong `load_model()`.
2. Gọi `model.track(..., persist=True)`.
3. Lấy `xyxy`, `cls`, `id`.
4. Vẽ kết quả bằng `result.plot()`.

### 85–100 phút: logic đếm

Nhớ đúng chuỗi:

```text
bounding box chạm vạch
        +
class ổn định 2 frame
        +
(track_id, class_name) chưa được đếm
        ↓
tăng class và tính lại Total
```

Điều kiện chạm vạch đứng:

```python
touches_line = x1 <= line_x <= x2
```

Total luôn được tính lại:

```python
total = sum(counts.values())
```

### 100–110 phút: hoàn thiện tác vụ

1. Start: reset số đếm, mở lại video từ đầu, bắt đầu timer.
2. Stop: hỏi Yes/No, dừng, giữ số và lưu một dòng.
3. Reset: hỏi Yes/No, đưa số về 0, không lưu dòng.
4. Video kết thúc: lưu một dòng và dừng.
5. Mỗi mốc 10: lưu một dòng, không reset Total.

### 110–120 phút: kiểm thử bắt buộc

1. `python -m py_compile app_ui.py app_actions.py main.py`.
2. Login sai và đúng.
3. Start hai lần.
4. Stop hai lần và kiểm tra hộp thoại.
5. Reset hai lần.
6. Kiểm tra `Total = green + red + yellow`.
7. Kiểm tra một vật thể không bị đếm lặp qua nhiều frame.
8. Kiểm tra Export khi chưa login.

## 3. Các hàm cần thuộc

### UI

```text
build_ui
build_camera_zone
build_login_zone
build_control_zone
build_counting_zone
build_table_zone
show_frame
show_counts
add_record
```

### Actions

```text
load_model
login
import_video
start / stop / reset
process_next_frame
detect_and_count
register_count
save_record
export_data
```

## 4. Cách tìm lỗi nhanh

- Không thấy video: kiểm tra `capture.isOpened()` và kết quả `read()`.
- Video quá chậm: giảm `MODEL_IMAGE_SIZE`, sau đó tăng `VIDEO_FRAME_STEP`.
- Đếm lặp: kiểm tra `counted_track_keys`.
- Miss khi đổi màu: khóa đếm phải là `(track_id, class_name)`.
- Đếm sai class: tăng `CLASS_CONFIRM_FRAMES` hoặc confidence.
- Bounding box chạm nhưng không đếm: in `x1`, `line_x`, `x2`, `track_id`.
- UI treo: không dùng vòng `while` vô hạn; phải dùng `root.after()`.
- Ảnh không hiện: phải giữ tham chiếu `self.camera_photo`.

## 5. Chiến lược luyện tập

1. Lần 1: chép lại code và hiểu từng hàm.
2. Lần 2: chỉ nhìn danh sách hàm, tự viết lại.
3. Lần 3: bấm giờ 120 phút như thi thật.
4. Sau mỗi lần, ghi lại ba lỗi làm mất nhiều thời gian nhất.
5. Chỉ thêm SQL Server hoặc widget cấu hình sau khi luồng video và bộ đếm đã chạy đúng.
