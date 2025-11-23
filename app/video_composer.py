import json
import os
from typing import List, Dict, Optional

import numpy as np
from moviepy.editor import (
    AudioFileClip,
    ImageClip,
    CompositeAudioClip,
    concatenate_videoclips,
)

from .backgrounds import prepare_background_image
from .caption_renderer import render_caption_frame
from .config import VIDEO_WIDTH, VIDEO_HEIGHT, FPS
from .tts_layer import generate_english_tts, generate_urdu_tts


def _load_script(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Script must be a list of {en, ur} objects")
    return data


def build_video(
    script_path: str,
    output_path: str,
    background_path: Optional[str] = None,
    english_font_path: Optional[str] = None,
    urdu_font_path: Optional[str] = None,
    bgm_path: Optional[str] = None,
    bgm_volume: float = 0.1,
    log: Optional[callable] = None,
) -> str:
    from .cleanup import ensure_temp_dirs, get_temp_image_path
    
    segments = _load_script(script_path)
    if not segments:
        raise ValueError("Script is empty")

    ensure_temp_dirs()

    if background_path:
        bg_final = prepare_background_image(background_path)
    else:
        from PIL import Image

        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (15, 15, 24))
        bg_final = get_temp_image_path(suffix="_fallback_bg.jpg")
        img.save(bg_final, format="JPEG", quality=95)

    clips = []

    for idx, pair in enumerate(segments, start=1):
        if log:
            log(f"[segment {idx}/{len(segments)}] Generating audio and frame...")
        en_text = pair.get("en", "")
        ur_text = pair.get("ur", "")

        en_tts = generate_english_tts(en_text)
        ur_tts = generate_urdu_tts(ur_text)

        teaching_gap = 0.2
        pause_after = float(pair.get("pause_after", 0.0) or 0.0)
        min_duration = float(pair.get("min_duration", 0.0) or 0.0)

        en_start = 0.0
        ur_start = en_tts.duration + teaching_gap
        total_audio_duration = ur_start + ur_tts.duration + pause_after

        if total_audio_duration < min_duration:
            total_audio_duration = min_duration

        frame_img = render_caption_frame(
            bg_final,
            pair,
            english_font_path=english_font_path,
            urdu_font_path=urdu_font_path,
        )
        img_array = np.array(frame_img)
        img_clip = ImageClip(img_array).set_duration(total_audio_duration)

        en_audio_clip = AudioFileClip(en_tts.path)
        ur_audio_clip = AudioFileClip(ur_tts.path)

        en_track = en_audio_clip.set_start(en_start).volumex(1.0)
        ur_track = ur_audio_clip.set_start(ur_start).volumex(1.0)

        mixed_audio = CompositeAudioClip([en_track, ur_track])
        mixed_audio = mixed_audio.audio_fadein(0.12).audio_fadeout(0.12)

        clip = img_clip.set_audio(mixed_audio)
        clip = clip.fadein(0.5).fadeout(0.5)
        clips.append(clip)


    final = concatenate_videoclips(clips, method="compose")
    final = final.set_fps(FPS).resize((VIDEO_WIDTH, VIDEO_HEIGHT))

    # Add background music if provided
    if bgm_path:
        try:
            bgm_audio = AudioFileClip(bgm_path)
            
            # Loop the BGM to match video duration
            video_duration = final.duration
            if bgm_audio.duration < video_duration:
                # Calculate how many times to loop
                loops_needed = int(video_duration / bgm_audio.duration) + 1
                bgm_audio = bgm_audio.loop(n=loops_needed)
            
            # Trim BGM to match video duration
            bgm_audio = bgm_audio.subclip(0, video_duration)
            
            # Set BGM volume (default is low to not overpower voices)
            bgm_audio = bgm_audio.volumex(bgm_volume)
            
            # Mix BGM with existing audio
            if final.audio:
                final_audio = CompositeAudioClip([final.audio, bgm_audio])
                final = final.set_audio(final_audio)
            else:
                final = final.set_audio(bgm_audio)
        except Exception as e:
            if log:
                log(f"Warning: Could not add BGM: {e}")
            # Continue without BGM if there's an error

    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=FPS,
        threads=4,
        preset="medium",
    )

    return output_path
