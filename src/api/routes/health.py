from fastapi import APIRouter
from api.schemas.base.base_response import BaseResponse
from api.schemas.base.health_data import HealthData
from api.config import settings
import redis

class HealthController:
    def __init__(self):
        self.router = APIRouter(tags=["Health"])
        self.router.add_api_route("/health", self.health_check, methods=["GET"], response_model=BaseResponse[HealthData])

    async def health_check(self):
        redis_status = "disconnected"
        try:
            r = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)
            r.ping()
            redis_status = "connected"
        except Exception:
            redis_status = "disconnected"
        
        return BaseResponse.ok(HealthData(
            status="healthy",
            version=settings.api_version,
            redis=redis_status
        ))

controller = HealthController()
router = controller.router
