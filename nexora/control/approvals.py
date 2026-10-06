"""Human-in-the-loop approval center.

Approvals are single-use execution grants. Execution uses an atomic claim so
two workers cannot consume the same approved action concurrently.
"""
import time
import json

from nexora.database.models import Approval
from nexora.database import repositories as repo

from nexora.control.policy import PolicyEngine

_policy = PolicyEngine()

try:
    from nexora.control import always_allow
    always_allow.load_grants()
except Exception:
    pass


class ApprovalCenter:
    def request(self, tool: str, action: str, reason: str = "",
                risk: str = "medium", task_id: str | None = None, step_id: str | None = None,
                arguments: dict | None = None) -> Approval:
        encoded = json.dumps(arguments, sort_keys=True, separators=(",", ":")) if arguments is not None else None
        a = Approval(tool=tool, action=action, arguments_json=encoded, reason=reason, risk=risk, task_id=task_id, step_id=step_id)
        return repo.add_obj(a)

    def pending(self) -> list:
        return repo.query(Approval, Approval.status == "pending")

    def approve(self, approval_id: str, always: bool = False) -> Approval | None:
        a = repo.get_by_id(Approval, approval_id)
        if a is None or a.status != "pending":
            return None
        a.status = "approved"
        a.decided_at = time.time()
        repo.update_fields(a, status="approved", decided_at=a.decided_at)
        if always:
            from nexora.control import always_allow
            always_allow.save_grant(a.tool, a.action)
            from nexora.control.audit import audit
            audit(
                "user", tool=a.tool, action=a.action, decision="ALLOW",
                outcome="approved as always-allow rule (persisted)",
            )
        return a

    def reject(self, approval_id: str) -> Approval | None:
        a = repo.get_by_id(Approval, approval_id)
        if a is None or a.status != "pending":
            return None
        a.decided_at = time.time()
        return repo.update_fields(
            a, status="rejected", decided_at=a.decided_at
        )

    def claim(self, approval_id: str) -> Approval | None:
        """Atomically claim an approved approval for one execution attempt."""
        return repo.claim_approval(Approval, approval_id)

    def mark_executed(self, approval_id: str) -> Approval | None:
        a = repo.get_by_id(Approval, approval_id)
        if a is None or a.status != "executing":
            return None
        return repo.update_fields(
            a, status="executed", decided_at=a.decided_at or time.time()
        )

    def mark_failed(self, approval_id: str) -> Approval | None:
        a = repo.get_by_id(Approval, approval_id)
        if a is None or a.status != "executing":
            return None
        return repo.update_fields(
            a, status="failed", decided_at=a.decided_at or time.time()
        )

    def decide(self, approval_id: str, approved: bool, always: bool = False):
        if approved:
            return self.approve(approval_id, always=always)
        return self.reject(approval_id)
