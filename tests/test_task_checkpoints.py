from nexora.core.task_engine import TaskEngine


def test_task_steps_are_durable_and_resumable():
    engine = TaskEngine()
    task = engine.create("test durable work")
    steps = engine.initialize_steps(task.id, ["one", "two"])
    assert len(steps) == 2
    assert engine.next_resumable_step(task.id).step_index == 0

    engine.checkpoint(steps[0].id, status="running", attempts=1,
                      checkpoint={"cursor": "a"})
    engine.checkpoint(steps[0].id, status="completed", output="done")
    assert engine.next_resumable_step(task.id).step_index == 1

    engine.set_status(task.id, "PAUSED")
    assert engine.resume(task.id).status == "RUNNING"


def test_initialize_steps_does_not_duplicate():
    engine = TaskEngine()
    task = engine.create("no duplicate steps")
    first = engine.initialize_steps(task.id, ["a"])
    second = engine.initialize_steps(task.id, ["a"])
    assert [x.id for x in first] == [x.id for x in second]
