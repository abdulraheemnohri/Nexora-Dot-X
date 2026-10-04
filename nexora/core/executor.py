"""Step executor: routes planned steps through System 1 and the tool registry."""
from nexora.control.policy import PolicyEngine, Decision
from nexora.control.approvals import ApprovalCenter
from nexora.control.audit import audit
from nexora.core.events import bus


class StepOutcome:
    def __init__(self, ok: bool, output: str = "", pending_approval=None):
        self.ok = ok
        self.output = output
        self.pending_approval = pending_approval


class Executor:
    def __init__(self, tool_registry=None):
        self.policy = PolicyEngine()
        self.approvals = ApprovalCenter()
        self.tools = tool_registry

    def execute(self, step: dict, *, bot_id=None, task_id=None, dry_run=False) -> StepOutcome:
        tool = step.get("tool") or step.get("kind", "work")
        action = step.get("action") or step.get("description", "")
        decision = self.policy.evaluate(tool, action, dry_run=dry_run)
        audit("agent", bot_id=bot_id, task_id=task_id, tool=tool,
              action=action, decision=decision.decision.value,
              outcome=decision.reason)
        if decision.decision is Decision.BLOCK:
            return StepOutcome(False, f"BLOCKED by policy: {decision.reason}")
        if decision.decision is Decision.ASK:
            a = self.approvals.request(tool, action, decision.reason, decision.risk.value)
            bus.publish("approval.requested", {"id": a.id, "tool": tool, "action": action})
            return StepOutcome(False, "waiting for user approval", pending_approval=a.id)
        if dry_run:
            return StepOutcome(True, f"[dry-run] would execute {tool}: {action}")
        if self.tools is None:
            return StepOutcome(True, f"step '{step.get('kind', tool)}' completed (no tool side effects configured)")
        result = self.tools.run(tool, action)
        return StepOutcome(result.get("ok", True), result.get("output", ""))

    def resume(self, approval_id: str) -> StepOutcome:
        """Continue execution after a user decision on a pending approval."""
        from nexora.database import repositories as repo
        from nexora.database.models import Approval
        a = repo.get_by_id(Approval, approval_id)
        if a is None or a.status != "approved":
            return StepOutcome(False, "approval not approved")
        step = {"tool": a.tool, "action": a.action}
        return self.execute(step, dry_run=False)
