from nexora.control.approvals import ApprovalCenter
from nexora.database.models import Approval


def test_approval_request_persists_task_step_link(monkeypatch):
    captured = {}

    def add_obj(obj):
        captured["obj"] = obj
        return obj

    center = ApprovalCenter()
    monkeypatch.setattr(
        "nexora.control.approvals.repo.add_obj", add_obj
    )
    approval = center.request(
        "terminal", "echo hello", "approval needed", "medium",
        task_id="task-1", step_id="step-1",
    )
    assert isinstance(approval, Approval)
    assert approval.task_id == "task-1"
    assert approval.step_id == "step-1"
    assert captured["obj"] is approval
