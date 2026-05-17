import pytest


def test_validate_env_passes_when_key_set(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
    from src.config import validate_env

    # Should not raise or exit
    validate_env()


def test_validate_env_exits_when_key_missing(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from src.config import validate_env

    with pytest.raises(SystemExit) as exc_info:
        validate_env()
    assert exc_info.value.code == 1


def test_validate_env_prints_missing_vars(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from src.config import validate_env

    with pytest.raises(SystemExit):
        validate_env()
    captured = capsys.readouterr()
    assert "ANTHROPIC_API_KEY" in captured.err
    assert "Missing required environment variables" in captured.err
