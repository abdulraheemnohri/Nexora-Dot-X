"""Persistent scheduler for recurring and future tasks."""
import time
from nexora.database.models import Task
from nexora.database import repositories as repo
from nexora.core.task_engine import TaskEngine


class Schedule:
    def __init__(self, job_id: str, goal: str, every_seconds: float,
                 dot_id=None, last_run: float = 0.0, enabled: bool = True):
        self.id = job_id
        self.goal = goal
        self.every = every_seconds
        self.dot_id = dot_id
        self.last_run = last_run
        self.enabled = enabled


class Scheduler:
    def __init__(self):
        self._jobs: dict[str, Schedule] = {}

    def add(self, job_id: str, goal: str, every_seconds: float, dot_id=None) -> Schedule:
        job = Schedule(job_id, goal, every_seconds, dot_id)
        self._jobs[job_id] = job
        return job

    def remove(self, job_id: str) -> bool:
        return self._jobs.pop(job_id, None) is not None

    def list(self) -> list:
        return list(self._jobs.values())

    def due(self) -> list:
        now = time.time()
        return [j for j in self._jobs.values() if j.enabled and now - j.last_run >= j.every]

    def run_due(self) -> list:
        engine = TaskEngine()
        created = []
        for job in self.due():
            t = engine.create(job.goal, dot_id=job.dot_id)
            job.last_run = time.time()
            created.append(t)
        return created
