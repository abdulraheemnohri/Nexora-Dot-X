from pathlib import Path
from nexora.database.engine import init_db
from nexora.core.task_engine import TaskEngine, TaskStatus


def test_task_lifecycle(tmp_path: Path):
    init_db(tmp_path / "test.db")
    engine = TaskEngine()
    t = engine.create("Summarize AI news", dot_id=None)
    assert t.status == TaskStatus.CREATED.value
    engine.set_status(t.id, TaskStatus.RUNNING.value)
    got = engine.get(t.id)
    assert got.status == TaskStatus.RUNNING.value
    engine.set_plan(t.id, [{"id": 1, "kind": "analyze"}])
    assert len(engine.get_plan(got)) == 1
