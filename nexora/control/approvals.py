"""Human-in-the-loop approval center.

Approvals are single-use execution grants. Once resumed, an approved record is
marked executed so it cannot be replayed.
"""
import time

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
                risk: str = "medium") -> Approval:
        a = Approval(tool=tool, action=action, reason=reason, risk=risk)
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

    def mark_executed(self, approval_id: str) -> Approval | None:
        a = repo.get_by_id(Approval, approval_id)
        if a is None or a.status != "approved":
            return None
        return repo.update_fields(
            a, status="executed", decided_at=a.decided_at or time.time()
        )

    def decide(self, approval_id: str, approved: bool, always: bool = False):
        if approved:
            return self.approve(approval_id, always=always)
        return self.reject(approval_id)
