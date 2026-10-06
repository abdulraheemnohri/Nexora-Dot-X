"""Model-bus provider backed by the local litert-lm serve process.

Talks to the OpenAI-compatible server started with 'nexora litert serve'
(GET /v1/models, POST /v1/chat/completions, default 127.0.0.1:9379).
The server runs on-device, so loopback requests stay allowed even in
local-only mode; non-loopback URLs respect NEXORA_LOCAL_ONLY as usual.
"""
from urllib.parse import urlparse

from nexora.config import settings
from nexora.models.base import ModelProvider, ModelInfo

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1", "[::1]"}


class LiteRTServeProvider(ModelProvider):
    backend = "litert-serve"

    def __init__(self, base_url: str = "", model: str = "", client=None):
        import os
        self.base_url = (base_url or os.getenv("NEXORA_LITERT_SERVE_URL",
                                               "http://127.0.0.1:9379")).rstrip("/")
        self.model = model
        self._client = client  # injectable for tests

    # ---- helpers ----------------------------------------------------------

    def _http(self):
        if self._client is not None:
            return self._client
        import httpx
        return httpx

    def _is_loopback(self) -> bool:
        host = (urlparse(self.base_url).hostname or "").lower()
        return host in LOOPBACK_HOSTS

    def _allowed(self) -> bool:
        """Loopback litert-lm serve is on-device: allowed even local-only."""
        return self._is_loopback() or not settings.local_only

    def _models_url(self) -> str:
        return self.base_url + "/v1/models"

    def _chat_url(self) -> str:
        return self.base_url + "/v1/chat/completions"

    # ---- ModelProvider API -------------------------------------------------

    def load(self, name: str) -> bool:
        info = self.health()
        if info.status != "ready":
            return False
        if name:
            self.model = name
        if not self.model:
            data = self._http().get(self._models_url(), timeout=5).json()
            models = [m.get("id") for m in data.get("data", []) if m.get("id")]
            self.model = models[0] if models else ""
        return True

    def unload(self) -> None:
        self.model = ""

    def generate(self, prompt: str, *, temperature: float = 0.7,
                 max_tokens: int = 512, system_prompt: str | None = None) -> str:
        if system_prompt:\n            prompt = system_prompt + "\\n\\n" + prompt\n        if not self._allowed():
            raise RuntimeError(
                "litert-serve disabled: non-loopback URL in local-only mode")
        r = self._http().post(
            self._chat_url(),
            json={"model": self.model or "default",
                  "messages": [{"role": "user", "content": prompt}],
                  "temperature": temperature, "max_tokens": max_tokens},
            timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def stream(self, prompt: str, **kwargs):
        yield self.generate(prompt, **kwargs)

    def health(self) -> ModelInfo:
        if not self._allowed():
            return ModelInfo("litert-serve", self.backend,
                             detail="disabled: non-loopback URL in local-only mode")
        try:
            r = self._http().get(self._models_url(), timeout=2)
            if r.status_code != 200:
                return ModelInfo("litert-serve", self.backend,
                                 detail=f"unreachable (HTTP {r.status_code})")
            data = r.json()
            names = [m.get("id") for m in data.get("data", []) if m.get("id")]
        except Exception:
            return ModelInfo("litert-serve", self.backend,
                             detail="not running (start with: nexora litert serve)")
        detail = "models: " + ", ".join(names) if names else "no models served"
        return ModelInfo(self.model or (names[0] if names else "litert-serve"),
                         self.backend, loaded=True, status="ready", detail=detail)
