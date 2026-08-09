# 🎬 Mini LosslessCut - Professional AI Video Processing Edition

A ultra-fast, high-performance video cutting and watermark/blur application built with **PyQt6**, **OpenCV**, **MediaPipe**, and **FFmpeg Hardware Acceleration (NVENC)**.

---

## 🚀 Key Features

* **⚡ Ultra-Fast Processing:**
  * Downscaled AI Inference (320x320) mapped directly to full-resolution frames.
  * Near-zero CPU overhead face pixelation via downscale/upscale resizing (`INTER_NEAREST`).
  * Direct pipe streaming to **Nvidia NVENC (`h264_nvenc` / `hevc_nvenc`)** for hardware-accelerated encoding.
* **🤖 AI-Powered Privacy Filters:**
  * Real-time Face Detection & Blurring (Pixelate / Gaussian / Box Blur / Image Replace).
  * Background Segmentation & Soft Blur blending.
* **🎨 Multi-Text Overlays & Watermarking:**
  * Canva-style multi-text overlays with full control over font, size, rotation, and opacity.
  * Pixel-perfect DPI scaling and preview parity.
* **💾 Project State Management:**
  * Automatic save & restore of project configurations via `<video_name>.json`.
  * Safe JSON fallback with default values.
* **🧹 Clean Workspace:**
  * Instant workspace reset via `Ctrl + W` (or `Cmd + W`).

---

## 🛠️ Installation & Setup

### Prerequisites
* Python 3.10 or higher
* FFmpeg with NVENC support (Nvidia GPU recommended)

### Step 1: Clone Repository & Create Virtual Environment
```bash
git clone [https://github.com/apacheservices68/minilossless.git](https://github.com/apacheservices68/minilossless.git)
cd minilossless
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows