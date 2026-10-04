from dataclasses import dataclass, field
import uuid

@dataclass
class PlanStep:
    instruction: str
    tool: str | None = None
    action: str | None = None
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

class Planner:
    """Deterministic baseline planner; model-backed planning plugs into this contract."""
    def plan(self, goal: str) -> list[PlanStep]:
        return [PlanStep(instruction=goal)]

