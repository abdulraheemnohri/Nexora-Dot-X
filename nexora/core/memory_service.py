"""Federated memory search: merges layers/stores and resolves conflicts.

Wires MemoryManager + Federation into one query surface used by the
memory UI and the /api/memory/search endpoint.
"""
from nexora.core.events import bus
from nexora.memory.manager import MemoryManager
from nexora.memory.federation import Federation, MemoryItem


class MemoryService:
    def __init__(self, manager=None, federation=None):
        self.manager = manager or MemoryManager()
        self.federation = federation or Federation()

    def search_detailed(self, query: str, *, bot_id=None, limit: int = 50) -> list:
        """Federated search keeping per-hit metadata (kind, confidence)."""
        rows = self.manager.search(query, bot_id=bot_id, limit=limit)
        items = [MemoryItem(store=(r.kind or "shared"), content=r.content,
                            confidence=float(r.importance or 0.5),
                            created_at=float(r.created_at or 0.0))
                 for r in rows]
        winners = {}
        for it in items:
            key = it.content.strip().lower()
            prev = winners.get(key)
            if prev is None or self.federation.resolve([prev, it]) is it:
                winners[key] = it
        merged = self.federation.merge(list(winners.values()))
        # re-attach metadata from the winning rows
        by_content = {r.content.strip().lower(): r for r in rows}
        out = []
        for line in merged.split("\n"):
            if not line.strip():
                continue
            row = by_content.get(line.strip().lower())
            out.append({
                "content": line,
                "kind": getattr(row, "kind", None) if row else None,
                "confidence": round(float(getattr(row, "importance", 0.5) or 0.5), 2)
                              if row else None,
            })
        return out

    def search(self, query: str, *, bot_id=None, limit: int = 50) -> list:
        """Keyword search + federated dedupe across memory kinds (plain lines)."""
        return [h["content"] for h in self.search_detailed(query, bot_id=bot_id, limit=limit)]

    def remember(self, content: str, *, kind: str = "semantic",
                 importance: float = 0.5, bot_id=None) -> bool:
        if not content.strip():
            return False
        row = self.manager.save(content.strip(), kind=kind,
                                importance=importance, bot_id=bot_id)
        bus.publish("memory.saved", {"id": row.id, "kind": kind})
        return True

    def forget(self, query: str, *, bot_id=None) -> int:
        rows = self.manager.search(query, bot_id=bot_id, limit=1000)
        n = 0
        for r in rows:
            if self.manager.delete(r.id):
                n += 1
        if n:
            bus.publish("memory.forgotten", {"count": n})
        return n
