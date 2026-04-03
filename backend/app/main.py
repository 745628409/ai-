from pathlib import Path
from datetime import datetime
from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import (
    AnalysisRequest,
    ApiResponse,
    CharacterCard,
    GenerationRecord,
    ImageToVideoRequest,
    KeyframeToVideoRequest,
    TextToImageRequest,
    TextToVideoRequest,
)
from app.services.model_service import ModelService
from app.services.story_parser import analyze_story, build_enhanced_prompt
from app.services.storage_service import add_history, list_characters, list_history, save_character

app = FastAPI(title="Novel2Screen API", version="0.1.0")
model_service = ModelService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root_page() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static_index.html")


@app.get("/health", response_model=ApiResponse)
async def health() -> ApiResponse:
    return ApiResponse(success=True, data={"status": "running"})


@app.post("/api/analyze", response_model=ApiResponse)
async def analyze(req: AnalysisRequest) -> ApiResponse:
    data = analyze_story(req.text)
    return ApiResponse(success=True, data=data)


@app.get("/api/characters", response_model=ApiResponse)
async def get_characters() -> ApiResponse:
    return ApiResponse(success=True, data={"items": list_characters()})


@app.post("/api/characters", response_model=ApiResponse)
async def upsert_character(card: CharacterCard) -> ApiResponse:
    save_character(card.model_dump())
    return ApiResponse(success=True, message="角色已保存", data={"item": card.model_dump()})


@app.get("/api/history", response_model=ApiResponse)
async def get_history() -> ApiResponse:
    return ApiResponse(success=True, data={"items": list_history()})


@app.post("/api/generate/image", response_model=ApiResponse)
async def generate_image(req: TextToImageRequest) -> ApiResponse:
    analysis = analyze_story(req.text)
    prompt = build_enhanced_prompt(req.text, req.style, analysis)
    urls = await model_service.generate_images(prompt=prompt, aspect_ratio=req.aspect_ratio, count=req.candidate_count)

    record = GenerationRecord(
        id=str(uuid4()),
        kind="image",
        input_text=req.text,
        style=req.style,
        aspect_ratio=req.aspect_ratio,
        output_urls=urls,
        created_at=datetime.utcnow(),
        metadata={"analysis": analysis, "prompt": prompt, "character_ids": req.character_ids},
    )
    add_history(record.model_dump(mode="json"))

    return ApiResponse(success=True, data={"urls": urls, "analysis": analysis, "prompt": prompt})


@app.post("/api/generate/video/text", response_model=ApiResponse)
async def generate_text_video(req: TextToVideoRequest) -> ApiResponse:
    analysis = analyze_story(req.text)
    prompt = build_enhanced_prompt(req.text, req.style, analysis, extra="输出电影级连贯镜头")
    video_url = await model_service.text_to_video(prompt, req.duration_seconds)

    record = GenerationRecord(
        id=str(uuid4()),
        kind="video",
        input_text=req.text,
        style=req.style,
        aspect_ratio=req.aspect_ratio,
        output_urls=[video_url],
        created_at=datetime.utcnow(),
        metadata={"analysis": analysis, "prompt": prompt, "duration_seconds": req.duration_seconds},
    )
    add_history(record.model_dump(mode="json"))

    return ApiResponse(success=True, data={"video_url": video_url, "analysis": analysis, "shots": analysis["shots"], "prompt": prompt})


@app.post("/api/generate/video/image", response_model=ApiResponse)
async def generate_image_video(req: ImageToVideoRequest) -> ApiResponse:
    combined_text = f"基于输入图像，动作描述：{req.action_text}"
    analysis = analyze_story(combined_text)
    prompt = build_enhanced_prompt(combined_text, req.style, analysis, extra="强调角色动作和镜头推进")
    video_url = await model_service.image_to_video(req.image_url, prompt, req.duration_seconds)

    record = GenerationRecord(
        id=str(uuid4()),
        kind="video",
        input_text=combined_text,
        style=req.style,
        output_urls=[video_url],
        created_at=datetime.utcnow(),
        metadata={"prompt": prompt, "source_image": req.image_url},
    )
    add_history(record.model_dump(mode="json"))

    return ApiResponse(success=True, data={"video_url": video_url, "prompt": prompt})


@app.post("/api/generate/video/keyframes", response_model=ApiResponse)
async def generate_keyframe_video(req: KeyframeToVideoRequest) -> ApiResponse:
    analysis = analyze_story(req.story_text)
    prompt = build_enhanced_prompt(req.story_text, req.style, analysis, extra="请平滑衔接首中尾关键帧")
    video_url = await model_service.keyframe_video(
        req.start_image_url,
        req.middle_image_url,
        req.end_image_url,
        prompt,
        req.duration_seconds,
    )

    record = GenerationRecord(
        id=str(uuid4()),
        kind="video",
        input_text=req.story_text,
        style=req.style,
        output_urls=[video_url],
        created_at=datetime.utcnow(),
        metadata={
            "prompt": prompt,
            "start": req.start_image_url,
            "middle": req.middle_image_url,
            "end": req.end_image_url,
        },
    )
    add_history(record.model_dump(mode="json"))

    return ApiResponse(success=True, data={"video_url": video_url, "shots": analysis["shots"], "prompt": prompt})
