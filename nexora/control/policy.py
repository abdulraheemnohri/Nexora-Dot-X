from enum import Enum
from dataclasses import dataclass

class Decision(str, Enum):
    ALLOW = "ALLOW"
    ASK = "ASK"
    BLOCK = "BLOCK"

@dataclass(frozen=True)
class PolicyDecision:
    decision: Decision
    reason: str

class PolicyEngine:
    def evaluate(self, tool: str, action: str, *, dry_run: bool = False) -> PolicyDecision:
        if dry_run:
            return PolicyDecision(Decision.ALLOW, "Simulation/dry-run")
        text = f"{tool} {action}".lower()
        if "rm -rf" in text or "format disk" in text or "credential extraction" in text:
            return PolicyDecision(Decision.BLOCK, "Dangerous operation blocked by default")
        if tool in {"terminal", "git"}:
            return PolicyDecision(Decision.ASK, "Sensitive tool requires approval")
        return PolicyDecision(Decision.ALLOW, "Allowed by default policy")
