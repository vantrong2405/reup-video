from fastapi import APIRouter
from api.schemas.base.base_response import BaseResponse
from api.schemas.base.job_created_data import JobCreatedData
from api.schemas.logo.logo_detect_request import LogoDetectRequest
from api.schemas.logo.logo_detect_data import LogoDetectData
from api.schemas.logo.logo_process_request import LogoProcessRequest
from api.tasks.logo_tasks import overlay_logo_task, process_logo_task
from service.logo_service import LogoService

class LogoController:
    def __init__(self):
        self.router = APIRouter(prefix="/logos", tags=["Logos"])
        self.router.add_api_route("/detect", self.detect_logo, methods=["POST"], response_model=BaseResponse[LogoDetectData])
        self.router.add_api_route("/process", self.process_logo, methods=["POST"], response_model=BaseResponse[JobCreatedData])

    async def detect_logo(self, request: LogoDetectRequest):
        try:
            service = LogoService()
            result = service.detect_logo(
                image_path=request.image_path,
                model_path=request.model_path,
                conf_threshold=request.conf_threshold,
            )
            
            logos = []
            for logo in result.get("logos", []):
                logos.append({
                    "x": logo.get("x", 0),
                    "y": logo.get("y", 0),
                    "width": logo.get("width", 0),
                    "height": logo.get("height", 0),
                    "confidence": logo.get("confidence", 0.0),
                })
            
            return BaseResponse.ok(LogoDetectData(
                logos=logos,
                count=result.get("count", len(logos))
            ))
        except Exception as e:
            return BaseResponse.fail("LOGO_DETECT_ERROR", str(e))

    async def process_logo(self, request: LogoProcessRequest):
        try:
            task = process_logo_task.delay(
                origin_path=request.origin_path,
                logo_path=request.logo_path,
                model_path=request.model_path,
                conf_threshold=request.conf_threshold,
                output_path=request.output_path,
                scale_w=request.scale_w,
                scale_h=request.scale_h,
                margin=request.margin,
                offset_y=request.offset_y,
            )
            
            return BaseResponse.ok(JobCreatedData(job_id=task.id))
        except Exception as e:
            return BaseResponse.fail("LOGO_PROCESS_ERROR", str(e))

controller = LogoController()
router = controller.router
