"""System 1 step executor.

Approval resume executes the exact immutable tool/action stored in the approval
record. It does not re-run a potentially changed policy decision.
"""
from nexora.control.policy import PolicyEngine, Decision
from nexora.control.approvals import ApprovalCenter
from nexora.control.audit import audit
from nexora.core.events import bus
from nexora.database import repositories as repo
from nexora.database.models import Approval


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

    def execute(self, step: dict, *, bot_id=None, task_id=None, step_id=None, dry_run=False) -> StepOutcome:
        import asyncio
        return asyncio.run(self.execute_async(step, bot_id=bot_id, task_id=task_id, step_id=step_id, dry_run=dry_run))

    async def execute_async(self, step: dict, *, bot_id=None, task_id=None, step_id=None, dry_run=False) -> StepOutcome:
        tool = step.get("tool") or step.get("kind", "work")
        action = step.get("action") or step.get("description", "")
        decision = self.policy.evaluate(tool, action, dry_run=dry_run)
        audit(
            "agent", bot_id=bot_id, task_id=task_id, tool=tool,
            action=action, decision=decision.decision.value,
            outcome=decision.reason,
        )
        if decision.decision is Decision.BLOCK:
            return StepOutcome(False, f"BLOCKED by policy: {decision.reason}")
        if decision.decision is Decision.ASK:
            a = self.approvals.request(
                tool, action, decision.reason, decision.risk.value,
                task_id=task_id, step_id=step_id
            )
            bus.publish(
                "approval.requested",
                {"id": a.id, "tool": tool, "action": action},
            )
            return StepOutcome(
                False, "waiting for user approval", pending_approval=a.id
            )
        if dry_run:
            return StepOutcome(
                True, f"[dry-run] would execute {tool}: {action}"
            )
        if self.tools is None:
            return StepOutcome(
                True,
                f"step '{step.get('kind', tool)}' completed "
                "(no tool side effects configured)",
            )
        result = await self.tools.run_async(tool, action)
        return StepOutcome(
            result.get("ok", True), result.get("output", "")
        )

    async def execute_async(self, step: dict, *, bot_id=None, task_id=None, step_id=None, dry_run=False) -> StepOutcome:
        tool = step.get("tool") or step.get("kind", "work")
        action = step.get("action") or step.get("description", "")
        decision = self.policy.evaluate(tool, action, dry_run=dry_run)
        audit("agent", bot_id=bot_id, task_id=task_id, tool=tool, action=action, decision=decision.decision.value, outcome=decision.reason)
        if decision.decision is Decision.BLOCK:
            return StepOutcome(False, f"BLOCKED by policy: {decision.reason}")
        if decision.decision is Decision.ASK:
            a = self.approvals.request(tool, action, decision.reason, decision.risk.value, task_id=task_id, step_id=step_id)
            bus.publish("approval.requested", {"id": a.id, "tool": tool, "action": action})
            return StepOutcome(False, "waiting for user approval", pending_approval=a.id)
        if dry_run:
            return StepOutcome(True, f"[dry-run] would execute {tool}: {action}")
        if self.tools is None:
            return StepOutcome(True, f"step '{step.get('kind', tool)}' completed (no tool side effects configured)")
        result = await self.tools.run_async(tool, action)
        return StepOutcome(result.get("ok", True), result.get("output", ""))

    async def resume_async(self, approval_id: str) -> StepOutcome:
        """Execute only the exact action that the user approved.

        A pending approval contains the canonical tool and action. Because the
        record is immutable after creation and approval, no planner/model
        output is consulted during resume. If a future version adds mutable
        approvals, it must add an action digest and verify it here.
        """
        approval = repo.get_by_id(Approval, approval_id)
        if approval is None:
            return StepOutcome(False, "approval not found")
        if approval.status != "approved":
            return StepOutcome(False, "approval not approved")

        approval = self.approvals.claim(approval_id)
        if approval is None:
            return StepOutcome(False, "approval already claimed or executed")

        tool = approval.tool
        action = approval.action
        audit(
            "user", tool=tool, action=action, decision="ALLOW",
            outcome=f"executing approved action {approval.id}",
        )
        try:
            if self.tools is None:
                result = {"ok": True, "output": f"approved action recorded: {tool}: {action}"}
            else:
                result = await self.tools.run_async(tool, action)
            if result.get("ok", True):
                self.approvals.mark_executed(approval_id)
            else:
                self.approvals.mark_failed(approval_id)
            return StepOutcome(
                result.get("ok", True), result.get("output", "")
            )
        except Exception as exc:
            self.approvals.mark_failed(approval_id)
            return StepOutcome(False, f"approved action failed: {exc}")
