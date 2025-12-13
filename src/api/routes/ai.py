from fastapi import APIRouter
from api.schemas.base.base_response import BaseResponse
from api.schemas.ai.ai_rewrite_request import AIRewriteRequest
from api.schemas.ai.ai_rewrite_data import AIRewriteData
from service.ai_service import AIService

class AIController:
    def __init__(self):
        self.router = APIRouter(prefix="/ai", tags=["AI"])
        self.router.add_api_route("/rewrite", self.rewrite_text, methods=["POST"], response_model=BaseResponse[AIRewriteData])

    async def rewrite_text(self, request: AIRewriteRequest):
        try:
            result = AIService.rewrite_text(
                text_content=request.text,
                api_key=request.api_key,
                target_language=request.target_language,
            )

            return BaseResponse.ok(AIRewriteData(
                original=request.text,
                rewritten=result
            ))
        except Exception as e:
            return BaseResponse.fail("AI_REWRITE_ERROR", str(e))

controller = AIController()
router = controller.router
