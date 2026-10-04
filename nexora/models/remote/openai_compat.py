"""OpenAI-compatible remote provider adapter (optional, policy-gated)."""
from nexora.config import settings
from nexora.models.base import ModelProvider, ModelInfo


class OpenAICompatProvider(ModelProvider):
    backend = "openai-compatible"

    def __init__(self, base_url: str = "", api_key_env: str = "NEXORA_OPENAI_API_KEY",
                 model: str = ""):
        import os
        self.base_url = base_url or os.getenv("NEXORA_OPENAI_BASE_URL", "")
        self.api_key = os.getenv(api_key_env, "")
        self.model = model

    def _allowed(self) -> bool:
        return not settings.local_only and self.api_key and self.base_url

    def load(self, name: str) -> bool:
        return self._allowed()

    def unload(self) -> None:
        pass

    def generate(self, prompt: str, *, temperature: float = 0.7,
                 max_tokens: int = 512) -> str:
        if not self._allowed():
            raise RuntimeError("Remote inference disabled (local-only mode or missing credentials)")
        import httpx
        r = httpx.post(f"{self.base_url}/chat/completions",
                       headers={"Authorization": f"Bearer {self.api_key}"},
                       json={"model": self.model,
                             "messages": [{"role": "user", "content": prompt}],
                             "temperature": temperature, "max_tokens": max_tokens},
                       timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def stream(self, prompt: str, **kwargs):
        yield self.generate(prompt, **kwargs)

    def health(self) -> ModelInfo:
        if settings.local_only:
            return ModelInfo("remote", self.backend,
                             detail="disabled: NEXORA_LOCAL_ONLY=true")
        if not (self.api_key and self.base_url):
            return ModelInfo("remote", self.backend,
                             detail="not configured (base URL / API key)")
        return ModelInfo(self.model or "remote", self.backend, status="ready")
