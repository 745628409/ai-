from dataclasses import dataclass, field


@dataclass
class ShotSegment:
    index: int
    start_sec: float
    end_sec: float
    thumbnail_path: str
    keyframe_paths: list[str] = field(default_factory=list)
    effect_tags: list[str] = field(default_factory=list)
    scene_tags: list[str] = field(default_factory=list)


@dataclass
class SearchResult:
    shot: ShotSegment
    score: float
    reasons: list[str] = field(default_factory=list)
