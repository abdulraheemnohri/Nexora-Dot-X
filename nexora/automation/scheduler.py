"""Persistent scheduler for recurring and future tasks.

Schedules survive restarts (SQLite-backed). Due jobs create tasks that any
online Dot with matching id can pick up.
"""
import time
from sqlalchemy import select
from nexora.database.engine import get_session_factory
from nexora.database.schedule_model import ScheduleDB
from nexora.core.task_engine import TaskEngine


class Scheduler:
    def add(self, goal: str, every_seconds: float, dot_id=None) -> str:
        with get_session_factory()() as s:
            row = ScheduleDB(goal=goal, every_seconds=every_seconds, dot_id=dot_id)
            s.add(row)
            s.commit()
            return row.id

    def remove(self, job_id: str) -> bool:
        with get_session_factory()() as s:
            row = s.get(ScheduleDB, job_id)
            if row is None:
                return False
            s.delete(row)
            s.commit()
            return True

    def list(self) -> list:
        with get_session_factory()() as s:
            return list(s.scalars(select(ScheduleDB).order_by(ScheduleDB.created_at)))

    def run_due(self) -> list:
        now = time.time()
        engine = TaskEngine()
        created = []
        with get_session_factory()() as s:
            for row in s.scalars(select(ScheduleDB).where(ScheduleDB.enabled)):
                if now - row.last_run >= row.every_seconds:
                    t = engine.create(row.goal, dot_id=row.dot_id)
                    row.last_run = now
                    created.append(t)
            s.commit()
        return created
