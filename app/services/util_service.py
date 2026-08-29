# Add on 08282026
from app.core.ffmpeg_config import get_ffmpeg_crop_cmd
from app.core.helpers import calculate_cropped_bitrate, check_cuda_support, get_media_info

class UtilService:
    def __init__(self):
        self.use_gpu = check_cuda_support()

    def build_rotate_command(self, input_path: str, output_path: str, rotate_option: str) -> list[str]:
        """
        Xây dựng câu lệnh FFmpeg cho Xoay / Lật video.
        """
        # 1. Map các tùy chọn UI sang FFmpeg filter graph
        filter_map = {
            "Rotate 90°": "transpose=1",
            "Rotate 180°": "transpose=2,transpose=2",
            "Rotate 270°": "transpose=2",
            "Horizontal Flip": "hflip",
            "Vertical Flip": "vflip"
        }

        filter_str = filter_map.get(rotate_option)
        if not filter_str:
            return None

        # 2. Lấy bitrate gốc để đảm bảo chất lượng video đầu ra
        bitrate_str = None
        try:
            info = get_media_info(input_path)
            video_stream = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
            orig_bitrate = 0
            if "bit_rate" in info.get("format", {}):
                orig_bitrate = int(info["format"]["bit_rate"])
            elif "bit_rate" in video_stream:
                orig_bitrate = int(video_stream["bit_rate"])
            bitrate_bps = int(orig_bitrate)
            bitrate_str = f"{int(bitrate_bps / 1000)}k"
        except Exception:
            pass
        
        # 3. Lấy template command từ config
        cmd_template = get_ffmpeg_crop_cmd(
            is_gpu=self.use_gpu,
            bitrate=bitrate_str,
            filter_str=filter_str
        )

        # 4. Replace các placeholder đường dẫn
        cmd = [
            item.format(input_path=input_path, output_path=output_path)
            if isinstance(item, str) and ("{input_path}" in item or "{output_path}" in item)
            else item
            for item in cmd_template
        ]

        return cmd

    def build_resize_command(self, input_path: str, output_path: str, width: int, height: int) -> list[str]:
        """
        Xây dựng câu lệnh FFmpeg cho Đổi kích thước (Resize) video.
        """
        if width <= 0 or height <= 0:
            return None

        # 1. Filter scale trong FFmpeg
        filter_str = f"scale={width}:{height}"

        # 2. Tính toán bitrate phù hợp với kích thước mới (tránh phình dung lượng hoặc mờ video)
        bitrate_str = None
        try:
            info = get_media_info(input_path)
            video_stream = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
            
            if video_stream and "width" in video_stream and "height" in video_stream:
                orig_w = int(video_stream["width"])
                orig_h = int(video_stream["height"])
                
                # Lấy bitrate gốc
                orig_bitrate = 0
                if "bit_rate" in info.get("format", {}):
                    orig_bitrate = int(info["format"]["bit_rate"])
                elif "bit_rate" in video_stream:
                    orig_bitrate = int(video_stream["bit_rate"])
                
                if orig_bitrate > 0:
                    # Dùng helper tính bitrate theo tỉ lệ diện tích pixel mới / cũ
                    bitrate_bps = calculate_cropped_bitrate(orig_w, orig_h, width, height, orig_bitrate)
                    bitrate_str = f"{int(bitrate_bps / 1000)}k"
        except Exception:
            pass

        # 3. Lấy template command từ config
        cmd_template = get_ffmpeg_crop_cmd(
            is_gpu=self.use_gpu,
            bitrate=bitrate_str,
            filter_str=filter_str
        )

        # 4. Replace các placeholder đường dẫn
        cmd = [
            item.format(input_path=input_path, output_path=output_path)
            if isinstance(item, str) and ("{input_path}" in item or "{output_path}" in item)
            else item
            for item in cmd_template
        ]

        return cmd

    def get_execution_mode_str(self) -> str:
        return "GPU (NVIDIA CUDA)" if self.use_gpu else "CPU (libx264)"