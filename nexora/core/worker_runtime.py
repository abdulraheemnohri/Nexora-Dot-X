"""Process-local lifecycle manager for the autonomous worker."""
import asyncio
from collections.abc import Awaitable, Callable
from nexora.core.autonomous_worker import AutonomousWorker

class WorkerRuntime:
    def __init__(self, worker: AutonomousWorker | None = None):
        self.worker = worker or AutonomousWorker()
        self._task: asyncio.Task | None = None
        self._executor = None

    async def start(self, executor: Callable[[object], Awaitable[object]], recover: bool = True):
        if self._task and not self._task.done():
            return False
        self._executor = executor
        if recover:
            await self.worker.recover()
        self._task = asyncio.create_task(self.worker.run_forever(executor), name="nexora-worker")
        return True

    async def stop(self):
        self.worker.stop()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    @property
    def running(self):
        return bool(self._task and not self._task.done())
