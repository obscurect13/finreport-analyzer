import json
import os
import hashlib
from typing import Optional, Dict

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(key: str) -> str:
    return os.path.join(CACHE_DIR, f"{key}.json")


def make_key(text: str, language: str, filename: str = "") -> str:
    """Create a stable hash key from text, language, and filename."""
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    h.update(language.encode("utf-8"))
    h.update(filename.encode("utf-8"))
    return h.hexdigest()


def get_cached_result(key: str) -> Optional[Dict]:
    """Return cached result dict if present, else None."""
    path = _cache_path(key)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def set_cached_result(key: str, result: Dict) -> None:
    """Store result dict in cache."""
    path = _cache_path(key)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f)
