from api.tasks.celery_app import celery_app
from service.video_service import VideoService


@celery_app.task(bind=True, name="video.pipeline")
def process_pipeline_task(self, video_input: str, logo_input: str, detect_json: str,
                          output_path: str, **kwargs):
    try:
        self.update_state(state="PROCESSING", meta={"progress": 0})
        
        result = VideoService.process_pipeline(
            video_input=video_input,
            logo_input=logo_input,
            detect_json_str=detect_json,
            output_path=output_path,
            new_logo_url=kwargs.get("new_logo_url"),
            intro_url=kwargs.get("intro_url"),
            work_dir=kwargs.get("work_dir", "/tmp"),
            flip=kwargs.get("flip", False),
            zoom=kwargs.get("zoom", 1.0),
            speed=kwargs.get("speed", 1.0),
            brightness=kwargs.get("brightness", 0.0),
            saturation=kwargs.get("saturation", 1.0),
            hue=kwargs.get("hue", 0.0),
            background_music=kwargs.get("background_music"),
            bg_music_volume=kwargs.get("bg_music_volume", 0.3),
            remove_text=kwargs.get("remove_text", False),
            ocr_languages=kwargs.get("ocr_languages", ["en"]),
            gemini_key=kwargs.get("gemini_key"),
            filter_nsfw=kwargs.get("filter_nsfw", False),
            ffmpeg_preset=kwargs.get("ffmpeg_preset", "veryfast"),
            split_mode=kwargs.get("split_mode", "none"),
            split_start=kwargs.get("split_start", "00:00:00"),
            split_duration=kwargs.get("split_duration", 10.0),
            split_limit=kwargs.get("split_limit", 5),
            unique_mode=kwargs.get("unique_mode", False),
            watermark_text=kwargs.get("watermark_text"),
            watermark_opacity=kwargs.get("watermark_opacity", 0.15),
            watermark_size=kwargs.get("watermark_size", 18),
            watermark_speed=kwargs.get("watermark_speed", 50),
            watermark_position=kwargs.get("watermark_position", "bottom"),
        )
        
        return {"success": True, "output": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@celery_app.task(bind=True, name="video.split")
def split_video_task(self, input_path: str, output_dir: str, mode: str = "manual",
                     start_time: str = "00:00:00", duration: float = 10.0,
                     min_duration: float = 5.0, limit: int = 5, base_name: str = "video"):
    try:
        self.update_state(state="PROCESSING", meta={"progress": 0})
        
        result = VideoService.split_video_raw(
            input_path=input_path,
            output_dir=output_dir,
            mode=mode,
            start_time=start_time,
            duration=duration,
            min_duration=min_duration,
            limit=limit,
            base_name=base_name,
        )
        
        return {"success": True, "output_files": result, "count": len(result) if result else 0}
    except Exception as e:
        return {"success": False, "error": str(e)}


@celery_app.task(bind=True, name="video.insert_intro")
def insert_intro_task(self, video_input_path: str, intro_url: str, output_path: str,
                      work_dir_path: str = "/tmp"):
    try:
        self.update_state(state="PROCESSING", meta={"progress": 0})
        
        result = VideoService.insert_intro(
            video_input_path=video_input_path,
            intro_url=intro_url,
            output_path=output_path,
            work_dir_path=work_dir_path,
        )
        
        return {"success": True, "output": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
