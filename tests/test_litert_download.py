"""Tests for the LiteRT model download module (pure logic, no network)."""
from pathlib import Path

import pytest

from nexora.models.litert import download as dl


def _fake_urlopen(monkeypatch, chunks):
    """Fake urlopen yielding the given byte chunks, then EOF."""
    state = {"i": 0}

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self, n):
            i = state["i"]
            if i >= len(chunks):
                return b""
            state["i"] += 1
            return chunks[i]

    monkeypatch.setattr(dl.urllib.request, "urlopen", lambda url: FakeResp())


def test_download_refused_in_local_only(monkeypatch, tmp_path):
    monkeypatch.setenv("NEXORA_LOCAL_ONLY", "true")
    with pytest.raises(PermissionError):
        dl.download("https://example.com/model.litertlm",
                    tmp_path / "m.litertlm", allow_network=False)


def test_download_allowed_when_flag_set(monkeypatch, tmp_path):
    monkeypatch.setattr(dl, "_allow_network", lambda allow: True)
    _fake_urlopen(monkeypatch, [b"data"])
    path = dl.download("https://example.com/m.litertlm", tmp_path / "m.litertlm")
    assert Path(path).exists()
    assert Path(path).read_bytes() == b"data"


def test_ensure_default_model_cached(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXORA_LOCAL_ONLY", "true")
    dest = tmp_path / "litert" / (dl.DEFAULT_MODEL_REPO.split("/")[-1] + ".litertlm")
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"model")
    result = dl.ensure_default_model(str(tmp_path))
    assert result["ok"] and result["cached"] is True
    assert result["path"] == str(dest)


def test_download_default_model_refused_when_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXORA_LOCAL_ONLY", "true")
    with pytest.raises(PermissionError):
        dl.download_default_model(str(tmp_path))


def test_download_default_model_allowed(tmp_path, monkeypatch):
    monkeypatch.setattr(dl, "_allow_network", lambda allow: True)
    _fake_urlopen(monkeypatch, [b"model"])
    result = dl.download_default_model(str(tmp_path))
    assert result["ok"] and result["cached"] is False
    assert Path(result["path"]).exists()


def test_local_only_env_false_permits(monkeypatch, tmp_path):
    monkeypatch.setenv("NEXORA_LOCAL_ONLY", "false")
    _fake_urlopen(monkeypatch, [b"x"])
    path = dl.download("https://example.com/x", tmp_path / "x")
    assert Path(path).exists()
