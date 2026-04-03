from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any, Literal


StyleType = Literal["写实", "电影感", "插画", "奇幻", "国风", "悬疑", "赛博朋克"]
AspectRatio = Literal["16:9", "9:16", "1:1", "21:9"]


class CharacterCard(BaseModel):
    id: str
    name: str
    gender: str = "未指定"
    appearance: str
    clothing: str
    temperament: str
    identity_tags: list[str] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    text: str


class TextToImageRequest(BaseModel):
    text: str
    style: StyleType = "电影感"
    aspect_ratio: AspectRatio = "16:9"
    candidate_count: int = Field(default=3, ge=1, le=4)
    character_ids: list[str] = Field(default_factory=list)


class TextToVideoRequest(BaseModel):
    text: str
    style: StyleType = "电影感"
    aspect_ratio: AspectRatio = "16:9"
    duration_seconds: int = Field(default=5, ge=3, le=12)
    character_ids: list[str] = Field(default_factory=list)


class ImageToVideoRequest(BaseModel):
    image_url: str
    action_text: str
    style: StyleType = "电影感"
    duration_seconds: int = Field(default=5, ge=3, le=12)


class KeyframeToVideoRequest(BaseModel):
    start_image_url: str
    middle_image_url: str
    end_image_url: str
    story_text: str
    style: StyleType = "电影感"
    duration_seconds: int = Field(default=8, ge=4, le=15)


class GenerationRecord(BaseModel):
    id: str
    kind: Literal["image", "video"]
    input_text: str
    style: str
    aspect_ratio: str | None = None
    output_urls: list[str]
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApiResponse(BaseModel):
    success: bool
    message: str = "ok"
    data: dict[str, Any] = Field(default_factory=dict)
