from fastapi import APIRouter
from api.schemas.base.base_response import BaseResponse
from api.schemas.base.job_created_data import JobCreatedData
from api.schemas.nsfw.nsfw_detect_request import NSFWDetectRequest
from api.schemas.nsfw.nsfw_filter_request import NSFWFilterRequest
from api.tasks.nsfw_tasks import detect_nsfw_task, filter_nsfw_task

class NSFWController:
    def __init__(self):
        self.router = APIRouter(prefix="/nsfw", tags=["NSFW"])
        self.router.add_api_route("/detect", self.detect_nsfw, methods=["POST"], response_model=BaseResponse[JobCreatedData])
        self.router.add_api_route("/filter", self.filter_nsfw, methods=["POST"], response_model=BaseResponse[JobCreatedData])

    async def detect_nsfw(self, request: NSFWDetectRequest):
        try:
            task = detect_nsfw_task.delay(
                video_path=request.video_path,
                threshold=request.threshold,
                frame_interval=request.frame_interval,
            )
            
            return BaseResponse.ok(JobCreatedData(job_id=task.id))
        except Exception as e:
            return BaseResponse.fail("NSFW_DETECT_ERROR", str(e))

    async def filter_nsfw(self, request: NSFWFilterRequest):
        try:
            task = filter_nsfw_task.delay(
                video_path=request.video_path,
                output_path=request.output_path,
                work_dir=request.work_dir,
            )
            
            return BaseResponse.ok(JobCreatedData(job_id=task.id))
        except Exception as e:
            return BaseResponse.fail("NSFW_FILTER_ERROR", str(e))

controller = NSFWController()
router = controller.router
