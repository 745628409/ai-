from __future__ import annotations

from pathlib import Path
from typing import List

import cv2
from scenedetect import SceneManager, open_video
from scenedetect.detectors import ContentDetector

from models import ShotSegment


class ShotIndexer:
    def __init__(self, threshold: float = 27.0, keyframes_per_shot: int = 3) -> None:
        self.threshold = threshold
        self.keyframes_per_shot = max(1, keyframes_per_shot)

    def build_index(self, video_path: str, thumb_dir: str) -> List[ShotSegment]:
        video = open_video(video_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=self.threshold))
        scene_manager.detect_scenes(video)
        scene_list = scene_manager.get_scene_list()

        if not scene_list:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
            frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 1
            duration = frames / fps
            cap.release()
            scene_list = [
                (
                    self._seconds_to_timecode(0, fps),
                    self._seconds_to_timecode(duration, fps),
                )
            ]

        thumb_root = Path(thumb_dir)
        thumb_root.mkdir(parents=True, exist_ok=True)

        shots: List[ShotSegment] = []
        cap = cv2.VideoCapture(video_path)

        for idx, (start_tc, end_tc) in enumerate(scene_list):
            start_sec = start_tc.get_seconds()
            end_sec = end_tc.get_seconds()
            frame_times = self._build_sample_times(start_sec, end_sec, self.keyframes_per_shot)

            keyframe_paths: list[str] = []
            for k, t_sec in enumerate(frame_times):
                frame = self._read_frame(cap, t_sec)
                if frame is None:
                    continue
                img_path = thumb_root / f"shot_{idx:04d}_kf{k:02d}.jpg"
                cv2.imwrite(str(img_path), frame)
                keyframe_paths.append(str(img_path))

            if not keyframe_paths:
                continue

            shots.append(
                ShotSegment(
                    index=idx,
                    start_sec=start_sec,
                    end_sec=end_sec,
                    thumbnail_path=keyframe_paths[len(keyframe_paths) // 2],
                    keyframe_paths=keyframe_paths,
                )
            )

        cap.release()
        return shots

    @staticmethod
    def _build_sample_times(start_sec: float, end_sec: float, n: int) -> list[float]:
        if end_sec <= start_sec:
            return [start_sec]
        duration = end_sec - start_sec
        return [start_sec + duration * ((i + 1) / (n + 1)) for i in range(n)]

    @staticmethod
    def _read_frame(cap: cv2.VideoCapture, sec: float):
        cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
        ok, frame = cap.read()
        return frame if ok else None

    @staticmethod
    def _seconds_to_timecode(seconds: float, fps: float):
        from scenedetect.frame_timecode import FrameTimecode

        frames = int(seconds * fps)
        return FrameTimecode(timecode=frames, fps=fps)
