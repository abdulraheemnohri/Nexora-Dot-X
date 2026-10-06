"""Persistent task engine with the full Nexora task lifecycle."""
import enum
import json

from nexora.database.models import Task
from nexora.database import repositories as repo
from nexora.core.events import bus


class TaskStatus(str, enum.Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    PAUSED = "PAUSED"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskEngine:
    def create(self, goal: str, dot_id: str | None = None, priority: int = 1) -> Task:
        t = Task(goal=goal, dot_id=dot_id, priority=priority, status=TaskStatus.CREATED.value)
        t = repo.add_obj(t)
        bus.publish("task.created", {"id": t.id, "goal": goal, "dot_id": dot_id})
        return t

    def list(self, status: str | None = None,
             dot_id: str | None = None, limit: int = 200) -> list:
        if status and dot_id:
            return repo.query(Task, (Task.status == status)
                               & (Task.dot_id == dot_id), limit=limit)
        if status:
            return repo.query(Task, Task.status == status, limit=limit)
        if dot_id:
            return repo.query(Task, Task.dot_id == dot_id, limit=limit)
        return repo.get_all(Task, limit=limit, order_desc="created_at")

    def get(self, task_id: str) -> Task | None:
        return repo.get_by_id(Task, task_id)

    def set_status(self, task_id: str, status: str, result: str = "", error: str = "") -> Task | None:
        t = repo.get_by_id(Task, task_id)
        if t is None:
            return None
        t = repo.update_fields(t, status=status, result=result or t.result, error=error or t.error)
        bus.publish("task.status", {"id": task_id, "status": status})
        return t

    def set_plan(self, task_id: str, steps: list) -> Task | None:
        t = repo.get_by_id(Task, task_id)
        if t is None:
            return None
        return repo.update_fields(t, plan=json.dumps(steps, ensure_ascii=False))

    def get_plan(self, task) -> list:
        # accept a Task object or an id; always read the freshest row
        if isinstance(task, str):
            fresh = repo.get_by_id(Task, task)
        else:
            fresh = repo.get_by_id(Task, task.id)
        t = fresh or (None if isinstance(task, str) else task)
        if t is None or not getattr(t, "plan", None):
            return []
        try:
            return json.loads(t.plan)
        except json.JSONDecodeError:
            return []

    def initialize_steps(self, task_id: str, steps: list) -> list:
        from nexora.database.models import TaskStep
        existing = self.steps(task_id)
        if existing:
            return existing
        return [repo.add_obj(TaskStep(task_id=task_id, step_index=i, description=str(s)))
                for i, s in enumerate(steps)]

    def steps(self, task_id: str) -> list:
        from nexora.database.models import TaskStep
        return repo.query(TaskStep, TaskStep.task_id == task_id, limit=10000)

    def checkpoint(self, step_id: str, *, status: str | None = None,
                   output: str | None = None, error: str | None = None,
                   checkpoint: dict | None = None, attempts: int | None = None):
        from nexora.database.models import TaskStep
        import time
        step = repo.get_by_id(TaskStep, step_id)
        if step is None:
            return None
        values = {}
        if status is not None:
            values["status"] = status
            if status == "running" and step.started_at is None:
                values["started_at"] = time.time()
            if status in {"completed", "failed", "cancelled"}:
                values["completed_at"] = time.time()
        if output is not None:
            values["output"] = output
        if error is not None:
            values["error"] = error
        if checkpoint is not None:
            values["checkpoint_json"] = json.dumps(checkpoint, ensure_ascii=False)
        if attempts is not None:
            values["attempts"] = attempts
        return repo.update_fields(step, **values) if values else step

    def next_resumable_step(self, task_id: str):
        steps = sorted(self.steps(task_id), key=lambda s: s.step_index)
        return next((s for s in steps if s.status not in {"completed", "cancelled"}), None)

    def resume(self, task_id: str) -> Task | None:
        t = self.get(task_id)
        if t is None or t.status in {TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value}:
            return t
        return self.set_status(task_id, TaskStatus.RUNNING.value)
