"""Native LiteRT-LM provider using the public Engine/Conversation API.

The adapter intentionally keeps the optional runtime isolated so Nexora can
start without LiteRT-LM installed. It does not invent a private LiteRT API.
"""
from pathlib import Path
from typing import Any, Iterator

from nexora.models.base import ModelProvider, ModelInfo
from nexora.models.litert.diagnostics import scan, runtime_available
from nexora.models.litert.manifest import load_manifest


class LiteRTProvider(ModelProvider):
    backend = "litert"

    def __init__(self, model_path=None):
        self._engine = None
        self._conversation = None
        self._manifest = None
        self._model_path = str(model_path) if model_path else None
        self._detail = ""

    def _import_runtime(self):
        try:
            import litert_lm  # type: ignore
            return litert_lm
        except ImportError as exc:
            raise RuntimeError(
                "LiteRT-LM is not installed; use pip install nexora-dot-x[litert]"
            ) from exc

    def load(self, path: str) -> bool:
        if not runtime_available():
            self._detail = (
                "litert-lm runtime not installed "
                "(pip install nexora-dot-x[litert])"
            )
            return False
        try:
            litert_lm = self._import_runtime()
            engine_cls = getattr(litert_lm, "Engine", None)
            if engine_cls is None:
                raise RuntimeError(
                    "Installed LiteRT-LM package exposes no Engine API; "
                    "check the installed litert-lm version."
                )
            self._engine = engine_cls(model_path=str(path))
            self._conversation = None
            self._model_path = str(path)
            self._manifest = load_manifest(Path(path))
            self._detail = "loaded with LiteRT-LM Engine"
            return True
        except Exception as exc:  # optional runtime
            self._engine = None
            self._conversation = None
            self._detail = f"load failed: {exc}"
            return False

    def _conversation_for(self, system_prompt: str | None = None):
        if self._engine is None:
            raise RuntimeError("LiteRT-LM: no model loaded")
        if self._conversation is None:
            create = getattr(self._engine, "create_conversation", None)
            if create is None:
                raise RuntimeError(
                    "Installed LiteRT-LM Engine has no create_conversation API"
                )
            kwargs: dict[str, Any] = {}
            if system_prompt:
                kwargs["system_message"] = system_prompt
            self._conversation = create(**kwargs)
        return self._conversation

    def unload(self) -> None:
        for obj in (self._conversation, self._engine):
            close = getattr(obj, "close", None) if obj is not None else None
            if callable(close):
                try:
                    close()
                except Exception:
                    pass
        self._conversation = None
        self._engine = None
        self._manifest = None

    @staticmethod
    def _text(result: Any) -> str:
        if result is None:
            return ""
        if isinstance(result, str):
            return result
        for attr in ("text", "content", "response"):
            value = getattr(result, attr, None)
            if isinstance(value, str):
                return value
        return str(result)

    def generate(self, prompt: str, *, temperature: float = 0.7,
                 max_tokens: int = 512, system_prompt: str | None = None,
                 **kwargs) -> str:
        conversation = self._conversation_for(system_prompt)
        send = getattr(conversation, "send_message", None)
        if send is None:
            raise RuntimeError(
                "Installed LiteRT-LM Conversation has no send_message API"
            )
        result = send(prompt)
        return self._text(result)

    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        conversation = self._conversation_for(kwargs.pop("system_prompt", None))
        send = getattr(conversation, "send_message", None)
        if send is None:
            raise RuntimeError(
                "Installed LiteRT-LM Conversation has no send_message API"
            )
        result = send(prompt)
        stream = getattr(result, "stream", None)
        if callable(stream):
            for chunk in stream():
                yield self._text(chunk)
            return
        if hasattr(result, "__iter__") and not isinstance(result, (str, bytes, dict)):
            for chunk in result:
                yield self._text(chunk)
            return
        yield self._text(result)

    def health(self) -> ModelInfo:
        if self._engine is not None:
            return ModelInfo(
                self._manifest.name if self._manifest else "litert",
                self.backend,
                loaded=True,
                status="ready",
                context=self._manifest.context if self._manifest else 0,
                detail=self._detail,
            )
        info = scan()
        if not info["runtime_available"]:
            return ModelInfo(
                "litert", self.backend, status="unavailable",
                detail="runtime not installed",
            )
        if not info["models"]:
            return ModelInfo(
                "litert", self.backend, status="unavailable",
                detail="no .litertlm model installed",
            )
        m = info["models"][0]
        return ModelInfo(
            m["name"], self.backend, status="unavailable",
            detail=self._detail or "model found, not loaded",
            context=m["context"],
        )
