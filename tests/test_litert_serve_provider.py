"""Tests for the litert-serve model-bus provider (HTTP fully faked)."""
import pytest

from nexora.models.base import ModelInfo
from nexora.models.litert.openai_local import LiteRTServeProvider


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("HTTP " + str(self.status_code))


class FakeHttp:
    def __init__(self, models_payload=None, chat_payload=None, fail_get=False):
        self.models_payload = models_payload or {"data": [{"id": "gemma4-e2b"}]}
        self.chat_payload = chat_payload or {
            "choices": [{"message": {"content": "hello back"}}]}
        self.fail_get = fail_get
        self.posts = []

    def get(self, url, timeout=None):
        if self.fail_get:
            raise ConnectionError("down")
        return FakeResponse(self.models_payload)

    def post(self, url, json=None, timeout=None):
        self.posts.append((url, json))
        return FakeResponse(self.chat_payload)


def test_loopback_allowed_in_local_only(monkeypatch):
    import nexora.config as cfg
    monkeypatch.setattr(cfg.settings, "local_only", True, raising=False)
    p = LiteRTServeProvider(client=FakeHttp())
    assert p._is_loopback() is True
    assert p._allowed() is True
    assert p.health().status == "ready"


def test_health_ready_reports_models():
    p = LiteRTServeProvider(client=FakeHttp())
    info = p.health()
    assert isinstance(info, ModelInfo)
    assert info.status == "ready"
    assert "gemma4-e2b" in info.detail


def test_health_unreachable_when_server_down():
    p = LiteRTServeProvider(client=FakeHttp(fail_get=True))
    info = p.health()
    assert info.status == "unavailable"
    assert "nexora litert serve" in info.detail


def test_generate_uses_chat_completions():
    http = FakeHttp()
    p = LiteRTServeProvider(model="gemma4-e2b", client=http)
    ou
t = p.generate("hello")
    assert out == "hello back"
    url, body = http.posts[0]
    assert url.endswith("/v1/chat/completions")
    assert body["model"] == "gemma4-e2b"
    assert body["messages"][0]["content"] == "hello"


def test_stream_yields_generation():
    p = LiteRTServeProvider(model="m", client=FakeHttp())
    chunks = list(p.stream("hi"))
    assert chunks == ["hello back"]


def test_load_picks_first_served_model():
    p = LiteRTServeProvider(client=FakeHttp())
    assert p.load("") is True
    assert p.model == "gemma4-e2b"


def test_load_with_explicit_name():
    p = LiteRTServeProvider(client=FakeHttp())
    assert p.load("my-model") is True
    assert p.model == "my-model"


def test_non_loopback_blocked_in_local_only(monkeypatch):
    import nexora.config as cfg
    monkeypatch.setattr(cfg.settings, "local_only", True, raising=False)
    p = LiteRTServeProvider(base_url="https://api.example.com", client=FakeHttp())
    assert p._is_loopback() is False
    assert p._allowed() is False
    info = p.health()
    assert info.status == "unavailable"
    with pytest.raises(RuntimeError):
        p.generate("hi")


def test_non_loopback_allowed_when_local_only_off(monkeypatch):
    import nexora.config as cfg
    monkeypatch.setattr(cfg.settings, "local_only", False, raising=False)
    p = LiteRTServeProvider(base_url="https://api.example.com", client=FakeHttp())
    assert p._allowed() is True
    assert p.health().status == "ready"
