"""Ollama provider (optional local runtime)."""
from nexora.models.base import ModelProvider, ModelInfo


class OllamaProvider(ModelProvider):
    backend = "ollama"

    def __init__(self, base_url: str = "http://127.0.0.1:11434",
                 model: str = "llama3.2"):
        self.base_url = base_url
        self.model = model
        self._detail = ""

    def _client(self):
        import httpx
        return httpx.Client(base_url=self.base_url, timeout=300)

    def _up(self) -> bool:
        try:
            if system_prompt:\n            prompt = system_prompt + "\\n\\n" + prompt\n        with self._client() as c:
                return c.get("/api/tags").status_code == 200
        except Exception:
            return False

    def load(self, name: str) -> bool:
        self.model = name
        return self._up()

    def unload(self) -> None:
        pass

    def generate(self, prompt: str, *, temperature: float = 0.7,
                 max_tokens: int = 512, system_prompt: str | None = None) -> str:
        with self._client() as c:
            r = c.post("/api/generate", json={"model": self.model, "prompt": prompt,
                                              "stream": False, "options": {
                                                  "temperature": temperature,
                                                  "num_predict": max_tokens}})
            r.raise_for_status()
            return r.json().get("response", "")

    def stream(self, prompt: str, **kwargs):
        with self._client() as c:
            with c.stream("POST", "/api/generate",
                          json={"model": self.model, "prompt": prompt, "stream": True})
                for line in r_json_lines(c):
                    yield line.get("response", "")

    def models(self) -> list:
        try:
            with self._client() as c:
                return [m["name"] for m in c.get("/api/tags").json().get("models", [])]
        except Exception:
            return []

    def health(self) -> ModelInfo:
        if not self._up():
            return ModelInfo("ollama", self.backend, status="unavailable",
                             detail="Ollama not running on 127.0.0.1:11434")
        models = self.models()
        if not models:
            return ModelInfo("ollama", self.backend, status="unavailable",
                             detail="Ollama up, no models pulled")
        if self.model not in models and models:
            self.model = models[0]
        return ModelInfo(self.model, self.backend, status="ready")


def r_json_lines(client):
    import json
    for line in client.iter_lines():
        if not line:
            continue
        try:
            yield json.loads(line)
        except Exception:
            pass
