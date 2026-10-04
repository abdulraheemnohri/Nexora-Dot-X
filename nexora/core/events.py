"""In-process event bus powering the live activity stream."""
import json
from collections import defaultdict
from typing import Callable
from nexora.database.models import Event
from nexora.database import repositories as repo


class EventBus:
    def __init__(self):
        self._subs: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, kind: str, fn: Callable):
        self._subs[kind].append(fn)

    def publish(self, kind: str, payload: dict):
        for fn in list(self._subs.get(kind, [])) + list(self._subs.get("*", [])):
            try:
                fn(kind, payload)
            except Exception:
                pass
        try:
            repo.add_obj(Event(kind=kind, payload=json.dumps(payload, ensure_ascii=False)))
        except Exception:
            pass

    def tail(self, limit: int = 100) -> list:
        return repo.get_all(Event, limit=limit, order_desc="created_at")


bus = EventBus()
