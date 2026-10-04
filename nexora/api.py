"""REST API surface (mounted by server.py; kept importable for tests)."""
from nexora.config import settings
from nexora.bots.manager import BotManager
from nexora.core.task_engine import TaskEngine


def status() -> dict:
    return {"status": "ready", "local_only": settings.local_only, "database": "sqlite"}


def list_dots() -> list:
    return [{"id": d.id, "name": d.name, "status": d.status}
            for d in BotManager().list()]


def list_tasks(status_filter: str | None = None) -> list:
    return [{"id": t.id, "goal": t.goal, "status": t.status}
            for t in TaskEngine().list(status_filter)]
