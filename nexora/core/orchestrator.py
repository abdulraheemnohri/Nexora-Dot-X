from nexora.control.policy import PolicyEngine, Decision
from nexora.control.approvals import ApprovalCenter

class Orchestrator:
    """System 1 is the only authority allowed to authorize tool execution."""
    def __init__(self):
        self.policy=PolicyEngine()
        self.approvals=ApprovalCenter()

    def authorize(self, tool, action, *, dry_run=False, reason=""):
        decision=self.policy.evaluate(tool, action, dry_run=dry_run)
        if decision.decision is Decision.ASK:
            approval=self.approvals.request(tool,action,reason or decision.reason)
            return decision, approval
        return decision, None
