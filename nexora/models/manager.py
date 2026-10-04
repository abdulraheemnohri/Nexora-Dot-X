class ModelManager:
    def __init__(self): self.providers={}
    def register(self,name,provider): self.providers[name]=provider
    def names(self): return list(self.providers)
    def get(self,name): return self.providers[name]
    async def health(self):
        out={}
        for name,p in self.providers.items():
            try: out[name]=await p.health()
            except Exception: out[name]=False
        return out
