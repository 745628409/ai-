from __future__ import annotations

from typing import Any
import httpx

from app.config import settings


ASPECT_TO_SIZE = {
    "16:9": "1536x1024",
    "9:16": "1024x1536",
    "1:1": "1024x1024",
    "21:9": "1792x768",
}


class ModelService:
    async def generate_images(self, prompt: str, aspect_ratio: str, count: int) -> list[str]:
        if settings.mock_mode or not settings.openai_api_key:
            return [f"https://picsum.photos/seed/novel-{i}/{self._mock_width(aspect_ratio)}/{self._mock_height(aspect_ratio)}" for i in range(1, count + 1)]

        url = f"{settings.openai_base_url}/images/generations"
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        payload = {
            "model": "gpt-image-1",
            "prompt": prompt,
            "size": ASPECT_TO_SIZE.get(aspect_ratio, "1536x1024"),
            "n": count,
            "quality": "high",
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        urls: list[str] = []
        for item in data.get("data", []):
            if item.get("url"):
                urls.append(item["url"])
            elif item.get("b64_json"):
                urls.append(f"data:image/png;base64,{item['b64_json']}")
        return urls

    async def text_to_video(self, prompt: str, duration: int) -> str:
        if settings.mock_mode or not settings.replicate_api_token:
            return "https://cdn.coverr.co/videos/coverr-woman-walking-down-a-dark-corridor-1579/1080p.mp4"

        prediction = await self._replicate_prediction(
            version="kwaivgi/kling-v1.6-pro",
            input_payload={"prompt": prompt, "duration": duration},
        )
        return prediction

    async def image_to_video(self, image_url: str, prompt: str, duration: int) -> str:
        if settings.mock_mode or not settings.replicate_api_token:
            return "https://cdn.coverr.co/videos/coverr-camera-moving-through-a-hallway-6604/1080p.mp4"

        prediction = await self._replicate_prediction(
            version="luma/ray-2",
            input_payload={"prompt": prompt, "image": image_url, "duration": duration},
        )
        return prediction

    async def keyframe_video(self, start: str, middle: str, end: str, prompt: str, duration: int) -> str:
        if settings.mock_mode or not settings.replicate_api_token:
            return "https://cdn.coverr.co/videos/coverr-night-hallway-cinematic-shot-4472/1080p.mp4"

        prediction = await self._replicate_prediction(
            version="minimax/video-01-live",
            input_payload={
                "prompt": prompt,
                "first_frame_image": start,
                "middle_frame_image": middle,
                "last_frame_image": end,
                "duration": duration,
            },
        )
        return prediction

    async def _replicate_prediction(self, version: str, input_payload: dict[str, Any]) -> str:
        headers = {
            "Authorization": f"Bearer {settings.replicate_api_token}",
            "Content-Type": "application/json",
        }
        payload = {"version": version, "input": input_payload}
        async with httpx.AsyncClient(timeout=180) as client:
            create = await client.post(f"{settings.replicate_base_url}/predictions", headers=headers, json=payload)
            create.raise_for_status()
            pred = create.json()
            get_url = pred["urls"]["get"]
            status = pred["status"]

            for _ in range(45):
                if status in {"succeeded", "failed", "canceled"}:
                    break
                polled = await client.get(get_url, headers=headers)
                polled.raise_for_status()
                pred = polled.json()
                status = pred["status"]

            if status != "succeeded":
                raise RuntimeError(f"视频生成失败，状态: {status}")

            output = pred.get("output")
            if isinstance(output, list):
                return output[-1]
            if isinstance(output, str):
                return output
            raise RuntimeError("模型未返回可用视频地址")

    @staticmethod
    def _mock_width(aspect_ratio: str) -> int:
        return {"16:9": 1366, "9:16": 720, "1:1": 1024, "21:9": 1680}.get(aspect_ratio, 1366)

    @staticmethod
    def _mock_height(aspect_ratio: str) -> int:
        return {"16:9": 768, "9:16": 1280, "1:1": 1024, "21:9": 720}.get(aspect_ratio, 768)
