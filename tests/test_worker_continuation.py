import pytest

from nexora.core.autonomous_worker import AutonomousWorker, WorkerLimits


class FakeStep:
    def __init__(self, step_id, index):
        self.id = step_id
        self.step_index = index
        self.attempts = 0


class FakeTask:
    id = "task-1"
    priority = 1


class FakeTasks:
    def __init__(self):
        self.steps = [FakeStep("s1", 0), FakeStep("s2", 1)]
        self.statuses = []
        self.completed = set()

    def resume(self, task_id):
        return FakeTask()

    def next_resumable_step(self, task_id):
        for step in self.steps:
            if step.id not in self.completed:
                return step
        return None

    def checkpoint(self, step_id, **kwargs):
        if kwargs.get("status") == "completed":
            self.completed.add(step_id)

    def set_status(self, task_id, status, **kwargs):
        self.statuses.append(status)


@pytest.mark.asyncio
async def test_worker_requeues_remaining_steps():
    tasks = FakeTasks()
    worker = AutonomousWorker(tasks, WorkerLimits())
    await worker.enqueue("task-1")

    calls = []

    async def execute(step):
        calls.append(step.id)
        return "ok-" + step.id

    assert await worker.run_once(execute)
    assert calls == ["s1"]
    assert tasks.statuses[-1] == "QUEUED"

    assert await worker.run_once(execute)
    assert calls == ["s1", "s2"]
    assert tasks.statuses[-1] == "COMPLETED"
