"""Nexora Dot X CLI."""
import os

import typer

from nexora.config import settings
from nexora.models.litert.diagnostics import scan

cli = typer.Typer(no_args_is_help=True)
litert = typer.Typer(no_args_is_help=True)
cli.add_typer(litert, name="litert")


@cli.command()
def status():
    typer.echo(f"Nexora Dot X 0.1.0 | local_only={settings.local_only}")


@cli.command()
def start(profile: str = typer.Option(os.getenv("NEXORA_PROFILE", "balanced"),
                                      "--profile", "-p",
                                      help="battery-saver | balanced | performance")):
    """Start the FastHTML server and the always-on background worker."""
    import asyncio
    import uvicorn
    from nexora.automation.worker import BackgroundWorker
    from nexora.core.profiles import get_profile
    from nexora.server import create_app

    p = get_profile(profile)
    worker = BackgroundWorker(p.name)
    typer.echo(f"Starting Nexora ({p.name} profile) on {settings.host}:{settings.port} ...")

    async def serve():
        server = uvicorn.Server(uvicorn.Config(
            create_app(), host=settings.host, port=settings.port,
            log_level=settings.log_level.lower()))
        ws_task = asyncio.create_task(worker.start())
        try:
            await server.serve()
        finally:
            worker.stop()
            ws_task.cancel()

    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        typer.echo("Nexora stopped.")


@cli.command()
def doctor():
    typer.echo("Python environment: OK")
    typer.echo(f"Database directory: {'OK' if settings.data_dir.exists() else 'WARN'}")
    result = scan(str(settings.model_dir))
    typer.echo(f"LiteRT-LM models: {len(result['models'])}")


@litert.command("list")
def litert_list():
    for path in scan(str(settings.model_dir))["models"]:
        typer.echo(path)


def main():
    cli()


if __name__ == "__main__":
    main()
