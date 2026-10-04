"""Model Router: picks a provider by routing policy with failover.

Local provider priority: LiteRT-LM -> GGUF -> Ollama -> remote (optional).
Remote providers are strictly refused when NEXORA_LOCAL_ONLY=true.
"""
from nexora.config import settings
from nexora.models.base import ModelProvider, ModelInfo

ROUTING_POLICIES = ("fastest", "cheapest", "local-only", "best-quality",
                    "coding", "reasoning", "tool-use", "low-memory")


class ModelRouter:
    def __init__(self):
        self._providers: dict[str, ModelProvider] = {}
        self._order: list[str] = []
        self._register_defaults()

    def _register_defaults(self):
        for mod, cls in (("nexora.models.litert.engine", "LiteRTProvider"),
                         ("nexora.models.gguf.engine", "GGUFProvider"),
                         ("nexora.models.ollama.engine", "OllamaProvider")):
            try:
                m = __import__(mod, fromlist=[cls])
                self.register(getattr(m, cls)())
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

    def ready(self) -> ModelProvider | None:
        for backend in self._order:
            p = self._providers.get(backend)
            if p and p.health().status == "ready":
                return p
        return None

    def select(self, policy: str = "local-only") -> ModelProvider | None:
        return self.ready()

    def generate(self, prompt: str, *, policy: str = "local-only", **kwargs) -> str:
        p = self.ready()
        if p is None:
            if settings.local_only:
                raise RuntimeError("No local model ready (LiteRT-LM/GGUF/Ollama). "
                                   "Install one: nexora litert scan / models/gguf / ollama pull")
            from nexora.models.remote.openai_compat import OpenAICompatProvider
            remote = OpenAICompatProvider()
            if remote.health().status == "ready":
                return remote.generate(prompt, **kwargs)
            raise RuntimeError("No model provider ready (local or remote)")
        return p.generate(prompt, **kwargs)

    def stream(self, prompt: str, *, policy: str = "local-only", **kwargs):
        p = self.ready()
        if p is None:
            raise RuntimeError("No local model ready")
        yield from p.stream(prompt, **kwargs)
