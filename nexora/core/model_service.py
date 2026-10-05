"""Model management actions behind the /models UI.

Shows router health per backend and exposes discover/load/unload actions.
Never fakes a model: statuses come straight from provider health().
"""
from nexora.core.events import bus
from nexora.models.router import ModelRouter


class ModelService:
    def __init__(self, router=None):
        self.router = router or ModelRouter()

    def status(self) -> list:
        out = []
        for info in self.router.available():
            out.append({"backend": info.backend, "status": info.status,
                        "model": getattr(info, "model", None) or "",
                        "detail": getattr(info, "detail", "") or ""})
        return out

    def ready_backend(self) -> str | None:
        p = self.router.ready()
        return p.backend if p else None

    def scan_litert(self) -> int:
        from nexora.models.litert.diagnostics import scan
        from nexora.config import settings
        found = len(scan(str(settings.model_dir))["models"])
        bus.publish("models.scan", {"found": found})
        return found

    # ---- provider registry helpers ----------------------------------------

    def _providers(self) -> dict:
        # the router keeps providers keyed by backend name
        return getattr(self.router, "_providers", {})

    def _provider(self, backend: str):
        return self._providers().get(backend)

    def discover(self) -> list:
        """List loadable models per backend (no loading happens)."""
        out = []
        for backend, provider in self._providers().items():
            entry = {"backend": backend, "models": []}
            # ollama exposes its pulled models directly
            if hasattr(provider, "models"):
                try:
                    entry["models"] = provider.models()
                except Exception:
                    entry["models"] = []
            # gguf / litert discover from disk
            elif hasattr(provider, "backend") and provider.backend == "gguf":
                try:
                    from nexora.config import settings
                    gguf_dir = settings.model_dir / "gguf"
                    if gguf_dir.exists():
                        entry["models"] = [str(p) for p in
                                           sorted(gguf_dir.glob("*.gguf"))]
                except Exception:
                    entry["models"] = []
            elif hasattr(provider, "backend") and provider.backend == "litert":
                try:
                    from nexora.models.litert.diagnostics import scan
                    from nexora.config import settings
                    entry["models"] = [m["path"] if isinstance(m, dict)
                                       else str(m)
                                       for m in scan(str(settings.model_dir))["models"]]
                except Exception:
                    entry["models"] = []
            out.append(entry)
        return out

    def load(self, backend: str, name: str) -> dict:
        provider = self._provider(backend)
        if provider is None:
            return {"ok": False, "error": "unknown backend: " + str(backend)}
        try:
            ok = provider.load(name)
        except Exception as e:
            ok = False
            provider_detail = str(e)
            bus.publish("models.load", {"backend": backend, "name": name,
                                        "ok": False})
            return {"ok": False, "error": provider_detail}
        info = provider.health()
        bus.publish("models.load", {"backend": backend, "name": name,
                                    "ok": bool(ok)})
        return {"ok": bool(ok), "backend": backend,
                "model": info.name, "status": info.status,
                "detail": info.detail}

    def unload(self, backend: str) -> dict:
        provider = self._provider(backend)
        if provider is None:
            return {"ok": False, "error": "unknown backend: " + str(backend)}
        try:
            provider.unload()
        except Exception as e:
            bus.publish("models.unload", {"backend": backend, "ok": False})
            return {"ok": False, "error": str(e)}
        info = provider.health()
        bus.publish("models.unload", {"backend": backend, "ok": True})
        return {"ok": True, "backend": backend,
                "status": info.status, "detail": info.detail}
