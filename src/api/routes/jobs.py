from fastapi import APIRouter
from api.schemas.base.base_response import BaseResponse
from api.schemas.base.job_status_data import JobStatusData
from api.tasks.celery_app import celery_app
from celery.result import AsyncResult

class JobController:
    def __init__(self):
        self.router = APIRouter(prefix="/jobs", tags=["Jobs"])
        self.router.add_api_route("/", self.list_jobs, methods=["GET"], response_model=BaseResponse[dict])
        self.router.add_api_route("/{job_id}", self.get_job_status, methods=["GET"], response_model=BaseResponse[JobStatusData])
        self.router.add_api_route("/{job_id}", self.cancel_job, methods=["DELETE"], response_model=BaseResponse[dict])

    async def list_jobs(self):
        try:
            i = celery_app.control.inspect()
            
            # Fetch tasks from different states
            active = i.active() or {}
            scheduled = i.scheduled() or {}
            reserved = i.reserved() or {}
            
            jobs = []
            
            # Helper to process task lists
            def process_task_list(task_dict, status_label):
                for worker, tasks in task_dict.items():
                    for task in tasks:
                        jobs.append({
                            "job_id": task.get("id"),
                            "name": task.get("name"),
                            "status": status_label,
                            "args": task.get("args"),
                            "kwargs": task.get("kwargs"),
                            "worker": worker,
                            "time_start": task.get("time_start")
                        })

            process_task_list(active, "processing")
            process_task_list(scheduled, "scheduled")
            process_task_list(reserved, "pending")
            
            return BaseResponse.ok({
                "count": len(jobs),
                "jobs": jobs
            })
        except Exception as e:
            return BaseResponse.fail("LIST_JOBS_ERROR", str(e))

    async def get_job_status(self, job_id: str):
        task = AsyncResult(job_id, app=celery_app)
        
        status_map = {
            "PENDING": "pending",
            "STARTED": "processing",
            "PROCESSING": "processing",
            "SUCCESS": "completed",
            "FAILURE": "failed",
            "REVOKED": "cancelled",
        }
        
        status = status_map.get(task.status, task.status.lower())
        
        result = None
        error = None
        progress = None
        
        if task.ready():
            if task.successful():
                result = task.result
            else:
                error = str(task.result) if task.result else "Unknown error"
        elif task.status == "PROCESSING":
            meta = task.info or {}
            progress = meta.get("progress")
        
        return BaseResponse.ok(JobStatusData(
            job_id=job_id,
            status=status,
            progress=progress,
            result=result,
            error=error,
        ))

    async def cancel_job(self, job_id: str):
        task = AsyncResult(job_id, app=celery_app)
        
        if task.ready():
            return BaseResponse.fail("JOB_ALREADY_COMPLETED", "Job has already completed")
        
        task.revoke(terminate=True)
        
        return BaseResponse.ok({"job_id": job_id, "status": "cancelled"})

controller = JobController()
router = controller.router
