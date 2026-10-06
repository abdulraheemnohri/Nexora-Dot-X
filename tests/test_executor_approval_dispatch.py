import pytest

from nexora.core.executor import Executor


@pytest.mark.asyncio
async def test_resume_dispatches_stored_structured_arguments(monkeypatch):
    from nexora.core import executor as executor_module

    class Approval:
        id = "approval-2"
        tool = "browser.navigate"
        action = "navigate"
        status = "approved"
        task_id = "task-2"
        arguments_json = '{"session_id":"s1","url":"https://example.com"}'

    captured = {}

    monkeypatch.setattr(executor_module.repo, "get_by_id", lambda model, approval_id: Approval())

    class Approvals:
        def claim(self, approval_id):
            return Approval()

        def mark_executed(self, approval_id):
            return Approval()

        def mark_failed(self, approval_id):
            return Approval()

    class Tools:
        async def run_async(self, tool, action):
            captured["tool"] = tool
            captured["action"] = action
            return {"ok": True, "output": "done"}

    runner = Executor(Tools())
    runner.approvals = Approvals()

    result = await runner.resume_async("approval-2")

    assert result.ok
    assert captured["tool"] == "browser.navigate"
    assert captured["action"]["session_id"] == "s1"
    assert captured["action"]["url"] == "https://example.com"
