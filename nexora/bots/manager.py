from dataclasses import dataclass, field
import uuid

@dataclass
class DotProfile:
    name: str
    mission: str = ""
    description: str = ""
    personality: str = ""
    system_prompt: str = ""
    model: str = ""
    memory_mode: str = "local"
    workspace: str = ""
    skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

class DotManager:
    def __init__(self): self.dots={}
    def create(self, **kwargs):
        dot=DotProfile(**kwargs); self.dots[dot.id]=dot; return dot
    def get(self, dot_id): return self.dots[dot_id]
    def list(self): return list(self.dots.values())
