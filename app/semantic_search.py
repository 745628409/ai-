from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np
from PIL import Image

try:
    from app.models import SearchResult, ShotSegment
except ModuleNotFoundError:
    from models import SearchResult, ShotSegment


EFFECT_CANDIDATES = [
    "爆炸特效",
    "火焰与烟雾",
    "大场面动作戏",
    "慢动作镜头",
    "科幻CG场景",
    "强光闪烁",
    "雨夜光影",
    "打斗段落",
]

SCENE_CANDIDATES = [
    "室内走廊",
    "房间室内",
    "街道夜景",
    "办公室",
    "门口/门厅",
    "楼梯间",
    "车内",
]

EVENT_CANDIDATES = {
    "walk_into_door": ["一个人走进一扇门", "人物进入门内", "走向门口并进入"],
    "open_eyes": ["人物睁开眼睛", "眼睛从闭到开", "面部特写睁眼"],
    "walking": ["人物行走", "走路镜头", "持续步行"],
}


class SemanticSearcher:
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32") -> None:
        self.model_name = model_name
        self.processor = None
        self.model = None

        self.shot_embeddings: np.ndarray | None = None
        self.shot_face_embeddings: np.ndarray | None = None
        self.shots: List[ShotSegment] = []

        self.effect_label_embeddings: np.ndarray | None = None
        self.scene_label_embeddings: np.ndarray | None = None
        self.event_label_embeddings: dict[str, np.ndarray] = {}

        self.actor_db: Dict[str, np.ndarray] = {}
        self.eye_open_scores: np.ndarray | None = None
        self.event_scores: dict[str, np.ndarray] = {}

        self.face_detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.eye_detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")

    def _ensure_model_loaded(self) -> None:
        if self.processor is None or self.model is None:
            from transformers import CLIPModel, CLIPProcessor

            self.processor = CLIPProcessor.from_pretrained(self.model_name)
            self.model = CLIPModel.from_pretrained(self.model_name)
        if self.effect_label_embeddings is None or self.scene_label_embeddings is None or not self.event_label_embeddings:
            self.effect_label_embeddings = self._encode_text(EFFECT_CANDIDATES)
            self.scene_label_embeddings = self._encode_text(SCENE_CANDIDATES)
            self.event_label_embeddings = {
                key: self._encode_text(prompts) for key, prompts in EVENT_CANDIDATES.items()
            }

    def load_actor_library(self, actor_root: str = "data/actors") -> int:
        self._ensure_model_loaded()
        root = Path(actor_root)
        self.actor_db.clear()
        if not root.exists():
            return 0

        for person_dir in root.iterdir():
            if not person_dir.is_dir():
                continue
            imgs = [p for p in person_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
            if not imgs:
                continue
            vectors = []
            for img in imgs:
                try:
                    face = self._crop_face(str(img))
                    image = face if face is not None else Image.open(img).convert("RGB")
                    vectors.append(self._encode_images([image])[0])
                except Exception:
                    continue
            if vectors:
                self.actor_db[person_dir.name] = self._normalize(np.mean(vectors, axis=0, keepdims=True))[0]
        return len(self.actor_db)

    def index_shots(self, shots: List[ShotSegment]) -> None:
        self._ensure_model_loaded()
        self.shots = shots
        shot_vectors: list[np.ndarray] = []
        face_vectors: list[np.ndarray] = []
        eye_scores: list[float] = []
        event_collect = {k: [] for k in EVENT_CANDIDATES.keys()}

        for shot in shots:
            images = [Image.open(p).convert("RGB") for p in shot.keyframe_paths] or [Image.open(shot.thumbnail_path).convert("RGB")]
            img_vecs = self._encode_images(images)
            shot_mean = np.mean(img_vecs, axis=0, keepdims=True)
            shot_vectors.append(shot_mean[0])

            shot.effect_tags = self._infer_tags(shot_mean, self.effect_label_embeddings, EFFECT_CANDIDATES, threshold=0.22)
            shot.scene_tags = self._infer_tags(shot_mean, self.scene_label_embeddings, SCENE_CANDIDATES, threshold=0.22)

            # 人脸向量 + 睁眼启发式
            face_imgs = []
            open_eye_votes = []
            for p in shot.keyframe_paths:
                face = self._crop_face(p)
                if face is not None:
                    face_imgs.append(face)
                    open_eye_votes.append(self._estimate_eye_open_score(face))

            if face_imgs:
                face_vec = np.mean(self._encode_images(face_imgs), axis=0)
                eye_scores.append(float(np.mean(open_eye_votes)))
            else:
                face_vec = np.zeros(img_vecs.shape[1], dtype=np.float32)
                eye_scores.append(0.0)
            face_vectors.append(face_vec)

            for evt_name, evt_emb in self.event_label_embeddings.items():
                score = float(np.max((img_vecs @ evt_emb.T)))
                event_collect[evt_name].append(score)

        self.shot_embeddings = self._normalize(np.vstack(shot_vectors))
        self.shot_face_embeddings = self._normalize(np.vstack(face_vectors) + 1e-8)
        self.eye_open_scores = np.array(eye_scores, dtype=np.float32)
        self.event_scores = {k: np.array(v, dtype=np.float32) for k, v in event_collect.items()}

    def search(self, query: str, top_k: int = 20) -> List[SearchResult]:
        self._ensure_model_loaded()
        if self.shot_embeddings is None or not self.shots:
            return []

        actor_name, clean_query = self._parse_actor_query(query)
        scene_name, clean_query = self._parse_scene_query(clean_query)
        text_vec = self._encode_text([clean_query or query])[0]

        global_scores = self.shot_embeddings @ text_vec
        final_scores = 0.68 * global_scores
        reasons = [["语义匹配"] for _ in self.shots]

        query_keywords = set((clean_query or query).replace("，", " ").replace(",", " ").split())
        effect_boost = np.zeros(len(self.shots), dtype=np.float32)
        scene_boost = np.zeros(len(self.shots), dtype=np.float32)

        for i, shot in enumerate(self.shots):
            if query_keywords.intersection(set(shot.effect_tags)):
                effect_boost[i] = 0.16
                reasons[i].append("特效标签命中")
            if scene_name and scene_name in shot.scene_tags:
                scene_boost[i] = 0.20
                reasons[i].append(f"场景命中:{scene_name}")

        final_scores = final_scores + effect_boost + scene_boost

        # 事件加权
        evt_boost = self._event_boost(query)
        if evt_boost is not None:
            final_scores = final_scores + evt_boost
            for i in range(len(self.shots)):
                if evt_boost[i] > 0.05:
                    reasons[i].append("事件命中")

        if actor_name and actor_name in self.actor_db and self.shot_face_embeddings is not None:
            actor_vec = self.actor_db[actor_name]
            actor_scores = self.shot_face_embeddings @ actor_vec
            final_scores = final_scores + 0.35 * actor_scores
            for i in range(len(self.shots)):
                reasons[i].append(f"演员匹配:{actor_name}")

        order = np.argsort(-final_scores)[:top_k]
        return [
            SearchResult(shot=self.shots[i], score=float(final_scores[i]), reasons=reasons[i])
            for i in order
        ]

    def _event_boost(self, query: str) -> np.ndarray | None:
        q = query.lower()
        size = len(self.shots)
        boost = np.zeros(size, dtype=np.float32)
        used = False

        if any(k in q for k in ["走进门", "进门", "进入门"]):
            if "walk_into_door" in self.event_scores:
                boost += 0.24 * self.event_scores["walk_into_door"]
                used = True
        if any(k in q for k in ["睁眼", "睁开眼", "open eyes"]):
            if "open_eyes" in self.event_scores:
                boost += 0.18 * self.event_scores["open_eyes"]
                used = True
            if self.eye_open_scores is not None:
                boost += 0.18 * self.eye_open_scores
                used = True
        if any(k in q for k in ["行走", "走路", "walking"]):
            if "walking" in self.event_scores:
                boost += 0.20 * self.event_scores["walking"]
                used = True

        return boost if used else None

    def _infer_tags(
        self,
        shot_vector: np.ndarray,
        label_embeddings: np.ndarray,
        labels: list[str],
        threshold: float,
    ) -> list[str]:
        sims = (label_embeddings @ shot_vector.T).reshape(-1)
        order = np.argsort(-sims)[:3]
        return [labels[i] for i in order if sims[i] > threshold]

    def _estimate_eye_open_score(self, face_image: Image.Image) -> float:
        rgb = np.array(face_image)
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        eyes = self.eye_detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(8, 8))
        # 检测到双眼时认为更可能是睁眼镜头
        return 1.0 if len(eyes) >= 2 else 0.0

    def _crop_face(self, image_path: str) -> Image.Image | None:
        bgr = cv2.imread(image_path)
        if bgr is None:
            return None
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40))
        if len(faces) == 0:
            return None
        x, y, w, h = max(faces, key=lambda item: item[2] * item[3])
        crop = bgr[y : y + h, x : x + w]
        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)

    def _parse_actor_query(self, query: str) -> tuple[str | None, str]:
        marker = "actor:"
        if marker not in query:
            return None, query
        after = query.split(marker, 1)[1].strip()
        if not after:
            return None, query
        parts = after.split(maxsplit=1)
        name = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
        return name, rest

    def _parse_scene_query(self, query: str) -> tuple[str | None, str]:
        marker = "scene:"
        if marker not in query:
            return None, query
        after = query.split(marker, 1)[1].strip()
        if not after:
            return None, query
        parts = after.split(maxsplit=1)
        scene = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
        return scene, rest

    def _encode_images(self, images: list[Image.Image]) -> np.ndarray:
        self._ensure_model_loaded()
        inputs = self.processor(images=images, return_tensors="pt", padding=True)
        image_features = self.model.get_image_features(**inputs).detach().cpu().numpy()
        return self._normalize(image_features)

    def _encode_text(self, texts: list[str]) -> np.ndarray:
        self._ensure_model_loaded()
        text_inputs = self.processor(text=texts, return_tensors="pt", padding=True)
        text_features = self.model.get_text_features(**text_inputs).detach().cpu().numpy()
        return self._normalize(text_features)

    @staticmethod
    def _normalize(vec: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(vec, axis=1, keepdims=True) + 1e-12
        return vec / norm
