import os
import cv2
import json
from pathlib import Path
from nudenet import NudeDetector

from utils.command_utils import CommandUtils

class NSFWService:

    @staticmethod
    def detect_unsafe_segments(video_path, threshold=0.7, frame_interval=1.0):
        try:
            detector = NudeDetector()
        except Exception as e:
            print(f"Error initializing NudeNet: {e}")
            raise e

        print(f"DEBUG: Scanning video for NSFW content: {video_path}")
        
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        step_frames = int(fps * frame_interval)
        
        unsafe_frames = []
        
        current_frame = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if current_frame % step_frames == 0:
                timestamp = current_frame / fps
                h, w = frame.shape[:2]
                if w > 640:
                    scale = 640 / w
                    frame = cv2.resize(frame, (640, int(h * scale)))
                
                preds = detector.detect(frame)
                unsafe_classes = [
                    'BUTTOCKS_EXPOSED', 'FEMALE_BREAST_EXPOSED', 
                    'FEMALE_GENITALIA_EXPOSED', 'MALE_GENITALIA_EXPOSED', 
                    'ANUS_EXPOSED'
                ]
                
                is_unsafe = False
                for p in preds:
                    if p['label'] in unsafe_classes and p['score'] >= threshold:
                        is_unsafe = True
                        print(f"NSFW Found at {timestamp:.2f}s: {p['label']} ({p['score']:.2f})")
                        break
                
                if is_unsafe:
                    unsafe_frames.append(timestamp)

            current_frame += 1
            
        cap.release()
        
        if not unsafe_frames:
            return []

        segments = []
        if not unsafe_frames: return []
        
        start = unsafe_frames[0]
        end = unsafe_frames[0]
        
        buffer_time = frame_interval * 2.0
        
        for t in unsafe_frames[1:]:
            if t - end <= buffer_time:
                end = t
            else:
                segments.append((max(0, start - 1.0), end + 1.0))
                start = t
                end = t
        segments.append((max(0, start - 1.0), end + 1.0))
        
        print(f"Unsafe Segments to cut: {segments}")
        return segments

    @staticmethod
    def filter_video(video_path, output_path, work_dir="/tmp"):
        segments = NSFWService.detect_unsafe_segments(video_path)
        if not segments:
            return video_path

        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        cap.release()

        keep_segments = []
        current_time = 0.0
        
        for (cut_start, cut_end) in segments:
            if cut_start > current_time:
                keep_segments.append((current_time, cut_start))
            current_time = max(current_time, cut_end)
            
        if current_time < duration:
            keep_segments.append((current_time, duration))
            
        if not keep_segments:
            raise Exception("Video is entirely NSFW!")

        work_dir = Path(work_dir)
        concat_list_path = work_dir / f"concat_list_{Path(video_path).stem}.txt"
        segment_files = []
        
        with open(concat_list_path, "w") as f:
            for i, (start, end) in enumerate(keep_segments):
                seg_file = work_dir / f"seg_{i}_{Path(video_path).stem}.mp4"
                duration_seg = end - start
                cmd = (
                    f"ffmpeg -y -ss {start} -t {duration_seg} -i \"{video_path}\" "
                    f"-c:v libx264 -preset veryfast -c:a aac \"{seg_file}\""
                )
                CommandUtils.run_command(cmd)
                segment_files.append(seg_file)
                f.write(f"file '{seg_file}'\n")
        
        cmd_concat = (
            f"ffmpeg -y -f concat -safe 0 -i \"{concat_list_path}\" "
            f"-c copy \"{output_path}\""
        )
        try:
             CommandUtils.run_command(cmd_concat)
        except Exception as e:
             print(f"Error concatenating: {e}")
             return video_path

        for sf in segment_files:
            try: sf.unlink()
            except: pass
        try: concat_list_path.unlink()
        except: pass
            
        return output_path
