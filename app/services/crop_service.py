from app.core.ffmpeg_config import get_ffmpeg_crop_cmd
from app.core.helpers import calculate_cropped_bitrate, check_cuda_support, get_media_info


class CropService:
    def __init__(self):
        self.use_gpu = check_cuda_support()

    def build_crop_command(self, input_path: str, output_path: str, x: int, y: int, w: int, h: int) -> list[str]:
        # Gọi hàm helper lấy template lệnh theo status GPU
        target_bitrate = None
        # 1. Trích xuất thông tin video gốc bằng ffprobe
        try:
            info = get_media_info(input_path)
            video_stream = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
            format_info = info.get("format", {})

            if video_stream:
                orig_w = int(video_stream.get("width", 0))
                orig_h = int(video_stream.get("height", 0))

                # Bitrate có thể nằm ở stream video hoặc format container
                raw_bitrate = video_stream.get("bit_rate") or format_info.get("bit_rate")

                if raw_bitrate and orig_w > 0 and orig_h > 0:
                    orig_bitrate = int(raw_bitrate)
                    # Tính toán bitrate mới
                    target_bitrate = calculate_cropped_bitrate(orig_w, orig_h, w, h, orig_bitrate)
        except Exception as e:
            print(f"[CẢNH BÁO] Không lấy được bitrate gốc: {e}")
        template = get_ffmpeg_crop_cmd(is_gpu=self.use_gpu, bitrate=target_bitrate)
        
        cmd = []
        for arg in template:
            if isinstance(arg, tuple):
                arg_str = str(arg[0]) if len(arg) > 0 else ""
            else:
                arg_str = str(arg)
            formatted_arg = arg_str.format(
                input_path=input_path,
                output_path=output_path,
                w=w,
                h=h,
                x=x,
                y=y
            )
            cmd.append(formatted_arg)
        return cmd

    def get_execution_mode_str(self) -> str:
        return "GPU (NVIDIA CUDA)" if self.use_gpu else "CPU (libx264)"