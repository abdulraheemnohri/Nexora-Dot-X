from dataclasses import dataclass,asdict
from pathlib import Path
import json
@dataclass
class ModelRecord:
    id:str
    provider:str
    path:str
    enabled:bool=True
    metadata:dict|None=None
class ModelRegistry:
    def __init__(self,path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True); self.records={}; self.load()
    def load(self):
        if self.path.exists(): self.records={x["id"]:ModelRecord(**x) for x in json.loads(self.path.read_text())}
    def save(self): self.path.write_text(json.dumps([asdict(x) for x in self.records.values()],indent=2))
    def upsert(self,record): self.records[record.id]=record; self.save(); return record
    def remove(self,id): self.records.pop(id); self.save()
    def list(self): return list(self.records.values())
