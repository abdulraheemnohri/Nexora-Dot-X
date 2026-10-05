"""Durable background worker for Nexora tasks.

The worker is intentionally executor-injected: System 1 remains responsible for
approvals/policy while this component owns queueing, retries, cancellation and
resource bounds.
"""
import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable
from nexora.core.task_engine import TaskEngine, TaskStatus

@dataclass
class WorkerLimits:
    max_concurrent: int = 1
    max_attempts: int = 3
    step_timeout: float = 300.0

class AutonomousWorker:
    def __init__(self, tasks: TaskEngine | None = None, limits: WorkerLimits | None = None):
        self.tasks = tasks or TaskEngine()
        self.limits = limits or WorkerLimits()
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._queued: set[str] = set()
        self._cancelled: set[str] = set()
        self._running = False

    async def enqueue(self, task_id: str, priority: int = 1):
        if task_id not in self._queued:
            self._queued.add(task_id)
            await self._queue.put((priority, task_id))
        return task_id

    def cancel(self, task_id: str):
        self._cancelled.add(task_id)
        self.tasks.set_status(task_id, TaskStatus.CANCELLED.value)

    async def _run_one(self, task_id: str, executor: Callable[[object], Awaitable[object]]):
        if task_id in self._cancelled: return
        task = self.tasks.resume(task_id)
        if task is None: return
        step = self.tasks.next_resumable_step(task_id)
        if step is None:
            self.tasks.set_status(task_id, TaskStatus.COMPLETED.value)
            return
        attempts = int(step.attempts or 0)
        if attempts >= self.limits.max_attempts:
            self.tasks.set_status(task_id, TaskStatus.FAILED.value, error="maximum attempts exceeded")
            return
        self.tasks.checkpoint(step.id, status="running", attempts=attempts + 1)
        try:
            result = await asyncio.wait_for(executor(step), timeout=self.limits.step_timeout)
            self.tasks.checkpoint(step.id, status="completed", output=str(result))
            if self.tasks.next_resumable_step(task_id) is None:
                self.tasks.set_status(task_id, TaskStatus.COMPLETED.value, result=str(result))
            else:
                self.tasks.set_status(task_id, TaskStatus.QUEUED.value)
        except asyncio.CancelledError:
            self.tasks.checkpoint(step.id, status="cancelled", error="worker cancelled")
            self.tasks.set_status(task_id, TaskStatus.CANCELLED.value)
            raise
        except Exception as exc:
            self.tasks.checkpoint(step.id, status="failed", error=str(exc))
            if attempts + 1 < self.limits.max_attempts:
                self.tasks.set_status(task_id, TaskStatus.RETRYING.value, error=str(exc))
            else:
                self.tasks.set_status(task_id, TaskStatus.FAILED.value, error=str(exc))

    async def run_once(self, executor: Callable[[object], Awaitable[object]]):
        if self._queue.empty(): return False
        _, task_id = await self._queue.get()
        self._queued.discard(task_id)
        await self._run_one(task_id, executor)
        return True

    async def run_forever(self, executor: Callable[[object], Awaitable[object]]):
        self._running = True
        while self._running:
            try:
                await self.run_once(executor)
                if self._queue.empty(): await asyncio.sleep(0.25)
            except asyncio.CancelledError:
                self._running = False
                raise

    def stop(self): self._running = False
