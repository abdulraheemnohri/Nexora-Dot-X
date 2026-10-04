import asyncio
from nexora.core.task_service import TaskService

class Runtime:
    def __init__(self,session_factory):
        self.tasks=TaskService(session_factory)
        self.queue=asyncio.Queue()
        self.running=False
    async def submit(self,dot_id,goal,priority=0):
        task=self.tasks.create(dot_id,goal,priority)
        await self.queue.put(task.id)
        return task
    async def worker(self):
        self.running=True
        while self.running:
            task_id=await self.queue.get()
            try:
                self.tasks.set_status(task_id,"PLANNING")
                await asyncio.sleep(0)
                self.tasks.set_status(task_id,"RUNNING")
                self.tasks.set_status(task_id,"COMPLETED","Task accepted by runtime; model/tool execution not configured.")
            except Exception as exc:
                self.tasks.set_status(task_id,"FAILED",str(exc))
            finally: self.queue.task_done()
    def stop(self): self.running=False
