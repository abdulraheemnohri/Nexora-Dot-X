from nexora.core.memory_service import MemoryService


class FakeRow:
    def __init__(self, content, kind="semantic", importance=0.5, created_at=1.0):
        self.id = "x"
        self.content = content
        self.kind = kind
        self.importance = importance
        self.created_at = created_at


class FakeManager:
    def __init__(self, rows):
        self.rows = rows
        self.deleted = []

    def search(self, query, bot_id=None, limit=50):
        q = (query or "").lower()
        return [r for r in self.rows if not q or q in r.content.lower()][:limit]

    def save(self, content, **kw):
        return FakeRow(content)

    def delete(self, rid):
        self.deleted.append(rid)
        return True


def test_search_merges_duplicates():
    rows = [FakeRow("Nexora runs local-first", "semantic", 0.9),
            FakeRow("nexora runs local-first", "user", 0.4)]
    svc = MemoryService(manager=FakeManager(rows))
    out = svc.search("nexora")
    assert len(out) == 1


def test_remember_rejects_empty():
    svc = MemoryService(manager=FakeManager([]))
    assert svc.remember("   ") is False


def test_forget_deletes_matches():
    rows = [FakeRow("alpha note"), FakeRow("beta note"), FakeRow("alpha two")]
    mgr = FakeManager(rows)
    svc = MemoryService(manager=mgr)
    n = svc.forget("alpha")
    assert n == 2 and len(mgr.deleted) == 2
