from app.core.ffmpeg_config import get_ffmpeg_crop_cmd
from app.core.helpers import check_cuda_support


class CropService:
    def __init__(self):
        self.use_gpu = check_cuda_support()

    def build_crop_command(self, input_path: str, output_path: str, x: int, y: int, w: int, h: int) -> list[str]:
        # Gọi hàm helper lấy template lệnh theo status GPU
        template = get_ffmpeg_crop_cmd(is_gpu=self.use_gpu)
        
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