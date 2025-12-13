from api.tasks.celery_app import celery_app
from service.nsfw_service import NSFWService


@celery_app.task(bind=True, name="nsfw.detect")
def detect_nsfw_task(self, video_path: str, threshold: float = 0.7, frame_interval: float = 1.0):
    try:
        self.update_state(state="PROCESSING", meta={"progress": 0})
        
        segments = NSFWService.detect_unsafe_segments(
            video_path=video_path,
            threshold=threshold,
            frame_interval=frame_interval,
        )
        
        segments_data = [{"start": s[0], "end": s[1]} for s in segments]
        
        return {"success": True, "segments": segments_data, "count": len(segments)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@celery_app.task(bind=True, name="nsfw.filter")
def filter_nsfw_task(self, video_path: str, output_path: str, work_dir: str = "/tmp"):
    try:
        self.update_state(state="PROCESSING", meta={"progress": 0})
        
        result = NSFWService.filter_video(
            video_path=video_path,
            output_path=output_path,
            work_dir=work_dir,
        )
        
        return {"success": True, "output": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
