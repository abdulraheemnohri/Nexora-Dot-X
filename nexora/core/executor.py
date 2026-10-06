"""System 1 step executor.

Approval resume executes the exact immutable tool/action stored in the approval
record. It does not re-run a potentially changed policy decision.
"""
import asyncio
import json

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
        return asyncio.run(
            self.execute_async(
                step,
                bot_id=bot_id,
                task_id=task_id,
                step_id=step_id,
                dry_run=dry_run,
            )
        )

    async def execute_async(
        self,
        step: dict,
        *,
        bot_id=None,
        task_id=None,
        step_id=None,
        dry_run=False,
    ) -> StepOutcome:
        tool = step.get("tool") or step.get("kind", "work")
        arguments = step.get("arguments") if isinstance(step.get("arguments"), dict) else None
        action = (
            step.get("action")
            or step.get("description", "")
            or (
                json.dumps(arguments, sort_keys=True, separators=(",", ":"))
                if arguments is not None
                else ""
            )
        )
        dispatch_action = arguments if arguments is not None else action

        decision = self.policy.evaluate(tool, action, dry_run=dry_run)
        audit(
            "agent",
            bot_id=bot_id,
            task_id=task_id,
            tool=tool,
            action=action,
            decision=decision.decision.value,
            outcome=decision.reason,
        )

        if decision.decision is Decision.BLOCK:
            return StepOutcome(False, f"BLOCKED by policy: {decision.reason}")

        if decision.decision is Decision.ASK:
            approval = self.approvals.request(
                tool,
                action,
                decision.reason,
                decision.risk.value,
                task_id=task_id,
                step_id=step_id,
                arguments=arguments,
            )
            bus.publish(
                "approval.requested",
                {"id": approval.id, "tool": tool, "action": action},
            )
            return StepOutcome(
                False,
                "waiting for user approval",
                pending_approval=approval.id,
            )

        if dry_run:
            return StepOutcome(True, f"[dry-run] would execute {tool}: {action}")

        if self.tools is None:
            return StepOutcome(
                True,
                f"step '{step.get('kind', tool)}' completed (no tool side effects configured)",
            )

        result = await self.tools.run_async(tool, dispatch_action)
        return StepOutcome(result.get("ok", True), result.get("output", ""))

    def resume(self, approval_id: str) -> StepOutcome:
        """Synchronous compatibility wrapper for approval continuation."""
        return asyncio.run(self.resume_async(approval_id))

    async def resume_async(self, approval_id: str) -> StepOutcome:
        """Execute only the exact action stored in the approved record.

        Resume does not consult planner/model output or re-evaluate a mutable
        proposal. Structured arguments captured with the approval are decoded
        and passed to the tool registry; otherwise the canonical action string
        is used. The approval is atomically claimed before execution.
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
        dispatch_action = action

        if getattr(approval, "arguments_json", None):
            try:
                dispatch_action = json.loads(approval.arguments_json)
            except (TypeError, json.JSONDecodeError):
                return StepOutcome(False, "approved action has invalid structured arguments")

        audit(
            "user",
            task_id=approval.task_id,
            tool=tool,
            action=action,
            decision="ALLOW",
            outcome=f"executing approved action {approval.id}",
        )

        try:
            if self.tools is None:
                result = {
                    "ok": True,
                    "output": f"approved action recorded: {tool}: {action}",
                }
            else:
                result = await self.tools.run_async(tool, dispatch_action)

            if result.get("ok", True):
                self.approvals.mark_executed(approval_id)
            else:
                self.approvals.mark_failed(approval_id)

            return StepOutcome(
                result.get("ok", True),
                result.get("output", ""),
            )
        except Exception as exc:
            self.approvals.mark_failed(approval_id)
            return StepOutcome(False, f"approved action failed: {exc}")
