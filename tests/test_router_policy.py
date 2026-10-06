from nexora.models.base import ModelInfo, ModelProvider
from nexora.models.router import ModelRouter


class FakeProvider(ModelProvider):
    def __init__(self, backend, name, context=4096, loaded=True):
        self.backend = backend
        self.name = name
        self.context = context
        self.loaded = loaded

    def load(self, name):
        return True

    def unload(self):
        pass

    def generate(self, prompt, **kwargs):
        return self.name

    def stream(self, prompt, **kwargs):
        yield self.name

    def health(self):
        return ModelInfo(
            self.name, self.backend, loaded=self.loaded,
            status="ready", context=self.context,
        )


def test_local_only_prefers_litert():
    router = ModelRouter()
    router._providers.clear()
    router._order.clear()
    router.register(FakeProvider("ollama", "ollama-model"))
    router.register(FakeProvider("litert", "litert-model"))
    assert router.select("local-only").backend == "litert"
