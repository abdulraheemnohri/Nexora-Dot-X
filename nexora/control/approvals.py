"""Approval center: pending human-in-the-loop decisions."""
from nexora.database.models import Approval
from nexora.database import repositories as repo

# single shared policy engine so "always allow" grants apply everywhere
from nexora.control.policy import PolicyEngine

_policy = PolicyEngine()


class ApprovalCenter:

    def request(self, tool: str, action: str, reason: str = "", risk: str = "medium") -> Approval:
        a = Approval(tool=tool, action=action, reason=reason, risk=risk)
        return repo.add_obj(a)

    def pending(self) -> list:
        return repo.query(Approval, Approval.status == "pending")

    def approve(self, approval_id: str, always: bool = False) -> Approval | None:
        a = repo.get_by_id(Approval, approval_id)
        if a is None:
            return None
        a.status = "approved"
        repo.update_fields(a, status="approved")
        if always:
            key = (" ".join((a.action or "").split()))
            _policy.allowed_always.add((a.tool, key))
            from nexora.control.audit import audit
            audit("user", tool=a.tool, action=a.action, decision="ALLOW",
                  outcome="approved as always-allow rule")
        return a

    def reject(self, approval_id: str) -> Approval | None:
        a = repo.get_by_id(Approval, approval_id)
        if a is None:
            return None
        return repo.update_fields(a, status="rejected")

    def decide(self, approval_id: str, approved: bool, always: bool = False):
        """User decision entry point (server + CLI)."""
        if approved:
            return self.approve(approval_id, always=always)
        return self.reject(approval_id)
