from pathlib import Path
from nexora.database.engine import init_db
from nexora.automation.scheduler import Scheduler


def test_schedule_persists(tmp_path: Path):
    init_db(tmp_path / "test.db")
    s = Scheduler()
    job_id = s.add("daily summary", every_seconds=60)
    jobs = s.list()
    assert any(j.id == job_id for j in jobs)
    s.remove(job_id)
    assert not any(j.id == job_id for j in s.list())
