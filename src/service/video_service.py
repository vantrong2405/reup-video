import os
import sys
import json
import shutil
import subprocess
import re
from pathlib import Path

# Try to import TextService and AIService
HAS_TEXT_SERVICE = False
try:
    from service.text_service import TextService
    HAS_TEXT_SERVICE = True
except ImportError:
    pass

HAS_AI_SERVICE = False
try:
    from service.ai_service import AIService
    HAS_AI_SERVICE = True
except ImportError:
    pass

HAS_NSFW_SERVICE = False
try:
    from service.nsfw_service import NSFWService
    HAS_NSFW_SERVICE = True
except ImportError:
    pass

class VideoService:
    @staticmethod
    def _run_command(command, check=True):
        print(f"Running command: {command}")
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if check and result.returncode != 0:
            print(f"Command failed with output:\n{result.stdout}\n{result.stderr}", file=sys.stderr)
            raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
        return result

    @staticmethod
    def _download_file(url, output_path):
        print(f"Downloading from {url} to {output_path}")
        if url.startswith("file://"):
            local_path = url[7:]
            if os.path.exists(local_path):
                 shutil.copy(local_path, output_path)
                 return
        elif os.path.exists(url):
             shutil.copy(url, output_path)
             return

        final_url = url
        if "drive.google.com" in url:
            file_id = None
            match = re.search(r'/d/([^/]*)/', url)
            if match:
                file_id = match.group(1)
            else:
                match = re.search(r'[?&]id=([^&]*)', url)
                if match:
                    file_id = match.group(1)

            if not file_id and re.match(r'^[a-zA-Z0-9_-]+$', url):
                 file_id = url

            if file_id:
                final_url = f"https://drive.google.com/uc?export=download&id={file_id}"

        cmd = f"wget -O \"{output_path}\" \"{final_url}\""
        VideoService._run_command(cmd)

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception(f"Downloaded file is empty or not found: {output_path}")

    @staticmethod
    def process_logo(video_input, logo_input, detect_json_str, output_file, new_logo_url=None,
                     flip=False, zoom=1.0, brightness=0.0, saturation=1.0, hue=0.0, background_music=None,
                     remove_text=False):
        video_input = Path(video_input)
        logo_input = Path(logo_input)
        output_file = Path(output_file)

        if not video_input.exists():
            raise FileNotFoundError(f"Video file not found: {video_input}")

        if not logo_input.exists():
            if not new_logo_url:
                raise Exception(f"Logo file not found and new_logo_url is empty: {logo_input}")
            logo_input.parent.mkdir(parents=True, exist_ok=True)
            VideoService._download_file(new_logo_url, str(logo_input))

        detected_data = {"logos": [], "count": 0}
        try:
            json_match = re.search(r'\{.*"logos".*\}', detect_json_str)
            if json_match: detect_json_str = json_match.group(0)
            detected_data = json.loads(detect_json_str)
        except:
            print(f"Warning: Failed to parse detect_json.")

        logos = detected_data.get("logos", [])
        box = {"x": 0, "y": 0, "width": 0, "height": 0}
        old_logo_found = False
        if len(logos) > 0:
            old_logo_found = True
            l = logos[0]
            box = {k: int(l.get(k, 0)) for k in ["x", "y", "width", "height"]}

        try:
            cmd_w = f"ffprobe -v error -select_streams v:0 -show_entries stream=width  -of csv=p=0 \"{video_input}\""
            vid_w = int(VideoService._run_command(cmd_w).stdout.strip() or 0)
            cmd_h = f"ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 \"{video_input}\""
            vid_h = int(VideoService._run_command(cmd_h).stdout.strip() or 0)
        except Exception:
            vid_w, vid_h = 0, 0

        output_file.parent.mkdir(parents=True, exist_ok=True)

        current_stream = "[0:v]"
        filter_parts = []

        if old_logo_found:
            # User requested "overlay 4 phía logo mới cho gọn" -> Tight fit
            expand = 0 # No extra black box expansion
            dx = max(0, box["x"] - expand)
            dy = max(0, box["y"] - expand)
            dw = box["width"] + expand * 2
            dh = box["height"] + expand * 2
            if vid_w > 0: dw = min(dw, vid_w - dx)
            if vid_h > 0: dh = min(dh, vid_h - dy)

            filter_parts.append(f"{current_stream}delogo=x={dx}:y={dy}:w={dw}:h={dh}[v_delogo]")
            current_stream = "[v_delogo]"
            # Drawbox helps if new logo has transparency, but keep it tight
            filter_parts.append(f"{current_stream}drawbox=x={dx}:y={dy}:w={dw}:h={dh}:color=black@1.0:t=fill[v_clean]")
            current_stream = "[v_clean]"
            
            # CRITICAL FIX: Apply logo overlay IMMEDIATELY after drawbox, BEFORE zoom/flip
            # This ensures logo and black box get same coordinate transformation
            new_w = dw
            new_h = dh
            new_x = dx
            new_y = dy
            filter_parts.append(f"[1:v]scale={new_w}:{new_h}[logo]")
            filter_parts.append(f"{current_stream}[logo]overlay={new_x}:{new_y}[v_with_logo]")
            current_stream = "[v_with_logo]"

        if remove_text and HAS_TEXT_SERVICE:
            print("DEBUG: Running OCR...")
            try:
                ocr_filters, _ = TextService.generate_mask_filters(video_input)
                if ocr_filters:
                    filter_parts.append(f"{current_stream}{ocr_filters}[v_text_removed]")
                    current_stream = "[v_text_removed]"
            except Exception as e:
                print(f"OCR Failed: {e}")

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

        # Handle case when no old logo was found - place logo at corner
        if not old_logo_found:
            padding = 10
            new_w, new_h = 220, 110
            new_x = vid_w - new_w - padding if vid_w > 0 else 10
            new_y = padding
            if flip and vid_w > 0:
                new_x = vid_w - new_x - new_w
            filter_parts.append(f"[1:v]scale={new_w}:{new_h}[logo]")
            filter_parts.append(f"{current_stream}[logo]overlay={new_x}:{new_y}[v_with_logo]")
            current_stream = "[v_with_logo]"

        # Rename final stream for consistency
        if current_stream != "[v_final]":
            # Use nullsink workaround or just use current stream as final
            pass
        
        # Replace last stream label with v_final for the ffmpeg command
        if filter_parts:
            last_filter = filter_parts[-1]
            # Replace the output label with [v_final]
            import re
            filter_parts[-1] = re.sub(r'\[v_\w+\]$', '[v_final]', last_filter)

        filter_complex = ";".join(filter_parts)

        audio_stream = "-map 0:a?"
        input_music = ""
        if background_music and Path(background_music).exists():
              input_music = f"-stream_loop -1 -i \"{background_music}\""
              audio_stream = "-map 2:a -shortest"

        cmd = (
            f"nice -n 10 ffmpeg -y "
            f"-i \"{video_input}\" "
            f"-i \"{logo_input}\" "
            f"{input_music} "
            f"-filter_complex \"{filter_complex}\" "
            f"-map \"[v_final]\" {audio_stream} "
            f"-c:v libx264 -preset veryfast -crf 25 "
            f"-c:a aac -ar 44100 -b:a 128k "
            f"\"{output_file}\""
        )

        VideoService._run_command(cmd)

        if not output_file.exists():
            raise Exception("Main FFmpeg failed to create output file")

        return str(output_file)

    @staticmethod
    def process_ai_dubbing(video_path, gemini_api_key, work_dir="/tmp", openai_key=None, tts_voice="",
                           target_language=None, caption_enabled=False, caption_font="Arial", caption_size="24",
                           caption_color="&H00FFFF", caption_position="bottom", video_speed=1.0, audio_source_path=None):
        if not HAS_AI_SERVICE:
            print("AI Service dependencies not installed. Skipping AI Dubbing.")
            return video_path

        work_dir = Path(work_dir)
        video_stem = Path(video_path).stem
        
        # Use separate source for audio extraction if provided, else use video_path
        extract_source = audio_source_path if audio_source_path else video_path
        
        audio_ext = work_dir / f"{video_stem}_extracted.mp3"
        audio_tts = work_dir / f"{video_stem}_tts_new.mp3"
        srt_path = work_dir / f"{video_stem}.srt"
        video_output = work_dir / f"{video_stem}_dubbed.mp4"

        try:
            print(f"--- AI Dubbing Step 1: Extract Audio (Source: {extract_source}) ---")
            cmd = f"ffmpeg -y -i \"{extract_source}\" -q:a 0 -map a \"{audio_ext}\""
            VideoService._run_command(cmd)

            print("--- AI Dubbing Step 2: Transcribe (Whisper) ---")
            original_text = AIService.transcribe_audio(audio_ext)
            print(f"Original Text: {original_text[:100]}...")

            print("--- AI Dubbing Step 3: Rewrite & Translate (Gemini) ---")
            new_script = AIService.rewrite_text(original_text, gemini_api_key, target_language)
            print(f"New Script (Target Lang: {target_language}): {new_script[:100]}...")

            print("--- AI Dubbing Step 4: TTS ---")
            if openai_key: print("Using OpenAI TTS")
            AIService.run_tts_sync(new_script, audio_tts, openai_key=openai_key, voice=tts_voice, language=target_language)

            srt_filter = ""
            if caption_enabled:
                 print("--- AI Dubbing Step 4.5: Generating Subtitles (Whisper) ---")
                 AIService.transcribe_audio_to_srt(audio_tts, srt_path)

                 # Configure ASS style
                 # Alignment: 2=Bottom Center, 5=Top Center? No, ASS Alignment: 2 is Bottom Center.
                 align = 2 # Default bottom
                 if caption_position.lower() == "center": align = 5
                 if caption_position.lower() == "top": align = 6

                 # ForceStyle string
                 style = f"Fontname={caption_font},FontSize={caption_size},PrimaryColour={caption_color},Alignment={align},Outline=1,Shadow=1"
                 # Escape colons in Windows paths if needed, but we are on Linux.
                 # Filter complex requires escaping
                 escaped_srt = str(srt_path).replace(":", "\\:").replace("'", "\\'")
                 srt_filter = f"subtitles='{escaped_srt}':force_style='{style}'"

            print("--- AI Dubbing Step 5: Merge Audio & Subtitles & Speed ---")

            cmd_merge = ""

            # Build filters
            v_filters = []
            if srt_filter: v_filters.append(srt_filter)
            if video_speed != 1.0: v_filters.append(f"setpts=PTS/{video_speed}")

            a_filters = []
            if video_speed != 1.0: a_filters.append(f"atempo={video_speed}")

            if v_filters or a_filters:
                 # Complex filter chain
                 # Video chain: [0:v] -> filters -> [v_out]
                 # Audio chain: [1:a] -> filters -> [a_out]

                 filter_str = ""
                 map_v = "0:v"
                 map_a = "1:a"

                 if v_filters:
                     filter_str += f"[0:v]{','.join(v_filters)}[v_out];"
                     map_v = "[v_out]"

                 if a_filters:
                     filter_str += f"[1:a]{','.join(a_filters)}[a_out]"
                     map_a = "[a_out]"
                 else:
                     if filter_str.endswith(";"): filter_str = filter_str[:-1]

                 cmd_merge = (
                    f"ffmpeg -y -i \"{video_path}\" -i \"{audio_tts}\" "
                    f"-filter_complex \"{filter_str}\" "
                    f"-map \"{map_v}\" -map \"{map_a}\" "
                    f"-c:v libx264 -preset veryfast -crf 23 "
                    f"-c:a aac -b:a 192k -shortest "
                    f"\"{video_output}\""
                 )
            else:
                # Original merge logic if no filters
                cmd_merge = (
                    f"ffmpeg -y -i \"{video_path}\" -i \"{audio_tts}\" "
                    f"-c:v copy -map 0:v -map 1:a -shortest \"{video_output}\""
                )

            VideoService._run_command(cmd_merge)

            return str(video_output)

        except Exception as e:
            print(f"AI Dubbing failed: {e}")
            # Fallback: return original video
            return str(video_path)

    @staticmethod
    def process_pipeline(video_input, logo_input, detect_json_str, output_path, new_logo_url=None, intro_url=None, work_dir="/tmp",
                         flip=False, zoom=1.0, brightness=0.0, saturation=1.0, hue=0.0, background_music=None, remove_text=False,
                         ai_dubbing=False, gemini_api_key=None, openai_key=None, filter_nsfw=False, tts_voice="",
                         target_language=None, caption_enabled=False, caption_font="Arial", caption_size="24",
                         caption_color="&H00FFFF", caption_position="bottom", video_speed=1.0):
        work_dir = Path(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)

        current_input = video_input

        if filter_nsfw:
            if HAS_NSFW_SERVICE:
                print("--- Step 0: NSFW Filtering ---")
                filtered_video = work_dir / f"nsfw_filtered_{Path(video_input).stem}.mp4"
                processed_video = NSFWService.filter_video(current_input, str(filtered_video), work_dir)
                if processed_video != current_input:
                    current_input = processed_video
                    print(f"NSFW Filter applied. New input: {current_input}")
                else:
                    print("No NSFW content detected.")
            else:
                print("Warning: NSFW Service not available. Skipping filter.")

        temp_processed_logo = work_dir / f"temp_logo_processed_{Path(video_input).stem}.mp4"

        print("--- Step 1: Processing Logo & Effects ---")
        VideoService.process_logo(
            current_input, logo_input, detect_json_str, temp_processed_logo, new_logo_url,
            flip, zoom, brightness, saturation, hue, background_music, remove_text
        )

        current_video_stage = temp_processed_logo
        if ai_dubbing and gemini_api_key:
            print("--- Step 1.5: AI Dubbing ---")
            dubbed_output = VideoService.process_ai_dubbing(
                current_video_stage, gemini_api_key, work_dir, openai_key, tts_voice,
                target_language, caption_enabled, caption_font, caption_size, caption_color, caption_position, video_speed,
                audio_source_path=video_input
            )
            current_video_stage = Path(dubbed_output)

        print("--- Step 2: Inserting Intro ---")
        final_output = VideoService.insert_intro(current_video_stage, intro_url, output_path, work_dir)

        if temp_processed_logo.exists() and temp_processed_logo != current_video_stage:
             try: temp_processed_logo.unlink()
             except: pass

        return final_output

    @staticmethod
    def insert_intro(video_input_path, intro_url, output_path, work_dir_path):
        video_input = Path(video_input_path)
        output_path = Path(output_path)
        work_dir = Path(work_dir_path)
        work_dir.mkdir(parents=True, exist_ok=True)

        video_output_temp = work_dir / f"{video_input.stem}_temp_concat.mp4"
        intro_video_path = work_dir / f"intro_{video_input.stem}.mp4"
        intro_scaled_path = work_dir / f"intro_scaled_{video_input.stem}.mp4"

        if not video_input.exists():
             raise FileNotFoundError(f"Processed video file not found: {video_input}")

        if not intro_url:
            shutil.copy(video_input, output_path)
            return str(output_path)

        VideoService._download_file(intro_url, str(intro_video_path))

        try:
            main_w = int(VideoService._run_command(f"ffprobe -v error -select_streams v:0 -show_entries stream=width  -of csv=p=0 \"{video_input}\"").stdout.strip() or 0)
            main_h = int(VideoService._run_command(f"ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 \"{video_input}\"").stdout.strip() or 0)
            main_fps = VideoService._run_command(f"ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 \"{video_input}\"").stdout.strip()

            audio_check = VideoService._run_command(f"ffprobe -v error -select_streams a:0 -count_frames -show_entries stream=codec_name -of csv=p=0 \"{video_input}\"", check=False)
            main_has_audio = bool(audio_check.stdout.strip())
        except Exception as e:
            raise Exception(f"Failed to probe main video: {e}")

        intro_has_audio = False
        if main_has_audio:
            intro_audio_check = VideoService._run_command(f"ffprobe -v error -select_streams a:0 -count_frames -show_entries stream=codec_name -of csv=p=0 \"{intro_video_path}\"", check=False)
            intro_has_audio = bool(intro_audio_check.stdout.strip())

        scale_filter = (
            f"scale={main_w}:{main_h}:force_original_aspect_ratio=decrease,"
            f"pad={main_w}:{main_h}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"fps={main_fps}"
        )

        intro_cmd_parts = [
            f"ffmpeg -y -i \"{intro_video_path}\""
        ]

        if main_has_audio:
            if intro_has_audio:
                intro_cmd_parts.append(f"-vf \"{scale_filter}\" -af \"aresample=48000:resampler=soxr\"")
            else:
                 intro_cmd_parts.append(
                     f"-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000 "
                     f"-vf \"{scale_filter}\" -c:a aac -ar 48000 -ac 2 -b:a 128k -shortest"
                 )
        else:
             intro_cmd_parts.append(f"-vf \"{scale_filter}\"")

        intro_cmd_parts.append(f"-c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p")

        if main_has_audio and intro_has_audio:
             intro_cmd_parts.append(f"-c:a aac -ar 48000 -ac 2 -b:a 128k")

        intro_cmd_parts.append(f"\"{intro_scaled_path}\"")

        VideoService._run_command(" ".join(intro_cmd_parts))

        concat_cmd = ""
        if main_has_audio:
            concat_cmd = (
                f"ffmpeg -y -i \"{intro_scaled_path}\" -i \"{video_input}\" "
                f"-filter_complex \"[0:a]aresample=48000:resampler=soxr[a0];[0:v][a0][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]\" "
                f"-map \"[outv]\" -map \"[outa]\" "
                f"-c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p "
                f"-c:a aac -ar 48000 -ac 2 -b:a 128k "
                f"\"{output_path}\""
            )
        else:
            concat_cmd = (
                f"ffmpeg -y -i \"{intro_scaled_path}\" -i \"{video_input}\" "
                f"-filter_complex \"[0:v][1:v]concat=n=2:v=1[outv]\" "
                f"-map \"[outv]\" "
                f"-c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p "
                f"\"{output_path}\""
            )

        VideoService._run_command(concat_cmd)

        if intro_scaled_path.exists(): intro_scaled_path.unlink()
        if intro_video_path.exists(): intro_video_path.unlink()

        return str(output_path)
