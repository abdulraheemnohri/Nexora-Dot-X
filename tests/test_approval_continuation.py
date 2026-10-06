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


def test_approval_request_persists_structured_arguments(monkeypatch):
    captured = {}
    monkeypatch.setattr("nexora.control.approvals.repo.add_obj", lambda obj: captured.setdefault("obj", obj))
    approval = ApprovalCenter().request(
        "browser.navigate", '{"session_id":"s1"}', "approval", "high",
        task_id="task-1", step_id="step-2", arguments={"session_id":"s1","url":"https://example.com"},
    )
    assert approval.arguments_json == '{"session_id":"s1","url":"https://example.com"}'
