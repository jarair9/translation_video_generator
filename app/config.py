from dataclasses import dataclass


VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 24


@dataclass
class CaptionStyle:
    box_width_ratio: float = 0.86
    box_radius: int = 25
    box_opacity: int = 242  # ~95%
    box_padding: int = 30
    box_y_ratio: float = 0.4
    shadow_offset: int = 10
    shadow_blur_radius: int = 18
    en_font_size: int = 54
    ur_font_size: int = 64
    line_spacing: int = 8


DEFAULT_CAPTION_STYLE = CaptionStyle()


@dataclass
class TTSConfig:
    # Edge TTS voices - using proper language-specific voices
    english_voice: str = "en-US-AvaMultilingualNeural"  # Female voice for English
    urdu_voice: str = "ur-PK-AsadNeural"  # Male voice for Urdu (Pakistan)


DEFAULT_TTS_CONFIG = TTSConfig()

