from nexora.control.policy import PolicyEngine, Decision
from nexora.control.approvals import ApprovalCenter
from nexora.tools.registry import ToolRegistry

class System1Executor:
    def __init__(self, registry=None, policy=None, approvals=None):
        self.registry=registry or ToolRegistry()
        self.policy=policy or PolicyEngine()
        self.approvals=approvals or ApprovalCenter()

    def request(self, tool, action, reason=""):
        d=self.policy.evaluate(tool,action)
        if d.decision is Decision.BLOCK: return {"decision":"BLOCK","reason":d.reason}
        if d.decision is Decision.ASK:
            a=self.approvals.request(tool,action,reason or d.reason)
            return {"decision":"ASK","reason":d.reason,"approval_id":a.id}
        return {"decision":"ALLOW","reason":d.reason}

