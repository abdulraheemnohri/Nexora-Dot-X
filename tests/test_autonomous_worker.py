import pytest
from nexora.core.autonomous_worker import AutonomousWorker, WorkerLimits

class FakeTasks:
    def __init__(self): self.status=[]; self.done=False
    def resume(self, task_id): return object()
    def next_resumable_step(self, task_id): return None if self.done else type("S",(),{"id":"s1","attempts":0})()
    def checkpoint(self, *args, **kwargs): self.done=True
    def set_status(self, *args, **kwargs): self.status.append(args)

@pytest.mark.asyncio
async def test_worker_completes_task():
    tasks=FakeTasks(); worker=AutonomousWorker(tasks, WorkerLimits())
    await worker.enqueue("t1")
    assert await worker.run_once(lambda step: _ok())
    assert any(x[1] == "COMPLETED" for x in tasks.status)

async def _ok():
    return "done"


@pytest.mark.asyncio
async def test_worker_recovers_persisted_work():
    class RecoverTasks(FakeTasks):
        def list(self, status=None, limit=200):
            if status == "QUEUED":
                return [type("T", (), {"id":"q1", "priority":2})()]
            if status == "RETRYING":
                return [type("T", (), {"id":"r1", "priority":1})()]
            if status == "RUNNING":
                return [type("T", (), {"id":"run1", "priority":1})()]
            return []
    tasks = RecoverTasks()
    worker = AutonomousWorker(tasks, WorkerLimits())
    recovered = await worker.recover()
    assert set(recovered) == {"q1", "r1", "run1"}
    assert worker._queued == {"q1", "r1", "run1"}
    assert any(args[1] == "QUEUED" for args in tasks.status)
