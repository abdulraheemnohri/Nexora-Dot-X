"""System-1 gated action bridge for local action-model outputs."""
from dataclasses import dataclass
from typing import Any, Callable
from nexora.control.policy import Decision, PolicyEngine
from nexora.tools.registry import ToolRegistry

@dataclass
class ActionProposal:
    tool: str
    arguments: dict[str, Any]
    confidence: float = 1.0
    source: str = "action-model"

class ActionBridge:
    def __init__(self, registry: ToolRegistry, policy: PolicyEngine | None = None,
                 min_confidence: float = 0.75):
        self.registry = registry
        self.policy = policy or PolicyEngine()
        self.min_confidence = min_confidence

    def parse(self, payload: dict[str, Any]) -> ActionProposal:
        tool = str(payload.get("tool", "")).strip()
        args = payload.get("arguments", {})
        confidence = float(payload.get("confidence", 0.0))
        if not tool: raise ValueError("action proposal requires tool")
        if not isinstance(args, dict): raise ValueError("arguments must be an object")
        if not 0 <= confidence <= 1: raise ValueError("confidence must be between 0 and 1")
        return ActionProposal(tool, args, confidence, str(payload.get("source", "action-model")))

    def authorize(self, proposal: ActionProposal):
        if proposal.confidence < self.min_confidence:
            return Decision.ASK, "confidence below threshold"
        error = self.registry.validate(proposal.tool, proposal.arguments)
        if error:
            return Decision.BLOCK, error
        action = proposal.arguments.get("action", proposal.arguments)
        result = self.policy.evaluate(proposal.tool, str(action))
        return result.decision, result.reason

    def dispatch(self, proposal: ActionProposal):
        decision, reason = self.authorize(proposal)
        if decision is not Decision.ALLOW:
            return {"ok": False, "decision": decision.value, "reason": reason,
                    "tool": proposal.tool}
        return {"ok": True, "decision": decision.value,
                "result": self.registry.run(proposal.tool, proposal.arguments)}


    async def dispatch_async(self, proposal: ActionProposal):
        """Async System-1 dispatch for action-model proposals."""
        decision, reason = self.authorize(proposal)
        if decision is not Decision.ALLOW:
            return {"ok": False, "decision": decision.value, "reason": reason,
                    "tool": proposal.tool}
        return {"ok": True, "decision": decision.value,
                "result": await self.registry.run_async(proposal.tool, proposal.arguments)}
