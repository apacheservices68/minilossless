---

### 🇻🇳 2. File `README_VN.md` (Tiếng Việt)

```markdown
# 🎬 Mini LosslessCut - Phiên bản Xử lý Video AI Chuyên Nghiệp

Ứng dụng xử lý, cắt video, đóng dấu watermark và xóa phông/làm mờ mặt bằng AI siêu tốc. Được xây dựng trên nền tảng **PyQt6**, **OpenCV**, **MediaPipe**, và **FFmpeg NVENC Hardware Acceleration**.

---

## 🚀 Tính năng Nổi bật

* **⚡ Hiệu năng Siêu Tốc (GPU NVENC + AI Optimization):**
  * Tự động thu nhỏ ảnh đầu vào AI về **320x320** giúp xử lý nhận diện siêu nhanh, sau đó quy đổi tọa độ ngược lại frame gốc.
  * Thuật toán Pixelate làm mờ mặt tối ưu bằng `cv2.resize` (Down/Up) ngốn **gần 0% CPU**.
  * Xuất video qua FFmpeg Pipe bằng GPU Nvidia (**`h264_nvenc` / `hevc_nvenc`**).
* **🤖 Xử lý AI Mặt & Nền:**
  * Tự động phát hiện và làm mờ khuôn mặt (Pixelate, Gaussian Blur, Box Blur, Đè ảnh thay thế).
  * Tự động tách nền và làm mờ hậu cảnh (Background Blur).
* **🎨 Hệ thống Watermark Đa dạng:**
  * Hỗ trợ chèn nhiều đoạn Text mẫu Canva (tùy chỉnh Font, Size, Góc xoay, Opacity).
  * Đồng bộ kích thước Preview và Render chuẩn pixel.
* **💾 Quản lý Trạng thái Dự án (JSON State):**
  * Tự động lưu và khôi phục toàn bộ tham số cài đặt vào file `<video_name>.json`.
  * Đọc JSON an toàn với cấu trúc Safe Fallback.
* **🧹 Dọn dẹp Workspace Sạch sẽ:**
  * Reset nhanh toàn bộ giao diện bằng phím tắt **`Ctrl + W`** (hoặc `Cmd + W`).

---

## 🛠️ Hướng dẫn Cài đặt & Chạy App

### Yêu cầu Hệ thống
* Python 3.10 trở lên
* Card đồ họa Nvidia (Hỗ trợ Driver NVENC) & FFmpeg

### Các bước Cài đặt:
```bash
# 1. Clone Repo
git clone [https://github.com/apacheservices68/minilossless.git](https://github.com/apacheservices68/minilossless.git)
cd minilossless

# 2. Tạo môi trường ảo
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. Cài đặt các thư viện
pip install -r requirements.txt

# 4. Chạy ứng dụng
python main.py