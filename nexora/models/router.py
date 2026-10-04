"""Model Router: picks a provider by routing policy with failover.

Local providers have priority; remote providers are strictly optional and
refused when NEXORA_LOCAL_ONLY=true.
"""
from nexora.config import settings
from nexora.models.base import ModelProvider, ModelInfo

ROUTING_POLICIES = ("fastest", "cheapest", "local-only", "best-quality",
                    "coding", "reasoning", "tool-use", "low-memory")


class ModelRouter:
    def __init__(self):
        self._providers: dict[str, ModelProvider] = {}
        self._order: list[str] = []  # failover order
        self._register_defaults()

    def _register_defaults(self):
        try:
            from nexora.models.litert.engine import LiteRTProvider
            self.register(LiteRTProvider(), first=True)
        except Exception:
            pass

    def register(self, provider: ModelProvider, first: bool = False):
        self._providers[provider.backend] = provider
        if first:
            self._order.insert(0, provider.backend)
        else:
            self._order.append(provider.backend)

    def available(self) -> list[ModelInfo]:
        return [p.health() for p in self._providers.values()]

    def select(self, policy: str = "local-only") -> ModelProvider | None:
        for backend in self._order:
            p = self._providers.get(backend)
            if p is None:
                continue
            info = p.health()
            if info.status == "ready":
                return p
        return None

    def generate(self, prompt: str, *, policy: str = "local-only", **kwargs) -> str:
        if policy not in ("local-only",) and not settings.local_only:
            for backend in self._order:
                p = self._providers.get(backend)
                if p and p.health().status == "ready":
                    return p.generate(prompt, **kwargs)
        p = self.select()
        if p is None:
            raise RuntimeError(
                "No model provider ready. Install a model (nexora litert scan) "
                "or configure a provider; remote inference is disabled in local-only mode.")
        return p.generate(prompt, **kwargs)
