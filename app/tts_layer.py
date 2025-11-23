import asyncio
import os
from dataclasses import dataclass
import edge_tts
from pydub import AudioSegment

from .config import DEFAULT_TTS_CONFIG, TTSConfig


@dataclass
class TTSAudio:
    path: str
    duration: float


async def _edge_tts_to_file(text: str, voice: str, out_path: str) -> None:
    """Generate TTS audio using Edge TTS."""
    communicate = edge_tts.Communicate(text, voice=voice)
    await communicate.save(out_path)


def _measure_audio(path: str) -> float:
    """Measure audio duration in seconds."""
    audio = AudioSegment.from_file(path)
    return audio.duration_seconds


def generate_english_tts(
    text: str,
    config: TTSConfig = DEFAULT_TTS_CONFIG,
) -> TTSAudio:
    """
    Generate English TTS audio using Edge TTS with female voice (Ava).
    
    Args:
        text: English text to convert to speech
        config: TTS configuration with voice settings
    
    Returns:
        TTSAudio object with path and duration
    """
    from .cleanup import get_temp_audio_path
    
    tmp = get_temp_audio_path(suffix="_en.mp3")
    
    # Use Edge TTS with female voice
    asyncio.run(_edge_tts_to_file(text, config.english_voice, tmp))
    
    duration = _measure_audio(tmp)
    return TTSAudio(path=tmp, duration=duration)


def generate_urdu_tts(
    text: str,
    config: TTSConfig = DEFAULT_TTS_CONFIG,
) -> TTSAudio:
    """
    Generate Urdu TTS audio using Edge TTS with male voice (Andrew).
    
    Args:
        text: Urdu text to convert to speech
        config: TTS configuration with voice settings
    
    Returns:
        TTSAudio object with path and duration
    """
    from .cleanup import get_temp_audio_path
    
    tmp = get_temp_audio_path(suffix="_ur.mp3")
    
    # Use Edge TTS with male voice
    asyncio.run(_edge_tts_to_file(text, config.urdu_voice, tmp))
    
    duration = _measure_audio(tmp)
    return TTSAudio(path=tmp, duration=duration)

