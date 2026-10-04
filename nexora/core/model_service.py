"""Model management actions behind the /models UI.

Shows router health per backend and exposes load/refresh actions.
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
