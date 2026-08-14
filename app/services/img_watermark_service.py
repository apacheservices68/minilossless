# Added on 08132026: [VI] Import cac thu vien can thiet / [EN] Import necessary libraries
import ffmpeg

from app.core.constants import VIDEO_CODECS
from app.core.watermark_constants import WATERMARK_POSITIONS

### Author : @apacheservices68 

def apply_image_watermark(video_path, output_path, image_path, position_expression):
    input_video = ffmpeg.input(video_path)
    watermark = ffmpeg.input(image_path)

    #### 081326 fix bug call from watermark constant
    position_info = WATERMARK_POSITIONS.get(position_expression, {})
    coords = position_info.get("expr", "x=10:y=10")

    pos_dict = dict(item.split('=') for item in coords.split(':'))    
    processed_video = ffmpeg.overlay(input_video, watermark, eof_action='repeat', x=pos_dict['x'], y=pos_dict['y'])

    ffmpeg.output(
        processed_video, 
        input_video.audio,  ### 081326 Add audio stream to output (fix bug missing audio output)
        output_path, 
        vcodec=VIDEO_CODECS.CPU_H264, 
        acodec='copy'
        ).run(overwrite_output=True)
    
