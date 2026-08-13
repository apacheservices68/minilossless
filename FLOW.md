# Phân Tích Luồng Thực Thi Tính Năng Cắt/Export Video

Đây là tài liệu phân tích chi tiết về quy trình thực thi (execution flow) của tính năng Cắt/Export trong dự án, từ giao diện người dùng đến lệnh FFmpeg cuối cùng.

## Sơ Đồ Luồng Thực Thi (Mermaid)

```graph TD
    subgraph UI Layer
        A["main_window.py: export_segments_action()"]
    end

    subgraph Service Layer
        B{"is_smart_cut?"}
        C["smartcut_service.py: SmartCutWorker.run()"]
        D["ffmpeg_service.py: cut_video()"]
        E["exact_cut_service.py: exact_cut()"]
        F["ffmpeg_service.py: get_ffmpeg_cut_cmd()"]
    end

    subgraph Execution
        G["Thread: SmartCutWorker"]
        H["FFmpeg Command (Re-encode for Smart Cut)"]
        I["FFmpeg Command (Lossless Cut)"]
    end

    A --> B
    B -- True --> C
    C --> G
    G -- calls --> D
    B -- False --> D
    D -- is_smart_cut=true --> E
    D -- is_smart_cut=false --> F
    E --> H
    F --> I
```

## Chi Tiết Luồng Thực Thi

Dưới đây là các bước chi tiết khi người dùng nhấn nút "Export".

### Kịch bản 1: `is_smart_cut = true` (Cắt chính xác)

Đây là luồng thực thi khi người dùng chọn chế độ "Smart Cut", ưu tiên độ chính xác của điểm cắt bằng cách re-encode lại video.

1.  **`app/ui/main_window.py` (Hàm `export_segments_action`)**
    *   Người dùng nhấn nút "Export", hàm `export_segments_action` được gọi.
    *   Hàm kiểm tra thấy `is_smart_cut` là `True` (dòng 343).
    *   Một đối tượng `SmartCutWorker` (từ `app/services/smartcut_service.py`) được khởi tạo. Đây là một `QThread` để chạy tác vụ nền, tránh làm treo giao diện.
    *   Hàm gọi `smart_worker.start()` và ngay lập tức `return` (dòng 356), kết thúc xử lý ở UI thread.

2.  **`app/services/smartcut_service.py` (Lớp `SmartCutWorker`, hàm `run`)**
    *   Hàm `run` được thực thi trong một thread riêng.
    *   Nó lặp qua từng `segment` (đoạn cắt) đã được định nghĩa.
    *   Với mỗi `segment`, nó gọi `ffmpeg_service.cut_video()` và truyền vào `is_smart_cut=True`.

3.  **`app/services/ffmpeg_service.py` (Hàm `cut_video`)**
    *   Hàm nhận được tham số `is_smart_cut=True`.
    *   Điều kiện `if is_smart_cut:` (dòng 83) được thỏa mãn.
    *   Hàm gọi `exact_cut_service.exact_cut()` (dòng 85) để thực hiện cắt chính xác.

4.  **`app/services/exact_cut_service.py` (Hàm `exact_cut`)**
    *   Hàm này xây dựng một câu lệnh `ffmpeg` phức tạp.
    *   Nó sử dụng các tham số như `-c:v libx264` và `-c:a aac` để **re-encode** video và audio. Việc này đảm bảo có thể cắt tại bất kỳ frame nào, mang lại độ chính xác cao nhất.
    *   Cuối cùng, nó thực thi lệnh `ffmpeg` thông qua `subprocess.run()`.

**Sơ đồ chuỗi gọi hàm:**
`main_window.py (export_segments_action)` -> `SmartCutWorker (run)` -> `ffmpeg_service.py (cut_video)` -> `exact_cut_service.py (exact_cut)` -> `FFmpeg Command (Re-encode)`

### Kịch bản 2: `is_smart_cut = false` (Cắt Lossless)

Đây là luồng mặc định, ưu tiên tốc độ bằng cách cắt không cần re-encode (chỉ cắt được ở các keyframe).

1.  **`app/ui/main_window.py` (Hàm `export_segments_action`)**
    *   Hàm kiểm tra thấy `is_smart_cut` là `False`.
    *   Code bỏ qua khối `if` (dòng 343) và đi vào khối `try...except` (dòng 358).
    *   Hàm lặp qua các `segment` và gọi trực tiếp `ffmpeg_service.cut_video()`, truyền vào `is_smart_cut=False`. Toàn bộ quá trình này chạy trên UI thread chính.

2.  **`app/services/ffmpeg_service.py` (Hàm `cut_video`)**
    *   Hàm nhận được tham số `is_smart_cut=False`.
    *   Điều kiện `if is_smart_cut:` (dòng 83) không được thỏa mãn.
    *   Hàm gọi `get_ffmpeg_cut_cmd()` (dòng 91) để lấy câu lệnh cắt lossless.
    *   Lệnh này sử dụng `-c copy` để sao chép trực tiếp các stream video/audio mà không re-encode, giúp tốc độ xử lý rất nhanh.
    *   Nó thực thi lệnh `ffmpeg` thông qua `subprocess.run()`.

**Sơ đồ chuỗi gọi hàm:**
`main_window.py (export_segments_action)` -> `ffmpeg_service.py (cut_video)` -> `ffmpeg_service.py (get_ffmpeg_cut_cmd)` -> `FFmpeg Command (Lossless)`

## Giải Thích Các Hàm Chính

| File | Hàm / Lớp | Vai Trò Chính |
| --- | --- | --- |
| `app/ui/main_window.py` | `export_segments_action` | **Điểm khởi đầu.** Lấy thông tin từ UI, quyết định luồng "Smart Cut" hay "Lossless Cut". |
| `app/services/smartcut_service.py` | `SmartCutWorker` | **Worker Thread.** Quản lý tác vụ "Smart Cut" trong một thread riêng để không block UI. |
| `app/services/ffmpeg_service.py` | `cut_video` | **Bộ điều phối cắt.** Dựa vào cờ `is_smart_cut` để gọi hàm cắt phù hợp (`exact_cut` hoặc tự thực hiện cắt lossless). |
| `app/services/exact_cut_service.py` | `exact_cut` | **Cắt chính xác.** Chịu trách nhiệm xây dựng và thực thi lệnh FFmpeg để re-encode, đảm bảo cắt chính xác tại mọi frame. |
| `app/services/ffmpeg_service.py`| `get_ffmpeg_cut_cmd` | **Cắt Lossless.** Xây dựng lệnh FFmpeg sử dụng `-c copy` để cắt nhanh tại các keyframe. |

---

