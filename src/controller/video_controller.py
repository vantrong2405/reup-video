import argparse
import sys
import json
import os
from service.video_service import VideoService
from service.logo_service import LogoService

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

class VideoController:
    DEFAULT_MODEL_PATH = "best.pt"
    DEFAULT_CONF_THRESHOLD = 0.4

    def __init__(self):
        self.service = LogoService()

    def _handle_detect(self, argv):
        parser = argparse.ArgumentParser(description="Logo Detection")
        parser.add_argument("command")
        parser.add_argument("image_path")
        parser.add_argument("model_path", nargs="?", default=self.DEFAULT_MODEL_PATH)
        parser.add_argument("conf_threshold", nargs="?", type=float, default=self.DEFAULT_CONF_THRESHOLD)
        args = parser.parse_args(argv[1:])
        try:
            result = self.service.detect_logo(args.image_path, args.model_path, args.conf_threshold)
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({"logos": [], "count": 0, "error": str(e)}), file=sys.stderr)
            sys.exit(1)

    def _handle_process(self, argv):
        parser = argparse.ArgumentParser(description="Logo Processing")
        parser.add_argument("command")
        parser.add_argument("origin_path")
        parser.add_argument("logo_path")
        parser.add_argument("model_path")
        parser.add_argument("conf_threshold", type=float)
        parser.add_argument("output_path")
        args = parser.parse_args(argv[1:])
        try:
            result = self.service.process_logo(args.origin_path, args.logo_path, args.model_path, args.conf_threshold, args.output_path)
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({"output": "", "error": str(e)}), file=sys.stderr)
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Video Processing Controller")
    subparsers = parser.add_subparsers(dest="command")

    parser_pipeline = subparsers.add_parser("pipeline")
    parser_pipeline.add_argument("video_input")
    parser_pipeline.add_argument("logo_input")
    parser_pipeline.add_argument("detect_json")
    parser_pipeline.add_argument("output_path")
    
    # Optional
    parser_pipeline.add_argument("--intro_url", help="URL or path to intro video")
    parser_pipeline.add_argument("--work_dir", default="/tmp", help="Working directory")
    parser_pipeline.add_argument("--flip", action="store_true", help="Flip video horizontally")
    parser_pipeline.add_argument("--zoom", type=float, default=1.0, help="Zoom factor")
    parser_pipeline.add_argument("--speed", type=float, default=1.0, help="Speed factor")
    parser_pipeline.add_argument("--ffmpeg_preset", default="veryfast", help="FFmpeg preset")
    
    # Color
    parser_pipeline.add_argument("--brightness", type=float, default=0.0)
    parser_pipeline.add_argument("--saturation", type=float, default=1.0)
    parser_pipeline.add_argument("--hue", type=float, default=0.0)
    
    # Audio
    parser_pipeline.add_argument("--background_music", help="Path to background music")
    parser_pipeline.add_argument("--bg_music_volume", type=float, default=0.3)
    
    # OCR
    parser_pipeline.add_argument("--remove_text", action="store_true")
    parser_pipeline.add_argument("--ocr_languages", nargs="+", default=["en"])
    parser_pipeline.add_argument("--gemini_key", help="Gemini API Key")
    
    # NSFW
    parser_pipeline.add_argument("--filter_nsfw", action="store_true")
    
    # Signature (NEW)
    parser_pipeline.add_argument("--unique", action="store_true", help="Enable unique video signature (anti-copyright)")
    parser_pipeline.add_argument("--watermark", help="Watermark text")
    parser_pipeline.add_argument("--watermark-opacity", type=float, default=0.15, help="Watermark opacity (0.1-0.3)")
    parser_pipeline.add_argument("--watermark-size", type=int, default=18, help="Watermark font size")
    parser_pipeline.add_argument("--watermark-speed", type=int, default=50, help="Watermark scroll speed (px/s)")
    parser_pipeline.add_argument("--watermark-position", choices=["top", "bottom", "diagonal", "random"], default="bottom")

    # Split
    parser_pipeline.add_argument("--split-mode", choices=['none', 'manual', 'auto'], default='none')
    parser_pipeline.add_argument("--split-start", default="00:00:00")
    parser_pipeline.add_argument("--split-duration", type=float, default=10.0)
    parser_pipeline.add_argument("--split-limit", type=int, default=5)

    args = parser.parse_args()

    if args.command == "detect":
         VideoController()._handle_detect(sys.argv)
    elif args.command == "process":
         VideoController()._handle_process(sys.argv)
    elif args.command == "pipeline":
        try:
            detect_json = args.detect_json
            if os.path.isfile(detect_json):
                with open(detect_json, 'r') as f:
                    detect_json = f.read()

            output = VideoService.process_pipeline(
                args.video_input,
                args.logo_input,
                detect_json,
                args.output_path,
                intro_url=args.intro_url,
                work_dir=args.work_dir,
                flip=args.flip,
                zoom=args.zoom,
                speed=args.speed,
                brightness=args.brightness,
                saturation=args.saturation,
                hue=args.hue,
                background_music=args.background_music,
                bg_music_volume=args.bg_music_volume,
                remove_text=args.remove_text,
                ocr_languages=args.ocr_languages,
                gemini_key=args.gemini_key,
                filter_nsfw=args.filter_nsfw,
                ffmpeg_preset=args.ffmpeg_preset,
                split_mode=args.split_mode,
                split_start=args.split_start,
                split_duration=args.split_duration,
                split_limit=args.split_limit,
                unique_mode=args.unique,
                watermark_text=args.watermark,
                watermark_opacity=getattr(args, 'watermark_opacity', 0.15),
                watermark_size=getattr(args, 'watermark_size', 18),
                watermark_speed=getattr(args, 'watermark_speed', 50),
                watermark_position=getattr(args, 'watermark_position', 'bottom')
            )
            print(json.dumps({"success": True, "output": output}))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
