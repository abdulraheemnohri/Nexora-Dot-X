"""Multi-agent delegation: a coordinator Dot fans work out to workers.

Workers run in parallel, results are aggregated. Every worker step still
passes System 1 (Executor does that). Bots cannot bypass System 1.
"""
import asyncio
from dataclasses import dataclass, field

from nexora.core.task_engine import TaskEngine, TaskStatus
from nexora.core.events import bus


@dataclass
class WorkerJob:
    dot_id: str
    description: str
    result: str = ""
    status: str = "QUEUED"


@dataclass
class Delegation:
    coordinator_id: str
    task_id: str
    workers: list = field(default_factory=list)


class Coordinator:
    def __init__(self, executor, bots=None, max_workers: int = 4, timeout: int = 300):
        self.executor = executor
        self.bots = bots
        self.max_workers = max_workers
        self.timeout = timeout
        self.tasks = TaskEngine()

    def delegate(self, coordinator_id: str, task_id: str,
                 worker_ids, steps) -> Delegation:
        worker_ids = list(worker_ids)[:self.max_workers]
        d = Delegation(coordinator_id, task_id)
        for wid in worker_ids:
            for step in steps:
                d.workers.append(WorkerJob(dot_id=wid,
                                          description=step.get("description", "")))
        bus.publish("delegation.created",
                    {"task": task_id, "coordinator": coordinator_id,
                     "workers": len(d.workers)})
        return d

    async def run(self, delegation: Delegation) -> dict:
        """Run worker jobs in parallel; aggregate outcomes."""

        async def one(job: WorkerJob) -> WorkerJob:
            outcome = self.executor.execute(
                {"kind": "work", "description": job.description},
                bot_id=job.dot_id, task_id=delegation.task_id)
            job.result = outcome.output
            job.status = "COMPLETED" if outcome.ok else "FAILED"
            return job

        done = await asyncio.wait_for(
            asyncio.gather(*(one(j) for j in delegation.workers),
                           return_exceptions=True),
            timeout=self.timeout)
        ok = sum(1 for j in done if getattr(j, "status", "") == "COMPLETED")
        failed = len(done) - ok
        bus.publish("delegation.finished",
                    {"task": delegation.task_id, "ok": ok, "failed": failed})
        self.tasks.set_status(delegation.task_id, TaskStatus.COMPLETED.value,
                              result="delegation: " + str(ok) + " ok / "
                                     + str(failed) + " failed")
        return {"ok": ok, "failed": failed,
                "results": [{"dot": j.dot_id, "status": j.status,
                             "result": j.result} for j in delegation.workers]}
