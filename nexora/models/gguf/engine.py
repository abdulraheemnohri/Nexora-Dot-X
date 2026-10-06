"""GGUF provider via llama.cpp server or python bindings (optional)."""
from pathlib import Path
from nexora.models.base import ModelProvider, ModelInfo
from nexora.config import settings


class GGUFProvider(ModelProvider):
    backend = "gguf"

    def __init__(self, model_path=None):
        self._model = None
        self._name = ""
        self._detail = ""
        self._server_url = "http://127.0.0.1:8080"

    def _llama_server_up(self) -> bool:
        try:
            import httpx
            r = httpx.get(f"{self._server_url}/health", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def load(self, path: str) -> bool:
        if not Path(path).exists():
            self._detail = f"model file not found: {path}"
            return False
        if self._llama_server_up():
            self._model = path
            self._name = Path(path).stem
            return True
        try:
            from llama_cpp import Llama  # type: ignore
            self._model = Llama(model_path=path, n_ctx=4096)
            self._name = Path(path).stem
            return True
        except ImportError:
            self._detail = "neither llama.cpp server (127.0.0.1:8080) nor llama-cpp-python installed"
            return False
        except Exception as e:
            self._detail = f"load failed: {e}"
            return False

    def unload(self) -> None:
        self._model = None

    def generate(self, prompt: str, *, temperature: float = 0.7,
                 max_tokens: int = 512, system_prompt: str | None = None) -> str:
        if system_prompt:\n            prompt = system_prompt + "\\n\\n" + prompt\n        if self._model is None:
            raise RuntimeError("GGUF: no model loaded")
        if isinstance(self._model, str):  # llama.cpp server mode
            import httpx
            r = httpx.post(f"{self._server_url}/completion",
                           json={"prompt": prompt, "n_predict": max_tokens,
                                 "temperature": temperature}, timeout=300)
            r.raise_for_status()
            return r.json().get("content", "")
        return self._model(prompt, max_tokens=max_tokens,
                           temperature=temperature)["choices"][0]["text"]

    def stream(self, prompt: str, **kwargs):
        if isinstance(self._model, str):
            import httpx
            with httpx.stream("POST", f"{self._server_url}/completion",
                              json={"prompt": prompt, "n_predict": kwargs.get("max_tokens", 512),
                                    "temperature": kwargs.get("temperature", 0.7)}, timeout=300) as r:
                for line in r.iter_lines():
                    if line.startswith("data: "):
                        import json
                        try:
                            yield json.loads(line[6:]).get("content", "")
                        except Exception:
                            pass
        else:
            yield self.generate(prompt, **kwargs)

    def health(self) -> ModelInfo:
        if self._model is not None:
            return ModelInfo(self._name, self.backend, loaded=True, status="ready", context=4096)
        gguf_dir = settings.model_dir / "gguf"
        found = list(gguf_dir.glob("*.gguf")) if gguf_dir.exists() else []
        if found:
            return ModelInfo(found[0].stem, self.backend, status="unavailable",
                             detail=f"{len(found)} GGUF model(s) found, not loaded")
        return ModelInfo("gguf", self.backend, status="unavailable",
                         detail="no .gguf models in models/gguf")
