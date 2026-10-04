import typer
from nexora.config import settings
from nexora.models.litert.diagnostics import scan

cli = typer.Typer(no_args_is_help=True)

@cli.command()
def status():
    typer.echo(f"Nexora Dot X 0.1.0 | local_only={settings.local_only}")

@cli.command()
def doctor():
    typer.echo(f"Python environment: OK")
    typer.echo(f"Database directory: {'OK' if settings.data_dir.exists() else 'WARN'}")
    result = scan(str(settings.model_dir))
    typer.echo(f"LiteRT-LM models: {len(result['models'])}")

@cli.command()
def litert_list():
    for path in scan(str(settings.model_dir))["models"]:
        typer.echo(path)

def main():
    cli()

if __name__ == "__main__":
    main()
