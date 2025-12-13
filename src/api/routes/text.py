from fastapi import APIRouter
from api.schemas.base.base_response import BaseResponse
from api.schemas.base.job_created_data import JobCreatedData
from api.schemas.text.text_detect_request import TextDetectRequest
from api.schemas.text.text_detect_data import TextDetectData
from api.schemas.text.text_box import TextBox
from api.schemas.text.text_mask_filters_request import TextMaskFiltersRequest
from api.tasks.text_tasks import generate_mask_filters_task
from service.text_service import TextService

class TextController:
    def __init__(self):
        self.router = APIRouter(prefix="/text", tags=["Text/OCR"])
        self.router.add_api_route("/detect", self.detect_text, methods=["POST"], response_model=BaseResponse[TextDetectData])
        self.router.add_api_route("/mask-filters", self.generate_mask_filters, methods=["POST"], response_model=BaseResponse[JobCreatedData])

    async def detect_text(self, request: TextDetectRequest):
        try:
            service = TextService(languages=request.languages)
            boxes = service.detect_text(request.image_path)
            
            text_boxes = [
                TextBox(
                    x=b.get("x", 0),
                    y=b.get("y", 0),
                    width=b.get("width", 0),
                    height=b.get("height", 0),
                    text=b.get("text", ""),
                    prob=b.get("prob", 0.0),
                )
                for b in boxes
            ]
            
            return BaseResponse.ok(TextDetectData(
                boxes=text_boxes,
                count=len(text_boxes)
            ))
        except Exception as e:
            return BaseResponse.fail("TEXT_DETECT_ERROR", str(e))

    async def generate_mask_filters(self, request: TextMaskFiltersRequest):
        try:
            task = generate_mask_filters_task.delay(
                video_path=request.video_path,
                languages=request.languages,
                expand=request.expand,
                max_frames=request.max_frames,
            )
            
            return BaseResponse.ok(JobCreatedData(job_id=task.id))
        except Exception as e:
            return BaseResponse.fail("TEXT_MASK_FILTERS_ERROR", str(e))

controller = TextController()
router = controller.router
