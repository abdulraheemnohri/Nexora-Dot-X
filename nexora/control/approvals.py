from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
import uuid

class ApprovalStatus(StrEnum):
    PENDING="PENDING"; APPROVED="APPROVED"; REJECTED="REJECTED"; CANCELLED="CANCELLED"

@dataclass
class Approval:
    tool: str
    action: str
    reason: str
    risk: str = "medium"
    params: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)

class ApprovalCenter:
    def __init__(self):
        self.items: dict[str, Approval] = {}
    def request(self, tool, action, reason, risk="medium", params=None):
        item=Approval(tool,action,reason,risk,params or {})
        self.items[item.id]=item
        return item
    def decide(self, approval_id, approved: bool):
        item=self.items[approval_id]
        item.status=ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        return item
    def pending(self): return [x for x in self.items.values() if x.status==ApprovalStatus.PENDING]
