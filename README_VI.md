# MiniLosslessCut

> Tiện ích xử lý video desktop hiệu năng cao, trọng lượng nhẹ được xây dựng bằng PyQt6, OpenCV và MediaPipe. Được thiết kế chuyên biệt cho việc cắt ghép nhanh, đóng dấu bản quyền chuẩn xác và che mặt bảo mật bằng AI.

---

## 🚀 Tính năng nổi bật

### 1. Cắt ghép Video & Điều khiển tối ưu
* **Cắt khung hình tốc độ cao:** Xử lý và chỉnh sửa đoạn video nhanh chóng với chi phí re-encode tối thiểu.
* **Phím tắt tiện lợi:** Nhấn ngay `Ctrl + W` (Windows/Linux) hoặc `Cmd + W` (macOS) để đóng hoặc reset video hiện tại, giúp chuyển đổi nhanh giữa các dự án.
* **Trợ giúp trực quan:** Hệ thống tooltip tích hợp sẵn giúp người dùng nắm bắt các phím tắt và thao tác một cách mượt mà.

### 2. Đóng dấu Văn bản Nâng cao (Watermark)
* **Đồng bộ hiển thị 1:1:** Tự động cân chỉnh DPI ($1.333\times$) và điều chỉnh bounding box giúp giao diện UI khớp hoàn toàn với video đầu ra.
* **Tùy chỉnh linh hoạt:** Quản lý toàn diện kích thước font, góc xoay, độ mờ (hỗ trợ cả dải $0-100$ và $0-1$) cùng tọa độ offset.
* **Độ ổn định cao:** Luồng render chuẩn hóa đảm bảo tính nhất quán trên nhiều tỷ lệ khung hình khác nhau (kể cả video dọc 9:16).

### 3. Pipeline Che mặt & Bảo mật bằng AI
* **Tích hợp MediaPipe:** Nhận diện khuôn mặt thời gian thực với độ chính xác cao.
* **Tối ưu Bounding Box thông minh:** Mở rộng biên độ phía trên ($+15\% - 20\%$) để che kín hoàn toàn phần trán và tóc mai mà không bị lệch tâm ngang.
* **Tùy chọn Hình dạng Che mặt (Shape Options):**
  * **Square (Mặc định):** Khung chữ nhật/vuông tiêu chuẩn.
  * **Circle / Ellipse:** Mặt nạ hình tròn/elip mềm mại ôm sát khuôn mặt.
  * **Replace Image:** Cho phép chọn ảnh cá nhân (PNG/JPG) để đè trực tiếp lên mặt.
* **Kiểu làm mờ & Tùy chỉnh độ mạnh:**
  * **Gaussian Blur:** Làm mờ mịn tự nhiên.
  * **Pixelate (Mosaic):** Hiệu ứng ô vuông pixel với kích thước khối tùy chỉnh.
  * **Box Blur:** Làm mờ dạng mảng phẳng siêu tốc.
  * **Solid Color (Blackout):** Che kín bằng khối màu đơn sắc.
  * **Điều chỉnh cường độ:** Tùy biến độ mạnh hiệu ứng trong khoảng $1 - 100$.

---

## 💻 Hướng dẫn Cài đặt

1. **Clone Repository:**
   ```bash
   git clone https://github.com/your-username/minilosslesscut.git
   cd minilosslesscut
   ```

2. **Cài đặt Thư viện phụ thuộc:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Cấu hình FFmpeg:**
   Đảm bảo tệp nhị phân tương ứng (`ffmpeg.exe` cho Windows hoặc `ffmpeg` cho macOS/Linux) nằm trong PATH hệ thống hoặc cấu trúc thư mục `bin/` của dự án.

---

## 🕹️ Hướng dẫn Sử dụng Nhanh

1. **Khởi động ứng dụng:**
   ```bash
   python main.py
   ```
2. **Mở Video:** Chọn tệp video cần xử lý thông qua giao diện chính.
3. **Áp dụng Hiệu ứng:** 
   * Truy cập tab Watermark để cấu hình chữ ký.
   * Chuyển sang tab Face Blur, chọn hình dạng, kiểu làm mờ và mức độ mong muốn.
4. **Quản lý không gian làm việc:** Nhấn `Ctrl + W` bất cứ lúc nào để đóng video hiện tại và làm sạch workspace cho video tiếp theo.
