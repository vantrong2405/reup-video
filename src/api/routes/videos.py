from fastapi import APIRouter
from api.schemas.base.base_response import BaseResponse
from api.schemas.base.job_created_data import JobCreatedData
from api.schemas.video.video_pipeline_request import VideoPipelineRequest
from api.schemas.video.video_split_request import VideoSplitRequest
from api.schemas.video.video_info_request import VideoInfoRequest
from api.schemas.video.video_info_data import VideoInfoData
from api.tasks.video_tasks import process_pipeline_task, split_video_task
from utils.video_utils import VideoUtils

class VideoController:
    def __init__(self):
        self.router = APIRouter(prefix="/videos", tags=["Videos"])
        self.router.add_api_route("/pipeline", self.process_video_pipeline, methods=["POST"], response_model=BaseResponse[JobCreatedData])
        self.router.add_api_route("/split", self.split_video, methods=["POST"], response_model=BaseResponse[JobCreatedData])
        self.router.add_api_route("/info", self.get_video_info, methods=["GET"], response_model=BaseResponse[VideoInfoData])

    async def process_video_pipeline(self, request: VideoPipelineRequest):
        try:
            task = process_pipeline_task.delay(
                video_input=request.video_input,
                logo_input=request.logo_input,
                detect_json=request.detect_json,
                output_path=request.output_path,
                new_logo_url=request.new_logo_url,
                intro_url=request.intro_url,
                work_dir=request.work_dir,
                flip=request.flip,
                zoom=request.zoom,
                speed=request.speed,
                brightness=request.brightness,
                saturation=request.saturation,
                hue=request.hue,
                background_music=request.background_music,
                bg_music_volume=request.bg_music_volume,
                remove_text=request.remove_text,
                ocr_languages=request.ocr_languages,
                gemini_key=request.gemini_key,
                filter_nsfw=request.filter_nsfw,
                ffmpeg_preset=request.ffmpeg_preset,
                split_mode=request.split_mode,
                split_start=request.split_start,
                split_duration=request.split_duration,
                split_limit=request.split_limit,
                unique_mode=request.unique_mode,
                watermark_text=request.watermark_text,
                watermark_opacity=request.watermark_opacity,
                watermark_size=request.watermark_size,
                watermark_speed=request.watermark_speed,
                watermark_position=request.watermark_position,
            )
            
            return BaseResponse.ok(JobCreatedData(job_id=task.id))
        except Exception as e:
            return BaseResponse.fail("VIDEO_PIPELINE_ERROR", str(e))

    async def split_video(self, request: VideoSplitRequest):
        try:
            task = split_video_task.delay(
                input_path=request.input_path,
                output_dir=request.output_dir,
                mode=request.mode,
                start_time=request.start_time,
                duration=request.duration,
                min_duration=request.min_duration,
                limit=request.limit,
                base_name=request.base_name,
            )
            
            return BaseResponse.ok(JobCreatedData(job_id=task.id))
        except Exception as e:
            return BaseResponse.fail("VIDEO_SPLIT_ERROR", str(e))

    async def get_video_info(self, video_path: str):
        try:
            info = VideoUtils.get_video_info(video_path)
            
            return BaseResponse.ok(VideoInfoData(
                width=info.get("width", 0),
                height=info.get("height", 0),
                fps=info.get("fps", "30"),
                duration=info.get("duration", 0.0),
                has_audio=info.get("has_audio", False),
            ))
        except Exception as e:
            return BaseResponse.fail("VIDEO_INFO_ERROR", str(e))

controller = VideoController()
router = controller.router
