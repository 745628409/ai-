from typing import Any
import re


EMOTION_WORDS = ["紧张", "恐惧", "温暖", "悲伤", "孤独", "愤怒", "浪漫", "神秘"]
TIME_WORDS = ["夜晚", "清晨", "黄昏", "午夜", "雨天", "冬天", "夏天"]
CAMERA_HINTS = {
    "回头": "中近景跟拍后切换到人物特写",
    "走": "低速跟拍，轻微手持感",
    "奔跑": "快速推轨 + 摇镜",
    "看": "镜头从环境切到主观视角",
    "闪烁": "环境光变化，加入曝光波动",
}


def analyze_story(text: str) -> dict[str, Any]:
    characters = re.findall(r"[一-龥]{1,4}(?:女人|男人|少年|少女|女孩|男孩|警察|老师|医生)", text)
    scene = "室内" if any(k in text for k in ["走廊", "房间", "屋", "门"]) else "室外"
    emotion = next((w for w in EMOTION_WORDS if w in text), "悬疑")
    time = next((w for w in TIME_WORDS if w in text), "未说明")

    actions = []
    for token in ["走", "跑", "回头", "抬头", "看", "哭", "笑", "闪烁", "推门"]:
        if token in text:
            actions.append(token)

    camera_suggestions = []
    for key, value in CAMERA_HINTS.items():
        if key in text:
            camera_suggestions.append(value)

    if not camera_suggestions:
        camera_suggestions = ["建立全景 -> 人物中景 -> 情绪特写"]

    segments = split_into_shots(text)

    return {
        "characters": sorted(list(set(characters))) or ["未命名主角"],
        "scene": scene,
        "emotion": emotion,
        "time": time,
        "actions": actions or ["静止/缓慢动作"],
        "visual_focus": "人物与环境关系、灯光层次、动作节奏",
        "camera_suggestions": camera_suggestions,
        "shots": segments,
    }


def split_into_shots(text: str) -> list[dict[str, str]]:
    parts = [p.strip() for p in re.split(r"[，。；;,.]", text) if p.strip()]
    shots = []
    for idx, part in enumerate(parts, start=1):
        shots.append(
            {
                "shot": f"镜头{idx}",
                "description": part,
                "camera": "慢推镜" if idx == 1 else "切换到中近景",
                "duration": "1.5-2.0s",
            }
        )
    return shots or [{"shot": "镜头1", "description": text, "camera": "中景", "duration": "3s"}]


def build_enhanced_prompt(text: str, style: str, analysis: dict[str, Any], extra: str = "") -> str:
    return (
        f"风格:{style}; 文本:{text}; 场景:{analysis['scene']}; 时间:{analysis['time']}; "
        f"情绪:{analysis['emotion']}; 动作:{'、'.join(analysis['actions'])}; "
        f"运镜建议:{'；'.join(analysis['camera_suggestions'])}; {extra}"
    )
