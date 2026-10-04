from pathlib import Path
from nexora.models.litert.diagnostics import scan
from nexora.models.litert.engine import LiteRTEngine

class LiteRTModelManager:
    def __init__(self,model_dir):
        self.root=Path(model_dir); self.root.mkdir(parents=True,exist_ok=True)
    def list(self): return scan(str(self.root))["models"]
    def find(self,name):
        matches=[p for p in self.list() if Path(p).name==name or Path(p).stem==name]
        return matches[0] if matches else None
    def import_path(self,source):
        src=Path(source).resolve()
        if not src.exists(): raise FileNotFoundError(source)
        if src.is_file() and src.suffix!=".litertlm": raise ValueError("Only .litertlm models are accepted")
        target=self.root/src.name
        if src.is_dir():
            import shutil; shutil.copytree(src,target,dirs_exist_ok=True)
        else:
            import shutil; shutil.copy2(src,target)
        return str(target)
    def remove(self,name):
        import shutil
        p=self.find(name)
        if not p: raise FileNotFoundError(name)
        path=Path(p)
        if path.is_dir(): shutil.rmtree(path)
        else: path.unlink()
        return str(path)
    async def test(self,name,prompt="Reply with exactly: Nexora OK"):
        p=self.find(name)
        if not p: raise FileNotFoundError(name)
        e=LiteRTEngine(p); await e.load()
        try: return await e.generate(prompt)
        finally: await e.unload()
