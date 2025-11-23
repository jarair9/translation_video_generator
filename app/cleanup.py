import os
import shutil
import glob
from typing import Optional


# Temp directory structure
TEMP_ROOT = "temp"
TEMP_AUDIO_DIR = os.path.join(TEMP_ROOT, "audio")
TEMP_IMAGES_DIR = os.path.join(TEMP_ROOT, "images")
TEMP_SCRIPTS_DIR = os.path.join(TEMP_ROOT, "scripts")


def ensure_temp_dirs() -> None:
    """Create temp directory structure if it doesn't exist."""
    os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
    os.makedirs(TEMP_IMAGES_DIR, exist_ok=True)
    os.makedirs(TEMP_SCRIPTS_DIR, exist_ok=True)


def cleanup_temp(keep_root: bool = False, verbose: bool = False) -> None:
    """
    Clean up all temporary files after video generation.
    
    Args:
        keep_root: If True, keeps the temp directory structure but removes files
        verbose: If True, prints cleanup information
    
    Note:
        This function safely removes temp files without affecting
        generated videos in the main directory.
    """
    if not os.path.isdir(TEMP_ROOT):
        if verbose:
            print(f"Temp directory '{TEMP_ROOT}' does not exist, nothing to clean.")
        return
    
    try:
        if keep_root:
            # Remove files but keep directory structure
            file_count = 0
            for subdir in [TEMP_AUDIO_DIR, TEMP_IMAGES_DIR, TEMP_SCRIPTS_DIR]:
                if os.path.isdir(subdir):
                    for file in glob.glob(os.path.join(subdir, "*")):
                        if os.path.isfile(file):
                            try:
                                os.remove(file)
                                file_count += 1
                            except Exception as e:
                                if verbose:
                                    print(f"Could not remove {file}: {e}")
            
            # Also clean root temp directory
            for file in glob.glob(os.path.join(TEMP_ROOT, "*")):
                if os.path.isfile(file):
                    try:
                        os.remove(file)
                        file_count += 1
                    except Exception as e:
                        if verbose:
                            print(f"Could not remove {file}: {e}")
            
            if verbose:
                print(f"Cleaned {file_count} temp files.")
        else:
            # Remove entire temp directory
            shutil.rmtree(TEMP_ROOT)
            if verbose:
                print(f"Removed temp directory: {TEMP_ROOT}")
                
    except Exception as e:
        if verbose:
            print(f"Cleanup error: {e}")
        # Silently fail - don't crash the application


def get_temp_audio_path(suffix: str = "_audio.mp3") -> str:
    """Get a unique temp path for audio files."""
    import tempfile
    ensure_temp_dirs()
    fd, path = tempfile.mkstemp(suffix=suffix, dir=TEMP_AUDIO_DIR)
    os.close(fd)
    return path


def get_temp_image_path(suffix: str = "_image.jpg") -> str:
    """Get a unique temp path for image files."""
    import tempfile
    ensure_temp_dirs()
    fd, path = tempfile.mkstemp(suffix=suffix, dir=TEMP_IMAGES_DIR)
    os.close(fd)
    return path


def get_temp_script_path(suffix: str = "_script.json") -> str:
    """Get a unique temp path for script files."""
    import tempfile
    ensure_temp_dirs()
    fd, path = tempfile.mkstemp(suffix=suffix, dir=TEMP_SCRIPTS_DIR)
    os.close(fd)
    return path

