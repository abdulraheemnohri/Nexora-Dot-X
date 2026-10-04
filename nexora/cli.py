"""Nexora Dot X CLI."""
import os

import typer

from nexora.config import settings
from nexora.models.litert.diagnostics import scan

cli = typer.Typer(no_args_is_help=True)
litert = typer.Typer(no_args_is_help=True)
cli.add_typer(litert, name="litert")

DEFAULT_LITERT_MODEL = "litert-community/gemma-4-E2B-it-litert-lm"


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


# ---- built-in LiteRT-LM CLI -------------------------------------------------

@litert.command("list")
def litert_list():
    """List installed .litertlm models."""
    models = scan(str(settings.model_dir))["models"]
    if not models:
        typer.echo("No LiteRT models found. Run: nexora litert install")
        return
    for path in models:
        typer.echo(path)


@litert.command("install")
def litert_install(
    repo: str = typer.Option(DEFAULT_LITERT_MODEL, "--repo", "-r",
                             help="HuggingFace repo (default: built-in Gemma model)"),
    allow_network: bool = typer.Option(
        False, "--allow-network", "-y",
        help="Explicitly allow the network download (local-only default: off)"),
):
    """Download the built-in LiteRT-LM model (gemma-4-E2B-it-litert-lm by default)."""
    from nexora.models.litert.download import download_default_model
    typer.echo(f"Downloading {repo} ...")
    try:
        r = download_default_model(str(settings.model_dir),
                                   allow_network=allow_network, repo=repo)
    except PermissionError as e:
        typer.secho(str(e), fg=typer.colors.YELLOW)
        typer.echo("Re-run with --allow-network to confirm the download.")
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"Download failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)
    if r["cached"]:
        typer.echo(f"Already installed: {r['path']}")
    else:
        typer.echo(f"Installed: {r['path']}")


@litert.command("run")
def litert_run(
    prompt: str = typer.Argument(..., help="Prompt for the built-in model"),
    model: str = typer.Option(None, "--model", "-m",
                              help="Model name or path (default: built-in Gemma)"),
):
    """Run a prompt through the built-in LiteRT-LM model."""
    from nexora.models.litert.engine import LiteRTProvider
    provider = LiteRTProvider()
    scan_result = scan(str(settings.model_dir))
    models = scan_result["models"]
    if not models:
        typer.secho("No LiteRT model installed. Run: nexora litert install",
                    fg=typer.colors.YELLOW)
        raise typer.Exit(1)
    path = model or models[0]["path"] if isinstance(models[0], dict) else models[0]
    if not provider.load(str(path)):
        typer.secho("LiteRT-LM unavailable: " + provider.health().detail, fg=typer.colors.RED)
        raise typer.Exit(1)
    typer.echo(provider.generate(prompt))


@litert.command("doctor")
def litert_doctor():
    """Diagnose the LiteRT-LM runtime and installed models."""
    result = scan(str(settings.model_dir))
    typer.echo(f"Runtime installed: {result['runtime_available']}")
    if not result["runtime_available"]:
        typer.echo("  -> pip install nexora-dot-x[litert]")
    typer.echo(f"Models found: {len(result['models'])}")
    if not result["models"]:
        typer.echo("  -> nexora litert install  (downloads the built-in Gemma model)")
    for path in result["models"]:
        typer.echo("  - " + str(path))


def main():
    cli()


if __name__ == "__main__":
    main()
