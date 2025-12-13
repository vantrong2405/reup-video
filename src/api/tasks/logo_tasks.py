from api.tasks.celery_app import celery_app
from service.logo_service import LogoService


@celery_app.task(bind=True, name="logo.overlay")
def overlay_logo_task(self, origin_path: str, logo_path: str, x: int, y: int,
                      width: int, height: int, output_path: str,
                      scale_w: float = 1.0, scale_h: float = 1.0,
                      margin: int = 0, offset_y: int = 0):
    try:
        self.update_state(state="PROCESSING", meta={"progress": 0})
        
        LogoService.SCALE_W = scale_w
        LogoService.SCALE_H = scale_h
        LogoService.MARGIN = margin
        LogoService.OFFSET_Y = offset_y
        
        service = LogoService()
        result = service.overlay_logo(origin_path, logo_path, x, y, width, height, output_path)
        
        return {"success": True, "output": result.get("output", output_path)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@celery_app.task(bind=True, name="logo.process")
def process_logo_task(self, origin_path: str, logo_path: str, model_path: str,
                      conf_threshold: float, output_path: str,
                      scale_w: float = 1.0, scale_h: float = 1.0,
                      margin: int = 0, offset_y: int = 0):
    try:
        self.update_state(state="PROCESSING", meta={"progress": 0})
        
        LogoService.SCALE_W = scale_w
        LogoService.SCALE_H = scale_h
        LogoService.MARGIN = margin
        LogoService.OFFSET_Y = offset_y
        
        service = LogoService()
        result = service.process_logo(origin_path, logo_path, model_path, conf_threshold, output_path)
        
        return {"success": True, "output": result.get("output", output_path), "detected_logos": result.get("detected", 0)}
    except Exception as e:
        return {"success": False, "error": str(e)}
