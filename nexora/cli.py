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
    typer.echo(f"Python {platform.python_version()} on {platform.system()} - OK")
    try:
        init_db()
        typer.echo("SQLite database - OK")
    except Exception as e:
        typer.echo(f"SQLite database - FAIL: {e}")
    for name, result in litert_doctor():
        typer.echo(f"LiteRT: {name} - {result}")


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
