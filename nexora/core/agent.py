"""Agent runtime: runs tasks for one Dot end-to-end."""
from nexora.core.planner import Planner
from nexora.core.task_engine import TaskEngine, TaskStatus
from nexora.memory.manager import MemoryManager


class Agent:
    def __init__(self, dot, executor=None):
        self.dot = dot
        self.planner = Planner()
        self.tasks = TaskEngine()
        self.memory = MemoryManager()
        self.executor = executor

    async def run_task(self, task) -> str:
        self.tasks.set_status(task.id, TaskStatus.PLANNING.value)
        steps = self.planner.plan(task.goal)
        if not steps:
            self.tasks.set_status(task.id, TaskStatus.FAILED.value, error="empty goal")
            return TaskStatus.FAILED.value
        self.tasks.set_plan(task.id, steps)
        self.tasks.set_status(task.id, TaskStatus.RUNNING.value)
        self.memory.save(f"Task started: {task.goal}", bot_id=self.dot.id, kind="working")
        for step in steps:
            if self.executor is None:
                continue
            outcome = self.executor.execute(step, bot_id=self.dot.id, task_id=task.id)
            if outcome.pending_approval:
                self.tasks.set_status(task.id, TaskStatus.WAITING_APPROVAL.value)
                return TaskStatus.WAITING_APPROVAL.value
            if not outcome.ok:
                self.tasks.set_status(task.id, TaskStatus.FAILED.value, error=outcome.output)
                return TaskStatus.FAILED.value
        summary = f"Completed {len(steps)} steps for: {task.goal}"
        self.memory.save(summary, bot_id=self.dot.id, kind="episodic", importance=0.7)
        self.tasks.set_status(task.id, TaskStatus.COMPLETED.value, result=summary)
        return TaskStatus.COMPLETED.value
