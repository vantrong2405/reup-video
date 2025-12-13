from fastapi import APIRouter
from api.schemas.base.base_response import BaseResponse
from api.schemas.base.job_created_data import JobCreatedData
from api.schemas.upload.upload_drive_request import UploadDriveRequest
from api.schemas.upload.drive_link_data import DriveLinkData
from api.tasks.upload_tasks import upload_to_drive_task
from service.upload_service import UploadService

class UploadController:
    def __init__(self):
        self.router = APIRouter(prefix="/uploads", tags=["Upload"])
        self.router.add_api_route("/drive", self.upload_to_drive, methods=["POST"], response_model=BaseResponse[JobCreatedData])
        self.router.add_api_route("/drive-link", self.get_drive_link, methods=["GET"], response_model=BaseResponse[DriveLinkData])

    async def upload_to_drive(self, request: UploadDriveRequest):
        try:
            task = upload_to_drive_task.delay(
                local_path=request.local_path,
                drive_destination=request.drive_destination,
            )
            
            return BaseResponse.ok(JobCreatedData(job_id=task.id))
        except Exception as e:
            return BaseResponse.fail("UPLOAD_DRIVE_ERROR", str(e))

    async def get_drive_link(self, drive_path: str):
        try:
            link = UploadService.get_drive_link(drive_path)
            
            return BaseResponse.ok(DriveLinkData(link=link))
        except Exception as e:
            return BaseResponse.fail("DRIVE_LINK_ERROR", str(e))

controller = UploadController()
router = controller.router
