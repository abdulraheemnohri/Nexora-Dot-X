"""Built-in LiteRT-LM provider (first-class local runtime).

States:
- runtime + model loaded -> ready, real inference
- runtime missing       -> unavailable, with install hint
- model missing         -> unavailable until a .litertlm model is imported
"""
from pathlib import Path
from nexora.models.base import ModelProvider, ModelInfo
from nexora.models.litert.diagnostics import scan, runtime_available
from nexora.models.litert.manifest import load_manifest


class LiteRTProvider(ModelProvider):
    backend = "litert"

    def __init__(self, model_path=None):
        self._model = None
        self._manifest = None
        self._model_path = model_path
        self._detail = ""

    def load(self, path: str) -> bool:
        if not runtime_available():
            self._detail = "litert-lm runtime not installed (pip install nexora-dot-x[litert])"
            return False
        try:
            from litert_lm import runtime as litert_runtime  # type: ignore
            session = litert_runtime.Session(model=str(path))
        except Exception as e:  # pragma: no cover - optional runtime
            self._detail = f"load failed: {e}"
            return False
        self._model = session
        self._manifest = load_manifest(Path(path))
        return True

    def unload(self) -> None:
        self._model = None
        self._manifest = None

    def generate(self, prompt: str, *, temperature: float = 0.7,
                 max_tokens: int = 512) -> str:
        if self._model is None:
            raise RuntimeError("LiteRT-LM: no model loaded")
        try:
            return self._model.generate(prompt)
        except Exception as e:  # pragma: no cover
            raise RuntimeError(f"LiteRT-LM inference failed: {e}") from e

    def stream(self, prompt: str, **kwargs):
        yield self.generate(prompt, **kwargs)

    def health(self) -> ModelInfo:
        if self._model is not None:
            return ModelInfo(self._manifest.name if self._manifest else "litert",
                             self.backend, loaded=True, status="ready",
                             context=self._manifest.context if self._manifest else 0)
        info = scan()
        if not info["runtime_available"]:
            return ModelInfo("litert", self.backend, status="unavailable",
                             detail="runtime not installed")
        if not info["models"]:
            return ModelInfo("litert", self.backend, status="unavailable",
                             detail="no .litertlm model installed")
        m = info["models"][0]
        return ModelInfo(m["name"], self.backend, status="unavailable",
                         detail="model found, not loaded", context=m["context"])
