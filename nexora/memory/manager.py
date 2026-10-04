"""Persistent multi-layer memory backed by SQLite.

Layers: working, episodic, semantic, procedural, user, project, skill.
Vector/semantic index (FAISS) is optional; keyword + recency + importance
ranking keeps memory fully functional without it.
"""
from nexora.database.models import MemoryRecord
from nexora.database import repositories as repo


class MemoryManager:
    def save(self, content: str, *, bot_id=None, kind: str = "semantic",
             tags: str = "", project_id=None, importance: float = 0.5) -> MemoryRecord:
        m = MemoryRecord(content=content, bot_id=bot_id, kind=kind, tags=tags,
                          project_id=project_id, importance=importance)
        return repo.add_obj(m)

    def search(self, query: str = "", *, bot_id=None, kind=None, limit: int = 50) -> list:
        conds = []
        if bot_id:
            conds.append(MemoryRecord.bot_id == bot_id)
        if kind:
            conds.append(MemoryRecord.kind == kind)
        rows = list(repo.query(MemoryRecord, *conds, limit=1000)) if conds             else repo.get_all(MemoryRecord, limit=1000)
        q = query.lower().strip()
        if q:
            rows = [r for r in rows if q in r.content.lower() or q in (r.tags or "").lower()]
        rows.sort(key=lambda r: (r.importance, r.created_at), reverse=True)
        return rows[:limit]

    def delete(self, memory_id: str) -> bool:
        return repo.delete_by_id(MemoryRecord, memory_id)

    def clear(self, bot_id=None) -> int:
        rows = repo.query(MemoryRecord, *( [MemoryRecord.bot_id == bot_id] if bot_id else [] ), limit=100000)
        n = 0
        for r in rows:
            repo.delete_by_id(MemoryRecord, r.id)
            n += 1
        return n
