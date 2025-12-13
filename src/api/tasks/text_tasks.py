from api.tasks.celery_app import celery_app
from service.text_service import TextService


@celery_app.task(bind=True, name="text.mask_filters")
def generate_mask_filters_task(self, video_path: str, languages: list = None,
                                expand: int = 10, max_frames: int = 3):
    try:
        self.update_state(state="PROCESSING", meta={"progress": 0})
        
        if languages is None:
            languages = ["en"]
        
        filter_string, boxes = TextService.generate_mask_filters(
            video_path=video_path,
            languages=languages,
            expand=expand,
            max_frames=max_frames,
        )
        
        boxes_data = [
            {"x": b["x"], "y": b["y"], "width": b["width"], "height": b["height"]}
            for b in boxes
        ]
        
        return {"success": True, "filter_string": filter_string, "boxes": boxes_data}
    except Exception as e:
        return {"success": False, "error": str(e)}
