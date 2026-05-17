import os
import json
from src.cache import make_key, get_cached_result, set_cached_result


def test_cache_roundtrip(tmp_path, monkeypatch):
    # Use temporary cache directory
    temp_dir = tmp_path / "cache"
    temp_dir.mkdir()
    monkeypatch.setattr('src.cache.CACHE_DIR', str(temp_dir))

    text = "sample report"
    lang = "fr"
    key = make_key(text, lang)
    assert get_cached_result(key) is None

    data = {"foo": "bar"}
    set_cached_result(key, data)
    # Verify file exists and content matches
    cached = get_cached_result(key)
    assert cached == data
    # Direct file inspection
    path = os.path.join(str(temp_dir), f"{key}.json")
    with open(path, "r", encoding="utf-8") as f:
        assert json.load(f) == data
