# MiniLosslessCut

> A high-performance, lightweight desktop video processing utility built with PyQt6, OpenCV, and MediaPipe. Designed for fast framing, precision watermarking, and AI-powered privacy masking.

---

## 🚀 Key Features

### 1. High-Performance Video Trimming & Control
* **Lossless Precision:** Quickly slice and edit video segments with minimal re-encoding overhead.
* **Shortcut Management:** Instantly close or reset the active video workspace using `Ctrl + W` (Windows/Linux) or `Cmd + W` (macOS) for seamless multi-video workflows.
* **Interactive Tooltips:** Built-in contextual help and tooltips to guide users effortlessly through navigation and controls.

### 2. Advanced Text Watermarking
* **Visual Parity Control:** Precise DPI scaling ($1.333\times$) and bounding box correction ensuring 1:1 parity between UI preview and final rendered output.
* **Custom Styling:** Full control over font scaling, rotation, opacity ranges ($0-100$ or $0-1$), and positional offsets.
* **Stable Baseline:** Production-tested rendering pipeline guaranteeing visual consistency across diverse aspect ratios (including 9:16 vertical video).

### 3. AI-Powered Face Masking & Privacy Pipeline
* **MediaPipe Integration:** Real-time face detection optimized for accurate tracking.
* **Smart Bounding Box Adjustment:** Enhanced vertical offset ($+15\% - 20\%$) to completely cover the forehead and hairline without horizontal drift.
* **Multiple Masking Shapes:**
  * **Square (Default):** Standard rectangular privacy box.
  * **Circle / Ellipse:** Soft-edged circular/elliptical overlay.
  * **Replace Image:** Custom user-selected image (PNG/JPG) mapped directly over faces.
* **Flexible Blur Styles & Intensity:**
  * **Gaussian Blur:** Natural smooth blurring.
  * **Pixelate (Mosaic):** Retro television pixel effect with adjustable block size.
  * **Box Blur:** Fast flat-array blurring.
  * **Solid Color (Blackout):** Solid privacy block.
  * **Intensity Control:** Fine-tune blur strength or pixel density ($1 - 100$).

---

## 💻 Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/your-username/minilosslesscut.git
   cd minilosslesscut
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure FFmpeg:**
   Ensure the appropriate binary for your OS (`ffmpeg.exe` for Windows, `ffmpeg` for macOS/Linux) is placed in your system PATH or within the local `bin/` directory structure.

---

## 🕹️ Quick Start Guide

1. **Launch the Application:**
   ```bash
   python main.py
   ```
2. **Load a Video:** Select your target video file using the file picker.
3. **Apply Overlays:** 
   * Navigate to the Watermark tab to configure text properties.
   * Switch to the Face Blur tab, select your preferred shape, blur style, and intensity.
4. **Manage Workspace:** Press `Ctrl + W` anytime to close the current video and clear the workspace for a new file.
