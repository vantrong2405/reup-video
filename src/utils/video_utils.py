from utils.command_utils import CommandUtils

class VideoUtils:
    @staticmethod
    def get_video_info(video_input):
        info = {
            "width": 0, "height": 0, "fps": "30", "duration": 0.0, "has_audio": False
        }
        
        cmd_w = f"ffprobe -v error -select_streams v:0 -show_entries stream=width  -of csv=p=0 \"{video_input}\""
        info["width"] = int(CommandUtils.run_command(cmd_w).stdout.strip() or 0)
        
        cmd_h = f"ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 \"{video_input}\""
        info["height"] = int(CommandUtils.run_command(cmd_h).stdout.strip() or 0)
        
        cmd_fps = f"ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 \"{video_input}\""
        info["fps"] = CommandUtils.run_command(cmd_fps).stdout.strip()

        cmd_dur = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \"{video_input}\""
        try:
            info["duration"] = float(CommandUtils.run_command(cmd_dur).stdout.strip())
        except: pass

        cmd_a = f"ffprobe -v error -select_streams a:0 -count_frames -show_entries stream=codec_name -of csv=p=0 \"{video_input}\""
        audio_out = CommandUtils.run_command(cmd_a, check=False).stdout.strip()
        info["has_audio"] = bool(audio_out)
        
        return info
