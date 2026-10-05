"""Execute durable task steps through System 1 Executor."""
import asyncio
import json
from nexora.core.executor import Executor, StepOutcome

class TaskStepRunner:
    def __init__(self, executor: Executor | None = None):
        self.executor = executor or Executor()

    async def __call__(self, step):
        payload = {}
        try: payload = json.loads(step.input_json or "{}")
        except json.JSONDecodeError: pass
        if not payload:
            payload = {"description": step.description}
        outcome: StepOutcome = await asyncio.to_thread(self.executor.execute, payload,
                                                        task_id=step.task_id, step_id=step.id)
        if outcome.pending_approval:
            # The durable worker must stop rather than mark an approval as complete.
            raise WaitingApproval(outcome.pending_approval)
        if not outcome.ok:
            raise RuntimeError(outcome.output)
        return outcome.output

class WaitingApproval(Exception):
    def __init__(self, approval_id: str):
        super().__init__(f"waiting for approval: {approval_id}")
        self.approval_id = approval_id
