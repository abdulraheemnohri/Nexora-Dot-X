from nexora.memory.federation import Federation, MemoryItem


def test_resolve_prefers_approved():
    f = Federation()
    a = MemoryItem("bot", "maybe", confidence=1.0)
    b = MemoryItem("user", "definitely", confidence=0.5, approved=True)
    assert f.resolve([a, b]).content == "definitely"


def test_resolve_prefers_trusted_then_confidence():
    f = Federation()
    a = MemoryItem("shared", "low", confidence=0.2, trusted=True)
    b = MemoryItem("bot", "high", confidence=0.9)
    assert f.resolve([a, b]).content == "low"
    c = MemoryItem("user", "highest", confidence=0.99)
    assert f.resolve([b, c]).content == "highest"


def test_merge_dedupes():
    f = Federation()
    items = [MemoryItem("a", "same text", created_at=2),
             MemoryItem("b", "SAME TEXT", created_at=1),
             MemoryItem("c", "other", created_at=3)]
    merged = f.merge(items)
    assert "other" in merged
    assert merged.lower().count("same text") == 1
