import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "storage"
CHAR_FILE = DATA_DIR / "characters.json"
HISTORY_FILE = DATA_DIR / "history.json"


def _ensure_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CHAR_FILE.exists():
        CHAR_FILE.write_text("[]", encoding="utf-8")
    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text("[]", encoding="utf-8")


def _read_json(path: Path) -> list[dict[str, Any]]:
    _ensure_files()
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: list[dict[str, Any]]) -> None:
    _ensure_files()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def list_characters() -> list[dict[str, Any]]:
    return _read_json(CHAR_FILE)


def save_character(character: dict[str, Any]) -> None:
    chars = _read_json(CHAR_FILE)
    filtered = [c for c in chars if c.get("id") != character.get("id")]
    filtered.append(character)
    _write_json(CHAR_FILE, filtered)


def list_history() -> list[dict[str, Any]]:
    items = _read_json(HISTORY_FILE)
    return list(reversed(items))


def add_history(record: dict[str, Any]) -> None:
    items = _read_json(HISTORY_FILE)
    items.append(record)
    _write_json(HISTORY_FILE, items)
