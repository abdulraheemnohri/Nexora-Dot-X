"""System 1 orchestrator: the only authority that authorizes execution."""
from nexora.control.policy import PolicyEngine, Decision
from nexora.control.approvals import ApprovalCenter
from nexora.control.audit import audit


class Orchestrator:
    def __init__(self):
        self.policy = PolicyEngine()
        self.approvals = ApprovalCenter()

    def authorize(self, tool: str, action: str, *, dry_run: bool = False, reason: str = ""):
        decision = self.policy.evaluate(tool, action, dry_run=dry_run)
        approval = None
        if decision.decision is Decision.ASK:
            approval = self.approvals.request(tool, action, reason or decision.reason,
                                              decision.risk.value)
        audit("orchestrator", tool=tool, action=action,
              decision=decision.decision.value, outcome=decision.reason)
        return decision, approval
