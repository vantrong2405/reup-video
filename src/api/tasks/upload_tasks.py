from api.tasks.celery_app import celery_app
from service.upload_service import UploadService


@celery_app.task(bind=True, name="upload.drive")
def upload_to_drive_task(self, local_path: str, drive_destination: str):
    try:
        self.update_state(state="PROCESSING", meta={"progress": 0})
        
        success = UploadService.upload_to_drive(
            local_path=local_path,
            drive_destination=drive_destination,
        )
        
        return {"success": True, "destination": drive_destination}
    except Exception as e:
        return {"success": False, "error": str(e)}
