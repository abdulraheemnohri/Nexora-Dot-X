"""Unified model provider interface (Model Bus)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ModelInfo:
    name: str
    backend: str
    loaded: bool = False
    status: str = "unavailable"  # ready/loading/error/unavailable
    context: int = 0
    detail: str = ""


class ModelProvider(ABC):
    backend: str = "abstract"

    @abstractmethod
    def load(self, name: str) -> bool: ...

    @abstractmethod
    def unload(self) -> None: ...

    @abstractmethod
    def generate(self, prompt: str, *, temperature: float = 0.7,
                 max_tokens: int = 512) -> str: ...

    @abstractmethod
    def stream(self, prompt: str, **kwargs):
        """Yield generation chunks."""
        yield self.generate(prompt, **kwargs)

    @abstractmethod
    def health(self) -> ModelInfo: ...

    def metadata(self) -> ModelInfo:
        return self.health()

    def context_info(self) -> dict:
        return {"context": 0, "used": 0}
