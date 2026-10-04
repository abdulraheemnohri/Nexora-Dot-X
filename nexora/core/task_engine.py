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

    def list(self, status: str | None = None, limit: int = 200) -> list:
        if status:
            return repo.query(Task, Task.status == status, limit=limit)
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
