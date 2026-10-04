from pathlib import Path
import pytest
from types import SimpleNamespace

from nexora.database.engine import init_db
from nexora.core.agent import Agent
from nexora.core.task_engine import TaskEngine, TaskStatus
from nexora.core.executor import Executor, StepOutcome


class NoOpExecutor(Executor):
    def execute(self, step, **kwargs):
        return StepOutcome(True, "ok")


@pytest.mark.asyncio
async def test_agent_completes_task(tmp_path: Path):
    init_db(tmp_path / "test.db")
    dot = SimpleNamespace(id="dot1", name="Test Dot")
    agent = Agent(dot, executor=NoOpExecutor())
    t = TaskEngine().create("research AI developments")
    status = await agent.run_task(t)
    assert status == TaskStatus.COMPLETED.value
