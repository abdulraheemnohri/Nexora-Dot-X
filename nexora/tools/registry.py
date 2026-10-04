from dataclasses import dataclass

@dataclass
class ToolSpec:
    name: str
    description: str
    risk: str = "low"
    enabled: bool = True
    timeout: float = 30.0

class ToolRegistry:
    def __init__(self): self._tools={}
    def register(self, spec: ToolSpec): self._tools[spec.name]=spec
    def get(self,name): return self._tools[name]
    def list(self): return list(self._tools.values())
