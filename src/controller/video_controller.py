import sys
import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from service.video_service import VideoService

# Load environment variables from .env file
load_dotenv()

class VideoController:
    def process_logo(self, args):
        try:
            VideoService.process_logo(
                args.video_input,
                args.logo_input,
                args.detect_json,
                args.output_path,
                args.new_logo_url
            )
            print(json.dumps({"success": True, "output": args.output_path}))
        except Exception as e:
            print(f"Error processing logo: {e}", file=sys.stderr)
            sys.exit(1)

    def insert_intro(self, args):
        try:
            output = VideoService.insert_intro(
                args.video_input,
                args.intro_url,
                args.output_path,
                args.work_dir
            )
            print(json.dumps({"success": True, "output": output}))
        except Exception as e:
            print(f"Error inserting intro: {e}", file=sys.stderr)
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Video Controller")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_logo = subparsers.add_parser("process_logo", help="Process video logo replacement")
    p_logo.add_argument("video_input", help="Path to input video")
    p_logo.add_argument("logo_input", help="Path to logo file")
    p_logo.add_argument("detect_json", help="JSON string from detection")
    p_logo.add_argument("output_path", help="Path to output video")
    p_logo.add_argument("--new_logo_url", help="URL to download new logo if missing", default="")

    p_intro = subparsers.add_parser("insert_intro", help="Insert intro video")
    p_intro.add_argument("video_input", help="Path to input video")
    p_intro.add_argument("intro_url", help="URL to intro video")
    p_intro.add_argument("output_path", help="Path to output video")
    p_intro.add_argument("--work_dir", help="Working directory for temporary files", default="/tmp")

    p_pipe = subparsers.add_parser("pipeline", help="Run full video processing pipeline (Logo + Intro)")
    p_pipe.add_argument("video_input", help="Path to input video")
    p_pipe.add_argument("logo_input", help="Path to logo file")
    p_pipe.add_argument("detect_json", help="JSON string from detection")
    p_pipe.add_argument("output_path", help="Path to output video")
    p_pipe.add_argument("--new_logo_url", help="URL to download new logo if missing", default="")
    p_pipe.add_argument("--intro_url", help="URL to intro video", default="")
    p_pipe.add_argument("--work_dir", help="Working directory for temporary files", default="/tmp")
    # Effects
    p_pipe.add_argument("--flip", action="store_true", help="Flip video horizontally")
    p_pipe.add_argument("--zoom", type=float, default=1.0, help="Zoom factor (e.g., 1.1 for 110%)")
    p_pipe.add_argument("--brightness", type=float, default=0.0, help="Brightness adjustment (default 0.0)")
    p_pipe.add_argument("--saturation", type=float, default=1.0, help="Saturation adjustment (default 1.0)")
    p_pipe.add_argument("--hue", type=float, default=0.0, help="Hue adjustment (default 0.0)")
    p_pipe.add_argument("--background_music", help="Path to background music file", default=None)
    p_pipe.add_argument("--remove_text", action="store_true", help="Attempt to remove text using OCR")
    p_pipe.add_argument("--ai_dubbing", action="store_true", help="Enable AI Dubbing (Audio Rewrite)")
    p_pipe.add_argument("--gemini_key", help="Gemini API Key for text rewriting")
    p_pipe.add_argument("--openai_key", help="OpenAI API Key for TTS")
    p_pipe.add_argument("--tts_voice", help="TTS Voice ID (e.g. alloy, vi-VN-NamMinhNeural)", default="")
    p_pipe.add_argument("--target_language", help="Target language for translation", default=None)
    p_pipe.add_argument("--caption_enabled", action="store_true", help="Enable auto-generated captions")
    p_pipe.add_argument("--caption_font", help="Caption font name", default="Arial")
    p_pipe.add_argument("--caption_size", help="Caption font size", default="24")
    p_pipe.add_argument("--caption_color", help="Caption color (ASS Hex)", default="&H00FFFF")
    p_pipe.add_argument("--caption_position", help="Caption position (bottom/center)", default="bottom")
    p_pipe.add_argument("--video_speed", help="Video playback speed (e.g. 1.0, 1.25)", default="1.0")
    p_pipe.add_argument("--filter_nsfw", action="store_true", help="Enable NSFW content filtering")

    args = parser.parse_args()

    controller = VideoController()

    if args.command == "process_logo":
        controller.process_logo(args)
    elif args.command == "insert_intro":
        controller.insert_intro(args)
    elif args.command == "pipeline":
        try:
            gemini_key = args.gemini_key or os.getenv("GEMINI_API_KEY")
            openai_key = args.openai_key or os.getenv("OPENAI_API_KEY")


            output = VideoService.process_pipeline(
                args.video_input,
                args.logo_input,
                args.detect_json,
                args.output_path,
                args.new_logo_url,
                args.intro_url,
                args.work_dir,
                args.flip,
                args.zoom,
                args.brightness,
                args.saturation,
                args.hue,
                args.background_music,
                args.remove_text,
                args.ai_dubbing,
                gemini_key,
                openai_key,
                args.filter_nsfw,
                args.tts_voice,
                args.target_language,
                args.caption_enabled,
                args.caption_font,
                args.caption_size,
                args.caption_color,
                args.caption_position,
                float(args.video_speed)
            )
            print(json.dumps({"success": True, "output": output}))
        except Exception as e:
            print(f"Error in pipeline: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
