"""nexora command-line interface."""
import asyncio

import typer

from nexora.config import settings

cli = typer.Typer(no_args_is_help=True, add_completion=False)
litert = typer.Typer(no_args_is_help=True)
cli.add_typer(litert, name="litert")
backup_cli = typer.Typer(no_args_is_help=True)
cli.add_typer(backup_cli, name="backup")


@cli.command()
def start(profile: str = typer.Option("balanced",
                                      help="battery-saver/balanced/performance")):
    """Start the control center + background worker."""
    import uvicorn
    from nexora.server import create_app
    from nexora.automation.scheduler import Scheduler
    from nexora.automation.worker import BackgroundWorker

    app, _rt = create_app()
    worker = BackgroundWorker(Scheduler(), profile=profile)

    async def serve():
        config = uvicorn.Config(app, host=settings.host, port=settings.port,
                                loop="asyncio")
        server = uvicorn.Server(config)
        worker_task = asyncio.create_task(worker.run())
        try:
            await server.serve()
        finally:
            worker.stop()
            worker_task.cancel()

    asyncio.run(serve())


@cli.command()
def status():
    typer.echo("Nexora Dot X | local_only=" + str(settings.local_only) + " | "
               + "http://" + settings.host + ":" + str(settings.port))


@cli.command()
def doctor():
    """Environment diagnostics: PASS / WARN / FAIL per component."""
    import platform
    from nexora.database.engine import init_db
    from nexora.models.litert.diagnostics import doctor as litert_doctor
    from nexora.models.router import ModelRouter
    typer.echo("Python " + platform.python_version() + " on "
               + platform.system() + " - OK")
    try:
        init_db()
        typer.echo("SQLite database - OK")
    except Exception as e:
        typer.echo("SQLite database - FAIL: " + str(e))
    for name, result in litert_doctor():
        typer.echo("LiteRT: " + name + " - " + result)
    for m in ModelRouter().available():
        typer.echo("Provider " + m.name + " (" + m.backend + ") - "
                   + m.status + ": " + m.detail)


@cli.command()
def chat(goal: str):
    """One-shot generation via the model bus."""
    from nexora.models.router import ModelRouter
    try:
        typer.echo(ModelRouter().generate(goal))
    except Exception as e:
        typer.echo("error: " + str(e))


@cli.command()
def simulate(goal: str):
    """Dry-run a task: plan + policy-check steps without side effects."""
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
    typer.echo("status: " + t.status)
    typer.echo(t.result or t.error)


@cli.command()
def password():
    """Generate a password hash for NEXORA_SECRET_PASSWORD_HASH."""
    import getpass
    from nexora.security.auth import AuthManager
    pw = getpass.getpass("New password: ")
    typer.echo(AuthManager.hash_password(pw))


@cli.command()
def backup_create(include_models: bool = typer.Option(False,
                                                      help="Include model files")):
    """Create a zip backup (db, skills, workspaces)."""
    from nexora.database.engine import init_db
    from nexora.database.backup import create_backup
    init_db()
    path = create_backup(include_models=include_models)
    typer.echo("backup created: " + path)


@backup_cli.command("create")
def backup_create_cmd(include_models: bool = False):
    backup_create(include_models)


@backup_cli.command("restore")
def backup_restore(archive: str, skip_db: bool = typer.Option(False)):
    """Restore a backup archive."""
    from nexora.database.backup import restore_backup
    result = restore_backup(archive, restore_db=not skip_db)
    if result["ok"]:
        typer.echo("restored " + str(len(result["restored"])) + " items")
    else:
        typer.echo("error: " + result.get("error", "unknown"))


@litert.command("list")
def litert_list():
    from nexora.models.litert.diagnostics import scan
    for m in scan()["models"]:
        typer.echo(m["name"] + ": " + m["path"])


@litert.command("scan")
def litert_scan():
    from nexora.models.litert.diagnostics import scan
    info = scan()
    typer.echo("runtime: "
               + ("available" if info["runtime_available"] else "not installed"))
    typer.echo("directory: " + info["directory"])
    typer.echo("models: " + str(len(info["models"])))


@litert.command("doctor")
def litert_doctor_cmd():
    from nexora.models.litert.diagnostics import doctor
    for name, result in doctor():
        typer.echo(name + " - " + result)


def main():
    cli()


if __name__ == "__main__":
    main()
