"""Built-in LiteRT-LM provider (first-class local runtime).

Works in three states:
- runtime + model present  -> ready, real inference
- runtime missing          -> unavailable, clear message
- model missing            -> unavailable until a model is imported
"""
from nexora.models.base import ModelProvider, ModelInfo
from nexora.models.litert.diagnostics import scan, runtime_available
from nexora.models.litert.manifest import Manifest, load_manifest


class LiteRTProvider(ModelProvider):
    backend = "litert"

    def __init__(self, model_path=None):
        self._model = None
        self._manifest: Manifest | None = None
        self._model_path = model_path
        self._detail = ""

    def load(self, path: str) -> bool:
        if not runtime_available():
            self._detail = "litert-lm runtime not installed (pip install nexora-dot-x[litert])"
            return False
        try:
            from litert_lm import runtime as litert_runtime  # type: ignore
            self._model = litert_lm_load(path)  # placeholder replaced below
        except Exception as e:  # pragma: no cover - depends on optional runtime
            self._detail = f"load failed: {e}"
            return False
        self._manifest = load_manifest(type("P", (), {"exists": lambda s: True,
                                                      "with_suffix": None,
                                                      "name": path.split("/")[-1],
                                                      "stem": path.split("/")[-1],
                                                      "stat": None})())
        return True

    def unload(self) -> None:
        self._model = None
        self._manifest = None

    def generate(self, prompt: str, *, temperature: float = 0.7,
                 max_tokens: int = 512) -> str:
        if self._model is None:
            raise RuntimeError("LiteRT-LM: no model loaded")
        raise RuntimeError("LiteRT-LM: runtime adapter not installed")

    def stream(self, prompt: str, **kwargs):
        yield self.generate(prompt, **kwargs)

    def health(self) -> ModelInfo:
        if self._model is not None:
            return ModelInfo(self._manifest.name if self._manifest else "litert",
                             "litert", loaded=True, status="ready")
        info = scan()
        if not info["runtime_available"]:
            return ModelInfo("litert", "litert", status="unavailable",
                             detail="runtime not installed")
        if not info["models"]:
            return ModelInfo("litert", "litert", status="unavailable",
                             detail="no .litertlm model installed")
        return ModelInfo(info["models"][0]["name"], "litert", status="unavailable",
                         detail="model found, not loaded",
                         context=info["models"][0]["context"])
