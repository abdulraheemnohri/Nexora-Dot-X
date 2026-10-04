from pathlib import Path
from nexora.database.engine import init_db
from nexora.memory.manager import MemoryManager


def test_memory_save_and_search(tmp_path: Path):
    init_db(tmp_path / "test.db")
    m = MemoryManager()
    m.save("Nexora uses System 1 policy gate", kind="semantic",
           tags="architecture,security")
    m.save("Task completed yesterday", kind="episodic", importance=0.9)
    hits = m.search("policy")
    assert len(hits) == 1
    assert "policy" in hits[0].content.lower()
