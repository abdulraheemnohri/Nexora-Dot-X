"""Policy-aware Model Bus router.

Providers advertise capabilities through ModelInfo. Routing is deterministic,
local-first, and refuses remote inference in local-only mode.
"""
from nexora.config import settings
from nexora.models.base import ModelProvider, ModelInfo

ROUTING_POLICIES = (
    "fastest", "cheapest", "local-only", "best-quality",
    "coding", "reasoning", "tool-use", "low-memory",
)

_CAPABILITY_HINTS = {
    "coding": ("coding", "code"),
    "reasoning": ("reasoning", "thinking"),
    "tool-use": ("tool", "function"),
}


class ModelRouter:
    def __init__(self):
        self._providers: dict[str, ModelProvider] = {}
        self._order: list[str] = []
        self._register_defaults()

    def _register_defaults(self):
        for mod, cls in (
            ("nexora.models.litert.engine", "LiteRTProvider"),
            ("nexora.models.litert.openai_local", "LiteRTServeProvider"),
            ("nexora.models.gguf.engine", "GGUFProvider"),
            ("nexora.models.ollama.engine", "OllamaProvider"),
        ):
            try:
                m = __import__(mod, fromlist=[cls])
                self.register(getattr(m, cls)())
            except Exception:
                pass

    def register(self, provider: ModelProvider, first: bool = False):
        self._providers[provider.backend] = provider
        if provider.backend not in self._order:
            if first:
                self._order.insert(0, provider.backend)
            else:
                self._order.append(provider.backend)

    def available(self) -> list[ModelInfo]:
        return [p.health() for p in self._providers.values()]

    def _candidates(self) -> list[tuple[ModelProvider, ModelInfo]]:
        out = []
        for backend in self._order:
            provider = self._providers.get(backend)
            if provider is None:
                continue
            info = provider.health()
            if info.status == "ready":
                out.append((provider, info))
        return out

    @staticmethod
    def _score(info: ModelInfo, policy: str) -> float:
        name = (info.name + " " + info.backend + " " + info.detail).lower()
        score = 0.0
        if info.backend == "litert":
            score += 40.0
        if info.loaded:
            score += 20.0
        if info.context:
            score += min(info.context / 4096.0, 8.0)
        if policy == "low-memory":
            score += 30.0 if info.context <= 4096 else -20.0
        elif policy == "fastest":
            score += 10.0 if info.loaded else 0.0
        elif policy == "cheapest":
            score += 10.0 if info.backend in {"litert", "gguf", "ollama"} else 0.0
        elif policy == "best-quality":
            score += min(info.context / 1024.0, 32.0)
        elif policy in _CAPABILITY_HINTS:
            if any(h in name for h in _CAPABILITY_HINTS[policy]):
                score += 30.0
        return score

    def select(self, policy: str = "local-only") -> ModelProvider | None:
        policy = policy if policy in ROUTING_POLICIES else "local-only"
        candidates = self._candidates()
        if not candidates:
            return None
        if policy == "local-only" or settings.local_only:
            candidates = [
                item for item in candidates
                if item[0].backend not in {"openai", "anthropic", "gemini", "remote"}
            ]
        if not candidates:
            return None
        return max(candidates, key=lambda item: self._score(item[1], policy))[0]

    def ready(self, policy: str = "local-only") -> ModelProvider | None:
        return self.select(policy)

    def generate(self, prompt: str, *, policy: str = "local-only", **kwargs) -> str:
        provider = self.select(policy)
        if provider is None:
            if settings.local_only:
                raise RuntimeError(
                    "No local model ready (LiteRT-LM/GGUF/Ollama). "
                    "Install one: nexora litert scan / models/gguf / ollama pull"
                )
            from nexora.models.remote.openai_compat import OpenAICompatProvider
            remote = OpenAICompatProvider()
            if remote.health().status == "ready":
                return remote.generate(prompt, **kwargs)
            raise RuntimeError("No model provider ready (local or remote)")
        return provider.generate(prompt, **kwargs)

    def stream(self, prompt: str, *, policy: str = "local-only", **kwargs):
        provider = self.select(policy)
        if provider is None:
            raise RuntimeError("No model provider ready")
        yield from provider.stream(prompt, **kwargs)
