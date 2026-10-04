class ModelRouter:
    def __init__(self,registry,manager): self.registry=registry; self.manager=manager
    def choose(self,policy="local-only"):
        records=[r for r in self.registry.list() if r.enabled]
        if policy=="local-only": records=[r for r in records if r.provider in {"litert","llama.cpp","ollama","transformers"}]
        if not records: raise RuntimeError("No model matches routing policy")
        return records[0]
