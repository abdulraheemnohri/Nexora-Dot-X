from pathlib import Path
import pytest

from nexora.database.engine import init_db
from nexora.core.task_engine import TaskEngine
from nexora.core.delegation import Coordinator
from nexora.core.executor import Executor, StepOutcome


class NoOpExecutor(Executor):
    def execute(self, step, **kwargs):
        return StepOutcome(True, "ok")


@pytest.mark.asyncio
async def test_delegation_runs_workers(tmp_path: Path):
    init_db(tmp_path / "test.db")
    t = TaskEngine().create("fan-out goal")
    coord = Coordinator(NoOpExecutor())
    d = coord.delegate("coordinator1", t.id, ["w1", "w2"],
                       [{"description": "part A"}, {"description": "part B"}])
    assert len(d.workers) == 4
    result = await coord.run(d)
    assert result["ok"] == 4 and result["failed"] == 0
