"""nexora command-line interface."""
import typer

from nexora.config import settings

cli = typer.Typer(no_args_is_help=True, add_completion=False)
litert = typer.Typer(no_args_is_help=True)
cli.add_typer(litert, name="litert")


@cli.command()
def start():
    """Start the FastHTML control center."""
    import uvicorn
    from nexora.server import create_app
    app, _rt = create_app()
    uvicorn.run(app, host=settings.host, port=settings.port)


@cli.command()
def status():
    typer.echo(f"Nexora Dot X | local_only={settings.local_only} | "
               f"http://{settings.host}:{settings.port}")


@cli.command()
def doctor():
    """Environment diagnostics: PASS / WARN / FAIL per component."""
    import platform
    from nexora.database.engine import init_db
    from nexora.models.litert.diagnostics import doctor as litert_doctor
    from nexora.models.router import ModelRouter
    typer.echo(f"Python {platform.python_version()} on {platform.system()} - OK")
    try:
        init_db()
        typer.echo("SQLite database - OK")
    except Exception as e:
        typer.echo(f"SQLite database - FAIL: {e}")
    for name, result in litert_doctor():
        typer.echo(f"LiteRT: {name} - {result}")
    for m in ModelRouter().available():
        typer.echo(f"Provider {m.name} ({m.backend}) - {m.status}: {m.detail}")


@cli.command()
def chat(goal: str):
    """One-shot generation via the model bus."""
    from nexora.models.router import ModelRouter
    try:
        typer.echo(ModelRouter().generate(goal))
    except Exception as e:
        typer.echo(f"error: {e}")


@cli.command()
def simulate(goal: str):
    """Dry-run a task: plan + policy-check steps without side effects."""
    import asyncio
    from types import SimpleNamespace
    from nexora.database.engine import init_db
    from nexora.core.task_engine import TaskEngine
    from nexora.core.agent import Agent
    from nexora.core.executor import Executor

    init_db()
    dot = SimpleNamespace(id="simulate", name="Simulator")
    t = TaskEngine().create(goal)
    asyncio.run(Agent(dot, executor=Executor(tool_registry=None)).run_task(t))
    t = TaskEngine().get(t.id)
    typer.echo(f"status: {t.status}")
    typer.echo(t.result or t.error)


@litert.command("list")
def litert_list():
    from nexora.models.litert.diagnostics import scan
    for m in scan()["models"]:
        typer.echo(f"{m['name']}: {m['path']}")


@litert.command("scan")
def litert_scan():
    from nexora.models.litert.diagnostics import scan
    info = scan()
    typer.echo(f"runtime: {'available' if info['runtime_available'] else 'not installed'}")
    typer.echo(f"directory: {info['directory']}")
    typer.echo(f"models: {len(info['models'])}")


@litert.command("doctor")
def litert_doctor_cmd():
    from nexora.models.litert.diagnostics import doctor
    for name, result in doctor():
        typer.echo(f"{name} - {result}")


def main():
    cli()


if __name__ == "__main__":
    main()
