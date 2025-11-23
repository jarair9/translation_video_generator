from typing import Tuple, List, Dict

from PIL import Image, ImageDraw, ImageFilter

from .config import VIDEO_WIDTH, VIDEO_HEIGHT, DEFAULT_CAPTION_STYLE
from .fonts import get_urdu_font_path, get_english_font_path, load_font
from .urdu_text import wrap_text_rtl, wrap_text_ltr, measure_multiline


def _draw_rounded_rectangle_with_shadow(
    base: Image.Image,
    box: Tuple[int, int, int, int],
    radius: int,
    opacity: int,
    shadow_offset: int,
    shadow_blur_radius: int,
) -> None:
    x1, y1, x2, y2 = box

    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_box = (x1 + shadow_offset, y1 + shadow_offset, x2 + shadow_offset, y2 + shadow_offset)
    shadow_draw.rounded_rectangle(shadow_box, radius=radius, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur_radius))
    base.alpha_composite(shadow)

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(box, radius=radius, fill=(255, 255, 255, opacity))
    base.alpha_composite(overlay)


def render_caption_frame(
    background_path: str,
    pair: Dict[str, str],
    english_font_path: str | None = None,
    urdu_font_path: str | None = None,
) -> Image.Image:
    style = DEFAULT_CAPTION_STYLE

    bg = Image.open(background_path).convert("RGB").resize((VIDEO_WIDTH, VIDEO_HEIGHT))
    img = bg.convert("RGBA")
    draw = ImageDraw.Draw(img)

    en_font_path_resolved = get_english_font_path(english_font_path)
    ur_font_path_resolved = get_urdu_font_path(urdu_font_path)

    # Supersampling factor
    scale = 2
    
    # Create high-res canvas
    # We render the text on a separate high-res layer then paste it down
    # But to keep it simple with the existing background logic, let's just draw text high-res
    # Actually, simpler: Draw everything on a scaled-up transparent layer, then resize and composite.
    
    text_layer = Image.new("RGBA", (VIDEO_WIDTH * scale, VIDEO_HEIGHT * scale), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    
    # Load fonts at scaled size
    en_font_scaled = load_font(en_font_path_resolved, style.en_font_size * scale)
    ur_font_scaled = load_font(ur_font_path_resolved, style.ur_font_size * scale)
    
    # Recalculate layout at scale
    max_box_width = int(VIDEO_WIDTH * style.box_width_ratio) - 2 * style.box_padding
    max_box_width_scaled = max_box_width * scale
    
    # We need to re-wrap because font metrics might slightly differ at scale, but usually linear.
    # Let's re-wrap to be safe.
    en_lines_scaled = wrap_text_ltr(pair.get("en", ""), en_font_scaled, max_box_width_scaled, text_draw)
    ur_lines_scaled = wrap_text_rtl(pair.get("ur", ""), ur_font_scaled, max_box_width_scaled, text_draw)
    
    # Calculate scaled dimensions
    en_w_s, en_h_s = measure_multiline(en_lines_scaled, en_font_scaled, style.line_spacing * scale, text_draw)
    ur_w_s, ur_h_s = measure_multiline(ur_lines_scaled, ur_font_scaled, style.line_spacing * scale, text_draw)
    
    content_width_s = max(en_w_s, ur_w_s)
    content_height_s = en_h_s + ur_h_s + (style.line_spacing * scale) * 2
    
    box_width_s = content_width_s + (style.box_padding * scale) * 2
    box_height_s = content_height_s + (style.box_padding * scale) * 2
    
    # Position box
    box_left_s = (VIDEO_WIDTH * scale - box_width_s) // 2
    box_top_s = int(VIDEO_HEIGHT * scale * style.box_y_ratio) - box_height_s // 2
    box_right_s = box_left_s + box_width_s
    box_bottom_s = box_top_s + box_height_s
    
    # Draw Box (Scaled)
    _draw_rounded_rectangle_with_shadow(
        text_layer,
        (box_left_s, box_top_s, box_right_s, box_bottom_s),
        radius=style.box_radius * scale,
        opacity=style.box_opacity,
        shadow_offset=style.shadow_offset * scale,
        shadow_blur_radius=style.shadow_blur_radius * scale,
    )
    
    current_y_s = box_top_s + (style.box_padding * scale)
    
    # Draw English (Scaled)
    for line in en_lines_scaled:
        bbox = text_draw.textbbox((0, 0), line, font=en_font_scaled)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (VIDEO_WIDTH * scale) // 2 - w // 2
        text_draw.text((x, current_y_s), line, font=en_font_scaled, fill=(0, 0, 0, 255))
        current_y_s += h + (style.line_spacing * scale)

    current_y_s += (style.line_spacing * scale) + (10 * scale)

    # Draw Urdu (Scaled)
    for line in ur_lines_scaled:
        bbox = text_draw.textbbox((0, 0), line, font=ur_font_scaled)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (VIDEO_WIDTH * scale) // 2 - w // 2
        # Lighter stroke for better readability
        stroke_w = 0  # No stroke for lighter appearance
        text_draw.text((x, current_y_s), line, font=ur_font_scaled, fill=(0, 0, 0, 255), stroke_width=stroke_w, stroke_fill=(0,0,0,255))
        current_y_s += h + (style.line_spacing * scale)
        
    # Downscale and composite
    text_layer_resized = text_layer.resize((VIDEO_WIDTH, VIDEO_HEIGHT), resample=Image.LANCZOS)
    img.alpha_composite(text_layer_resized)

    return img.convert("RGB")
