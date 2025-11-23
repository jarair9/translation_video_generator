import os
import tempfile
from PIL import Image

from .config import VIDEO_WIDTH, VIDEO_HEIGHT


if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS


def prepare_background_image(source_path: str) -> str:
    from .cleanup import get_temp_image_path
    
    img = Image.open(source_path).convert("RGB")
    src_w, src_h = img.size
    target_ratio = VIDEO_WIDTH / VIDEO_HEIGHT
    src_ratio = src_w / src_h
    if abs(src_ratio - target_ratio) < 0.01:
        resized = img.resize((VIDEO_WIDTH, VIDEO_HEIGHT), Image.LANCZOS)
    elif src_ratio > target_ratio:
        new_height = VIDEO_HEIGHT
        new_width = int(new_height * src_ratio)
        resized = img.resize((new_width, new_height), Image.LANCZOS)
        left = (new_width - VIDEO_WIDTH) // 2
        resized = resized.crop((left, 0, left + VIDEO_WIDTH, VIDEO_HEIGHT))
    else:
        new_width = VIDEO_WIDTH
        new_height = int(new_width / src_ratio)
        resized = img.resize((new_width, new_height), Image.LANCZOS)
        top = (new_height - VIDEO_HEIGHT) // 2
        resized = resized.crop((0, top, VIDEO_WIDTH, top + VIDEO_HEIGHT))
    
    out_path = get_temp_image_path(suffix="_bg_final.jpg")
    resized.save(out_path, format="JPEG", quality=95)
    return out_path

