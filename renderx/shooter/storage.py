"""Persistent best-run data stored in the user's local application data."""

import json
import os
from pathlib import Path


def score_path() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return root / "RenderX" / "field-operations.json"


def load_best() -> dict:
    try:
        data = json.loads(score_path().read_text(encoding="utf-8"))
        return {"score": max(0, int(data.get("score", 0))),
                "wave": max(0, int(data.get("wave", 0))),
                "difficulty": str(data.get("difficulty", "NORMAL"))}
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {"score": 0, "wave": 0, "difficulty": "NORMAL"}


def save_if_best(score: int, wave: int, difficulty: str) -> dict:
    best = load_best()
    if score > best["score"]:
        data = {"score": int(score), "wave": int(wave),
                "difficulty": str(difficulty)}
        path = score_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
        temporary.replace(path)
        return data
    return best
