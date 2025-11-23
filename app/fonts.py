import json
import os
from typing import Optional, List, Dict, Any
from PIL import ImageFont


PREFERRED_FONTS_URDU: List[str] = [
    "Arial", # User confirmed this works for Urdu rendering
    "Noto Nastaliq Urdu",
    "Jameel Noori Nastaleeq",
    "Jameel Noori Nastaleeq Kasheeda",
    "Nafees Web Naskh",
    "Nafees Nastaleeq",
]

PREFERRED_FONTS_EN: List[str] = [
    "Segoe UI",
    "Arial",
    "Roboto",
]

_FONTS_CONFIG_CACHE: Optional[Dict[str, Any]] = None


def _load_fonts_config() -> Dict[str, Any]:
    global _FONTS_CONFIG_CACHE
    if _FONTS_CONFIG_CACHE is not None:
        return _FONTS_CONFIG_CACHE
    config_path = os.path.join(os.getcwd(), "fonts_config.json")
    if not os.path.isfile(config_path):
        _FONTS_CONFIG_CACHE = {}
        return _FONTS_CONFIG_CACHE
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            _FONTS_CONFIG_CACHE = json.load(f) or {}
    except Exception:
        _FONTS_CONFIG_CACHE = {}
    return _FONTS_CONFIG_CACHE


def _candidate_font_paths() -> List[str]:
    candidates: List[str] = []

    # 1) Project-local fonts directory (preferred if present)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_fonts_dir = os.path.join(project_root, "fonts")
    search_dirs: List[str] = []
    if os.path.isdir(local_fonts_dir):
        search_dirs.append(local_fonts_dir)

    # 2) System fonts (Windows)
    windows_dir = os.environ.get("WINDIR", "C:\\Windows")
    search_dirs.append(os.path.join(windows_dir, "Fonts"))

    for base in search_dirs:
        if os.path.isdir(base):
            for root, _dirs, files in os.walk(base):
                for f in files:
                    if f.lower().endswith((".ttf", ".otf")):
                        candidates.append(os.path.join(root, f))
    return candidates


def _find_font_by_preferred_names(preferred: List[str]) -> Optional[str]:
    candidates = _candidate_font_paths()
    lower_map = {os.path.basename(p).lower(): p for p in candidates}
    for name in preferred:
        name_lower = name.lower()
        for base, full in lower_map.items():
            if name_lower in base:
                return full
    return None


def get_urdu_font_path(override_path: Optional[str] = None) -> Optional[str]:
    if override_path:
        return override_path
    cfg = _load_fonts_config()
    cfg_path = cfg.get("urdu_font_path")
    if isinstance(cfg_path, str) and os.path.isfile(cfg_path):
        return cfg_path
    path = _find_font_by_preferred_names(PREFERRED_FONTS_URDU)
    if path:
        return path
    candidates = _candidate_font_paths()
    for p in candidates:
        base = os.path.basename(p).lower()
        if any(tag in base for tag in ["arab", "urdu", "naskh", "nastaliq"]):
            return p
    for p in candidates:
        base = os.path.basename(p).lower()
        if "arial" in base:
            return p
    return None


def get_english_font_path(override_path: Optional[str] = None) -> Optional[str]:
    if override_path:
        return override_path
    cfg = _load_fonts_config()
    cfg_path = cfg.get("english_font_path")
    if isinstance(cfg_path, str) and os.path.isfile(cfg_path):
        return cfg_path
    path = _find_font_by_preferred_names(PREFERRED_FONTS_EN)
    if path:
        return path
    candidates = _candidate_font_paths()
    for p in candidates:
        base = os.path.basename(p).lower()
        if "arial" in base:
            return p
    return None


def load_font(path: Optional[str], size: int) -> ImageFont.FreeTypeFont:
    if path and os.path.isfile(path):
        try:
            return ImageFont.truetype(path, size=size)
        except Exception as exc:
            raise RuntimeError(f"Failed to load font at {path}: {exc}") from exc
    else:
        raise RuntimeError(f"Font path is missing or does not exist: {path!r}")
