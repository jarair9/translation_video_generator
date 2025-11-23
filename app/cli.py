import argparse
import os

from .video_composer import build_video
from .cleanup import cleanup_temp


def main() -> None:
    parser = argparse.ArgumentParser(description="Urdu-English vertical video generator")
    parser.add_argument("script", help="Path to JSON script file with [{en, ur}] pairs")
    parser.add_argument("--output", "-o", default="output.mp4", help="Output video file path")
    parser.add_argument("--background", "-b", help="Optional background image path")
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Do not delete temp files after rendering",
    )
    parser.add_argument(
        "--english-font",
        help="Explicit path to English font file (.ttf/.otf)",
    )
    parser.add_argument(
        "--urdu-font",
        help="Explicit path to Urdu font file (.ttf/.otf)",
    )

    args = parser.parse_args()

    def _log(msg: str) -> None:
        print(msg)

    print("[info] Starting video build...")
    try:
        build_video(
            script_path=args.script,
            output_path=args.output,
            background_path=args.background,
            english_font_path=args.english_font,
            urdu_font_path=args.urdu_font,
            log=_log,
        )
        print(f"[info] Video written to {args.output}")
    finally:
        if not args.no_cleanup:
            cleanup_temp()


if __name__ == "__main__":
    main()
