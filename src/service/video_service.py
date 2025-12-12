import os
import sys
import json
import shutil
import subprocess
import re
from pathlib import Path

from service.text_service import TextService
from service.nsfw_service import NSFWService
from service.ai_service import AIService
from utils.command_utils import CommandUtils
from utils.file_utils import FileUtils
from utils.video_utils import VideoUtils
from utils.signature_utils import SignatureUtils

DEFAULT_FFMPEG_PRESET = "veryfast"
DEFAULT_BG_MUSIC_VOLUME = 0.3
DEFAULT_LOGO_WIDTH = 220
DEFAULT_LOGO_PADDING = 10
DEFAULT_LOGO_POSITION = "top-right"
DEFAULT_OCR_EXPAND = 10
DEFAULT_OCR_FRAMES = 2
DEFAULT_SPLIT_DURATION = 10.0
DEFAULT_SPLIT_MIN = 5.0
DEFAULT_SPLIT_LIMIT = 5

class VideoService:

    @staticmethod
    def process_pipeline(video_input, logo_input, detect_json_str, output_path, new_logo_url=None, intro_url=None, work_dir="/tmp",
                         flip=False, zoom=1.0, speed=1.0, brightness=0.0, saturation=1.0, hue=0.0, background_music=None, remove_text=False,
                         filter_nsfw=False, logo_width=DEFAULT_LOGO_WIDTH, logo_height=None, logo_padding=DEFAULT_LOGO_PADDING, logo_position=DEFAULT_LOGO_POSITION,
                         ffmpeg_preset=DEFAULT_FFMPEG_PRESET, delogo_expand=0, bg_music_volume=DEFAULT_BG_MUSIC_VOLUME, ocr_languages=['en'],
                         ocr_expand=DEFAULT_OCR_EXPAND, ocr_max_frames=DEFAULT_OCR_FRAMES, gemini_key=None,
                         split_mode='none', split_start="00:00:00", split_duration=DEFAULT_SPLIT_DURATION, split_min_duration=DEFAULT_SPLIT_MIN, split_limit=DEFAULT_SPLIT_LIMIT,
                         unique_mode=False, watermark_text=None, watermark_opacity=0.15, watermark_size=18, watermark_speed=50, watermark_position="bottom"):
        work_dir = Path(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)

        current_input = video_input

        if split_mode != 'none':
            print(f"--- Step -1: Splitting Video ({split_mode}) ---")
            split_files = VideoService.split_video_raw(
                video_input, work_dir, split_mode, split_start, split_duration, split_min_duration, split_limit, Path(video_input).stem
            )
            if split_files:
                current_input = split_files[0]
                print(f"Using split video as input: {current_input}")
            else:
                raise ValueError(f"Split mode '{split_mode}' failed to produce any output files.")

        if filter_nsfw:
            print("--- Step 0: NSFW Filtering ---")
            filtered_video = work_dir / f"nsfw_filtered_{Path(video_input).stem}.mp4"
            processed_video = NSFWService.filter_video(current_input, str(filtered_video), work_dir)
            if processed_video != current_input:
                current_input = processed_video

        temp_processed_logo = work_dir / f"temp_logo_processed_{Path(video_input).stem}.mp4"

        print("--- Step 1: Processing Logo & Effects ---")
        VideoService.process_logo(
            current_input, logo_input, detect_json_str, temp_processed_logo, new_logo_url,
            flip, zoom, speed, brightness, saturation, hue, background_music, remove_text,
            filter_nsfw=filter_nsfw,
            logo_width=logo_width, logo_height=logo_height, logo_padding=logo_padding, logo_position=logo_position,
            ffmpeg_preset=ffmpeg_preset, delogo_expand=delogo_expand, bg_music_volume=bg_music_volume, ocr_languages=ocr_languages,
            ocr_expand=ocr_expand, ocr_max_frames=ocr_max_frames, gemini_key=gemini_key,
            unique_mode=unique_mode, watermark_text=watermark_text, watermark_opacity=watermark_opacity,
            watermark_size=watermark_size, watermark_speed=watermark_speed, watermark_position=watermark_position
        )

        current_video_stage = temp_processed_logo

        print("--- Step 2: Inserting Intro ---")
        final_output = VideoService.insert_intro(current_video_stage, intro_url, output_path, work_dir)

        return final_output

    @staticmethod
    def process_logo(video_input, logo_input, detect_json_str, output_file, new_logo_url=None,
                     flip=False, zoom=1.0, speed=1.0, brightness=0.0, saturation=1.0, hue=0.0, background_music=None, remove_text=False,
                     filter_nsfw=False, logo_width=DEFAULT_LOGO_WIDTH, logo_height=None, logo_padding=DEFAULT_LOGO_PADDING, logo_position=DEFAULT_LOGO_POSITION,
                     ffmpeg_preset=DEFAULT_FFMPEG_PRESET, delogo_expand=0, bg_music_volume=DEFAULT_BG_MUSIC_VOLUME, ocr_languages=['en'],
                     ocr_expand=DEFAULT_OCR_EXPAND, ocr_max_frames=DEFAULT_OCR_FRAMES, gemini_key=None,
                     unique_mode=False, watermark_text=None, watermark_opacity=0.15, watermark_size=18, watermark_speed=50, watermark_position="bottom"):
        video_input = Path(video_input)
        logo_input = Path(logo_input)
        output_file = Path(output_file)

        VideoService._ensure_inputs(video_input, logo_input, new_logo_url)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        old_logo_found, box = VideoService._parse_logo_detection(detect_json_str)
        video_info = VideoUtils.get_video_info(video_input)
        vid_w = video_info["width"]
        vid_h = video_info["height"]
        has_audio = video_info["has_audio"]

        filter_complex_parts, final_video_stream = VideoService._build_visual_filters(
            video_input, "[0:v]", old_logo_found, box, vid_w, vid_h,
            delogo_expand, logo_width, logo_height, logo_padding, logo_position,
            flip, zoom, speed, brightness, saturation, hue, remove_text, ocr_languages,
            ocr_expand=ocr_expand, ocr_max_frames=ocr_max_frames, gemini_key=gemini_key,
            unique_mode=unique_mode, watermark_text=watermark_text, watermark_opacity=watermark_opacity,
            watermark_size=watermark_size, watermark_speed=watermark_speed, watermark_position=watermark_position
        )

        visual_filter_str = ";".join(filter_complex_parts)

        input_music_flag, audio_map_arg, final_filter_complex = VideoService._build_audio_config(
            background_music, bg_music_volume, speed, visual_filter_str, has_audio, unique_mode
        )

        vid_map_arg = f"-map \"{final_video_stream}\""

        cmd_parts = [
            f"ffmpeg -y",
            f"-i \"{video_input}\"",
            f"-i \"{logo_input}\"",
            f"{input_music_flag}",
            f"-filter_complex \"{final_filter_complex}\"",
            f"{vid_map_arg} {audio_map_arg}"
        ]

        if unique_mode:
             print("Applying Unique Signature Metadata...")
             metadata = SignatureUtils.get_random_metadata()
             for k, v in metadata.items():
                 cmd_parts.append(f"-metadata {k}='{v}'")

        cmd_parts.append(f"-c:v libx264 -preset {ffmpeg_preset} -crf 25")
        cmd_parts.append(f"-c:a aac -ar 44100 -b:a 128k")
        cmd_parts.append(f"\"{output_file}\"")

        cmd = " ".join(cmd_parts)
        print(f"Executing FFmpeg: {cmd[:200]}...")
        
        CommandUtils.run_command(cmd)

        if not output_file.exists():
            raise Exception("FFmpeg failed to create output file")

        return str(output_file)

    @staticmethod
    def split_video_raw(input_path, output_dir, mode='manual', start_time="00:00:00", duration=10.0, min_duration=5.0, limit=5, base_name="video"):
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        split_files = []

        if mode == 'manual':
            out_file = output_dir / f"{base_name}_cut_manual.mp4"
            cmd = f"ffmpeg -y -ss {start_time} -i \"{input_path}\" -t {duration} -c:v libx264 -preset veryfast -crf 23 -c:a aac \"{out_file}\""
            CommandUtils.run_command(cmd)
            if out_file.exists() and out_file.stat().st_size > 0:
                split_files.append(str(out_file))
        elif mode == 'auto':
            detect_cmd = f"ffmpeg -i \"{input_path}\" -vf \"select='gt(scene,0.4)',showinfo\" -f null -"
            result = subprocess.run(detect_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            timestamps = [0.0]
            for line in result.stderr.split('\n'):
                if "pts_time:" in line:
                    m = re.search(r'pts_time:([0-9.]+)', line)
                    if m: timestamps.append(float(m.group(1)))
            dur_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \"{input_path}\""
            total_duration = float(subprocess.check_output(dur_cmd, shell=True).strip())
            timestamps.append(total_duration)
            segments = [(timestamps[i], timestamps[i+1] - timestamps[i]) for i in range(len(timestamps)-1) if timestamps[i+1] - timestamps[i] >= min_duration][:limit]
            for idx, (start, dur) in enumerate(segments):
                out_file = output_dir / f"{base_name}_scene_{idx+1}.mp4"
                cmd = f"ffmpeg -y -ss {start} -i \"{input_path}\" -t {dur} -c copy -avoid_negative_ts 1 \"{out_file}\""
                CommandUtils.run_command(cmd)
                if out_file.exists(): split_files.append(str(out_file))
        return split_files

    @staticmethod
    def insert_intro(video_input_path, intro_url, output_path, work_dir_path):
        video_input = Path(video_input_path)
        output_path = Path(output_path)
        work_dir = Path(work_dir_path)
        work_dir.mkdir(parents=True, exist_ok=True)
        intro_video_path = work_dir / f"intro_{video_input.stem}.mp4"
        intro_scaled_path = work_dir / f"intro_scaled_{video_input.stem}.mp4"

        if not video_input.exists():
             raise FileNotFoundError(f"Processed video not found: {video_input}")

        if not intro_url:
            shutil.copy(video_input, output_path)
            return str(output_path)

        FileUtils.download_file(intro_url, str(intro_video_path))
        main_info = VideoUtils.get_video_info(video_input)
        intro_info = VideoUtils.get_video_info(intro_video_path)

        scale_filter = f"scale={main_info['width']}:{main_info['height']}:force_original_aspect_ratio=decrease,pad={main_info['width']}:{main_info['height']}:(ow-iw)/2:(oh-ih)/2:black,fps={main_info['fps']}"
        
        intro_cmd = f"ffmpeg -y -i \"{intro_video_path}\""
        if main_info['has_audio']:
            if intro_info['has_audio']:
                intro_cmd += f" -vf \"{scale_filter}\" -af \"aresample=48000\" -c:v libx264 -preset veryfast -crf 23 -c:a aac -ar 48000 \"{intro_scaled_path}\""
            else:
                intro_cmd += f" -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000 -vf \"{scale_filter}\" -c:v libx264 -preset veryfast -crf 23 -c:a aac -ar 48000 -shortest \"{intro_scaled_path}\""
        else:
            intro_cmd += f" -vf \"{scale_filter}\" -c:v libx264 -preset veryfast -crf 23 -an \"{intro_scaled_path}\""
        CommandUtils.run_command(intro_cmd)

        if main_info['has_audio']:
            concat_cmd = f"ffmpeg -y -i \"{intro_scaled_path}\" -i \"{video_input}\" -filter_complex \"[0:a]aresample=48000[a0];[0:v][a0][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]\" -map \"[outv]\" -map \"[outa]\" -c:v libx264 -preset veryfast -crf 23 -c:a aac -ar 48000 \"{output_path}\""
        else:
            concat_cmd = f"ffmpeg -y -i \"{intro_scaled_path}\" -i \"{video_input}\" -filter_complex \"[0:v][1:v]concat=n=2:v=1[outv]\" -map \"[outv]\" -c:v libx264 -preset veryfast -crf 23 \"{output_path}\""
        CommandUtils.run_command(concat_cmd)

        for f in [intro_scaled_path, intro_video_path]:
            if f.exists(): f.unlink()
        return str(output_path)

    @staticmethod
    def _ensure_inputs(video_input, logo_input, new_logo_url):
        if not video_input.exists():
            raise FileNotFoundError(f"Video not found: {video_input}")
        if not logo_input.exists():
            if not new_logo_url:
                raise Exception(f"Logo not found: {logo_input}")
            logo_input.parent.mkdir(parents=True, exist_ok=True)
            FileUtils.download_file(new_logo_url, str(logo_input))

    @staticmethod
    def _parse_logo_detection(detect_json_str):
        detected_data = {"logos": [], "count": 0}
        try:
            json_match = re.search(r'\{.*"logos".*\}', detect_json_str)
            if json_match: detect_json_str = json_match.group(0)
            parsed = json.loads(detect_json_str)
            if isinstance(parsed, dict): detected_data = parsed
            elif isinstance(parsed, list): detected_data = {"logos": parsed, "count": len(parsed)}
        except: pass
        logos = detected_data.get("logos", [])
        box = {"x": 0, "y": 0, "width": 0, "height": 0}
        old_logo_found = len(logos) > 0
        if old_logo_found:
            l = logos[0]
            box = {k: int(l.get(k, 0)) for k in ["x", "y", "width", "height"]}
        return old_logo_found, box

    @staticmethod
    def _build_visual_filters(video_input, current_stream, old_logo_found, box, vid_w, vid_h,
                              delogo_expand, logo_width, logo_height, logo_padding, logo_position,
                              flip, zoom, speed, brightness, saturation, hue, remove_text, ocr_languages=['en'],
                              ocr_expand=DEFAULT_OCR_EXPAND, ocr_max_frames=DEFAULT_OCR_FRAMES, gemini_key=None,
                              unique_mode=False, watermark_text=None, watermark_opacity=0.15, watermark_size=18, watermark_speed=50, watermark_position="bottom"):
        filter_parts = []

        if old_logo_found:
            expand = delogo_expand
            dx, dy = max(0, box["x"] - expand), max(0, box["y"] - expand)
            dw, dh = box["width"] + expand * 2, box["height"] + expand * 2
            if vid_w > 0: dw = min(dw, vid_w - dx)
            if vid_h > 0: dh = min(dh, vid_h - dy)
            filter_parts.append(f"{current_stream}delogo=x={dx}:y={dy}:w={dw}:h={dh}[v_delogo]")
            current_stream = "[v_delogo]"
            filter_parts.append(f"{current_stream}drawbox=x={dx}:y={dy}:w={dw}:h={dh}:color=black@1.0:t=fill[v_clean]")
            current_stream = "[v_clean]"
            filter_parts.append(f"[1:v]scale={dw}:{dh}[logo]")
            filter_parts.append(f"{current_stream}[logo]overlay={dx}:{dy}[v_with_logo]")
            current_stream = "[v_with_logo]"

        if remove_text:
            ocr_filters, _ = TextService.generate_mask_filters(video_input, languages=ocr_languages, expand=ocr_expand, max_frames=ocr_max_frames, vid_w=vid_w, vid_h=vid_h)
            if ocr_filters:
                filter_parts.append(f"{current_stream}{ocr_filters}[v_text_removed]")
                current_stream = "[v_text_removed]"

        if flip:
            filter_parts.append(f"{current_stream}hflip[v_flipped]")
            current_stream = "[v_flipped]"

        if zoom > 1.0:
            z_w, z_h = int(vid_w * zoom), int(vid_h * zoom)
            filter_parts.append(f"{current_stream}scale={z_w}:{z_h},crop={vid_w}:{vid_h}:(iw-ow)/2:(ih-oh)/2[v_zoomed]")
            current_stream = "[v_zoomed]"

        effects = []
        if brightness != 0.0 or saturation != 1.0: effects.append(f"eq=brightness={brightness}:saturation={saturation}")
        if hue != 0.0: effects.append(f"hue=h={hue}")
        if effects:
            filter_parts.append(f"{current_stream}{','.join(effects)}[v_colored]")
            current_stream = "[v_colored]"

        if speed != 1.0:
            filter_parts.append(f"{current_stream}setpts={1.0/speed}*PTS[v_speed]")
            current_stream = "[v_speed]"

        if unique_mode:
            print("Applying Unique Visual Signature...")
            unique_filters = SignatureUtils.get_visual_filters()
            filter_parts.append(f"{current_stream}{','.join(unique_filters)}[v_unique]")
            current_stream = "[v_unique]"

        if watermark_text:
            print(f"Applying Watermark: {watermark_text}")
            wm_filter = SignatureUtils.get_watermark_filter_static(watermark_text, watermark_opacity, watermark_size, watermark_position)
            if wm_filter:
                filter_parts.append(f"{current_stream}{wm_filter}[v_watermark]")
                current_stream = "[v_watermark]"

        if not old_logo_found:
            padding = logo_padding
            new_w, new_h = logo_width, logo_height if logo_height else -1
            pos_map = {"top-right": (f"W-w-{padding}", f"{padding}"), "top-left": (f"{padding}", f"{padding}"),
                       "bottom-right": (f"W-w-{padding}", f"H-h-{padding}"), "bottom-left": (f"{padding}", f"H-h-{padding}")}
            x_expr, y_expr = pos_map.get(logo_position, pos_map["top-right"])
            filter_parts.append(f"[1:v]scale={new_w}:{new_h}[logo]")
            filter_parts.append(f"{current_stream}[logo]overlay={x_expr}:{y_expr}[v_with_logo]")
            current_stream = "[v_with_logo]"

        if filter_parts:
            last_filter = filter_parts[-1]
            if re.search(r'\[\w+\]$', last_filter):
                filter_parts[-1] = re.sub(r'\[\w+\]$', '[v_final]', last_filter)
        return filter_parts, "[v_final]" if filter_parts else current_stream

    @staticmethod
    def _build_audio_config(background_music, bg_music_volume, speed, filter_complex_str, original_has_audio=True, unique_mode=False):
        if not (background_music and Path(background_music).exists()):
            if speed != 1.0:
                if not original_has_audio: return "", "", filter_complex_str
                audio_filter = f"[0:a]atempo={speed}[a_out]"
                filter_complex_str = f"{filter_complex_str};{audio_filter}" if filter_complex_str else audio_filter
                return "", "-map \"[a_out]\"", filter_complex_str
            if original_has_audio:
                if unique_mode:
                    audio_sig = ",".join(SignatureUtils.get_audio_filters())
                    audio_filter = f"[0:a]{audio_sig}[a_out]"
                    filter_complex_str = f"{filter_complex_str};{audio_filter}" if filter_complex_str else audio_filter
                    return "", "-map \"[a_out]\"", filter_complex_str
                return "", "-map \"0:a?\"", filter_complex_str
            return "", "", filter_complex_str
        input_music_flag = f"-stream_loop -1 -i \"{background_music}\""
        audio_setup = f"[0:a]atempo={speed},volume=1.0[a1]" if speed != 1.0 else "[0:a]volume=1.0[a1]"
        audio_filter = f"{audio_setup};[2:a]volume={bg_music_volume}[a2];[a1][a2]amix=inputs=2:duration=first[a_out]" if original_has_audio else f"[2:a]volume={bg_music_volume}[a_out]"
        filter_complex_str = f"{filter_complex_str};{audio_filter}" if filter_complex_str else audio_filter
        return input_music_flag, "-map \"[a_out]\"", filter_complex_str
