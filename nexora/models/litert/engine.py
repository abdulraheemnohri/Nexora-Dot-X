class LiteRTEngine:
    """Adapter boundary for the installed LiteRT-LM runtime.

    The dependency is optional so Nexora can boot without LiteRT-LM.
    A compatible runtime adapter should be supplied here when installed.
    """
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.loaded = False

    async def load(self):
        try:
            import litert_lm  # type: ignore
        except ImportError as exc:
            raise RuntimeError("LiteRT-LM is not installed; install nexora-dot-x[litert].") from exc
        self.loaded = True

    async def unload(self):
        self.loaded = False

    async def generate(self, prompt: str, **kwargs):
        if not self.loaded:
            raise RuntimeError("LiteRT model is not loaded")
        raise NotImplementedError("Bind this adapter to the installed LiteRT-LM API.")
