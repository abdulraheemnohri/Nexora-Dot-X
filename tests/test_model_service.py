"""Tests for ModelService discover/load/unload (fake router, no runtimes)."""
from nexora.models.base import ModelInfo
from nexora.core.model_service import ModelService


class FakeProvider:
    backend = "fake"

    def __init__(self):
        self.loaded = None
        self.unloaded = False

    def models(self):
        return ["m1", "m2"]

    def load(self, name):
        self.loaded = name
        return True

    def unload(self):
        self.unloaded = True
        self.loaded = None

    def health(self):
        if self.loaded:
            return ModelInfo(self.loaded, self.backend, loaded=True,
                             status="ready")
        return ModelInfo(self.backend, self.backend, status="unavailable")


class FakeRouter:
    def __init__(self, providers):
        self._providers = providers

    def available(self):
        return [p.health() for p in self._providers.values()]

    def ready(self):
        for p in self._providers.values():
            if p.health().status == "ready":
                return p
        return None


def test_status_lists_all_backends():
    p = FakeProvider()
    svc = ModelService(router=FakeRouter({"fake": p}))
    rows = svc.status()
    assert len(rows) == 1
    assert rows[0]["backend"] == "fake"
    assert rows[0]["status"] == "unavailable"


def test_load_unknown_backend():
    svc = ModelService(router=FakeRouter({}))
    r = svc.load("nope", "x")
    assert r["ok"] is False
    assert "unknown backend" in r["error"]


def test_load_success():
    p = FakeProvider()
    svc = ModelService(router=FakeRouter({"fake": p}))
    r = svc.load("fake", "m1")
    assert r["ok"] is True
    assert r["model"] == "m1"
    assert r["status"] == "ready"
    assert svc.ready_backend() == "fake"


def test_unload():
    p = FakeProvider()
    p.load("m1")
    svc = ModelService(router=FakeRouter({"fake": p}))
    r = svc.unload("fake")
    assert r["ok"] is True
    assert p.unloaded is True
    assert svc.ready_backend() is None


def test_unload_unknown_backend():
    svc = ModelService(router=FakeRouter({}))
    r = svc.unload("nope")
    assert r["ok"] is False


def test_discover_lists_provider_models():
    p = FakeProvider()
    svc = ModelService(router=FakeRouter({"fake": p}))
    entries = svc.discover()
    assert entries[0]["backend"] == "fake"
    assert entries[0]["models"] == ["m1", "m2"]
