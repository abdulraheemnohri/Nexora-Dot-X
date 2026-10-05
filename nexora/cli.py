"""Nexora Dot X CLI."""
import os

import typer

from nexora.config import settings
from nexora.models.litert.diagnostics import scan

cli = typer.Typer(no_args_is_help=True)
litert = typer.Typer(no_args_is_help=True)
cli.add_typer(litert, name="litert")
skills = typer.Typer(no_args_is_help=True)
cli.add_typer(skills, name="skills")

DEFAULT_LITERT_MODEL = "litert-community/gemma-4-E2B-it-litert-lm"
DEFAULT_LITERT_FILE = "gemma-4-E2B-it.litertlm"


@cli.command()
def status():
    """Show runtime status (aligned with GET /api/status)."""
    from nexora import __version__
    from nexora.core.profiles import get_profile

    typer.echo(f"Nexora Dot X {__version__} | "
               f"profile={get_profile().name}")
    typer.echo(f"local_only={settings.local_only} | "
               f"auth={settings.auth_enabled} | "
               f"{settings.host}:{settings.port}")
    try:
        from nexora.control import always_allow as grants_store
        from nexora.control.approvals import ApprovalCenter
        from nexora.core.model_service import ModelService
        from nexora.skills.manager import SkillManager

        models = ModelService()
        typer.echo(f"ready model backend: "
                   f"{models.ready_backend() or 'none ready'}")
        for m in models.status():
            typer.echo(f"  - {m['backend']}: {m['status']} "
                       f"({m['model']})")
        typer.echo(f"pending approvals: "
                   f"{len(ApprovalCenter().pending())}")
        typer.echo(f"always-allow grants: "
                   f"{len(grants_store.list_grants())}")
        sm = SkillManager()
        typer.echo(f"skills: {len(sm.pending())} pending, "
                   f"{len(sm.scan())} active")
    except Exception as e:
        typer.echo(f"runtime details unavailable: {e}")


@cli.command()
def start(profile: str = typer.Option(os.getenv("NEXORA_PROFILE", "balanced"),
                                      "--profile", "-p",
                                      help="battery-saver | balanced | performance"),
          with_litert_serve: bool = typer.Option(
              False, "--with-litert-serve",
              help="Also start the official litert-lm OpenAI-compatible "
                   "server in the background (127.0.0.1:9379)"),
          serve_port: int = typer.Option(9379, "--serve-port",
                                         help="Port for the litert-lm server")):
    """Start the FastHTML server and the always-on background worker."""
    import asyncio
    import uvicorn
    from nexora.automation.worker import BackgroundWorker
    from nexora.core.profiles import get_profile
    from nexora.server import create_app

    p = get_profile(profile)
    worker = BackgroundWorker(p.name)
    typer.echo(f"Starting Nexora ({p.name} profile) on "
               f"{settings.host}:{settings.port} ...")

    serve_proc = None
    if with_litert_serve:
        from nexora.models.litert import cli_bridge
        args = cli_bridge.build_serve_args(host="127.0.0.1", port=serve_port)
        serve_proc = cli_bridge.spawn_serve(args)
        if serve_proc is None:
            typer.secho("litert-lm CLI not found - skipping the serve "
                        "attachment. Install with: pip install litert-lm",
                        fg=typer.colors.YELLOW)
        else:
            typer.echo(f"litert-lm serve attached on "
                       f"127.0.0.1:{serve_port}/v1 "
                       f"(pid {serve_proc.pid})")

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
    finally:
        if serve_proc is not None:
            serve_proc.terminate()
            try:
                serve_proc.wait(timeout=5)
            except Exception:
                serve_proc.kill()
            typer.echo("litert-lm serve stopped.")


@cli.command()
def doctor():
    typer.echo("Python environment: OK")
    typer.echo(f"Database directory: "
               f"{'OK' if settings.data_dir.exists() else 'WARN'}")
    result = scan(str(settings.model_dir))
    typer.echo(f"LiteRT-LM models: {len(result['models'])}")


# ---- built-in LiteRT-LM CLI ---------------------------------------------

@litert.command("list")
def litert_list():
    """List installed .litertlm models."""
    models = scan(str(settings.model_dir))["models"]
    if not models:
        typer.echo("No LiteRT models found. Run: nexora litert install")
        return
    for m in models:
        if isinstance(m, dict):
            typer.echo(f"{m.get('name', '?')}  {m['path']}")
        else:
            typer.echo(str(m))


@litert.command("install")
def litert_install(
    repo: str = typer.Option(DEFAULT_LITERT_MODEL, "--repo", "-r",
                             help="HuggingFace repo (default: built-in Gemma model)"),
    allow_network: bool = typer.Option(
        False, "--allow-network", "-y",
        help="Explicitly allow the network download (local-only default: off)"),
):
    """Download the built-in LiteRT-LM model (gemma by default)."""
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


@litert.command("import")
def litert_import(
    repo: str = typer.Option(DEFAULT_LITERT_MODEL, "--repo", "-r",
                             help="HuggingFace repo to import from"),
    file: str = typer.Option(DEFAULT_LITERT_FILE, "--file", "-f",
                             help=".litertlm filename inside the repo"),
    name: str = typer.Option(None, "--name", "-n",
                             help="Local registry name for the model"),
    allow_network: bool = typer.Option(False, "--allow-network", "-y",
                                       help="Allow contacting HuggingFace"),
):
    """Import a model into the official litert-lm registry (litert-lm import)."""
    from nexora.models.litert import cli_bridge
    local_name = name or (file.rsplit(".", 1)[0] if "." in file else file)
    try:
        cli_bridge.require_network(allow_network)
        args = cli_bridge.build_import_args(repo, file, local_name)
        result = cli_bridge.run_cli(args, network=True)
    except PermissionError as e:
        typer.secho(str(e), fg=typer.colors.YELLOW)
        typer.echo("Re-run with --allow-network to confirm.")
        raise typer.Exit(1)
    except RuntimeError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(1)
    if result.returncode != 0:
        typer.secho("litert-lm import failed: "
                    + (result.stderr or result.stdout),
                    fg=typer.colors.RED)
        raise typer.Exit(1)
    typer.echo(f"Imported {repo} as '{local_name}' into the "
               "litert-lm registry.")


@litert.command("run")
def litert_run(
    prompt: str = typer.Argument(..., help="Prompt for the model"),
    model: str = typer.Option(None, "--model", "-m",
                              help="Model name/path (default: first installed)"),
    backend: str = typer.Option(None, "--backend", "-b",
                                help="cpu | gpu (official litert-lm CLI)"),
    speculative: bool = typer.Option(False, "--mtp/--no-mtp",
                                     help="Multi-Token Prediction (litert-lm CLI)"),
    attachment: str = typer.Option(None, "--attachment", "-a",
                                  help="Image/audio file to attach (litert-lm CLI)"),
    vision_backend: str = typer.Option(None, "--vision-backend",
                                       help="Backend for image attachments"),
    audio_backend: str = typer.Option(None, "--audio-backend",
                                      help="Backend for audio attachments"),
    use_cli: bool = typer.Option(False, "--cli",
                                 help="Run via the official litert-lm CLI"),
):
    """Run a one-shot prompt through LiteRT-LM."""
    from nexora.models.litert import cli_bridge
    if (use_cli or backend or speculative or attachment
            or vision_backend or audio_backend):
        scan_result = scan(str(settings.model_dir))
        models = scan_result["models"]
        ref = model
        if not ref and models:
            m0 = models[0]
            ref = m0["path"] if isinstance(m0, dict) else str(m0)
        if not ref:
            typer.secho("No LiteRT model installed. "
                        "Run: nexora litert install",
                        fg=typer.colors.YELLOW)
            raise typer.Exit(1)
        try:
            args = cli_bridge.build_run_args(
                ref, prompt=prompt, backend=backend,
                speculative=speculative,
                attachment=attachment, vision_backend=vision_backend,
                audio_backend=audio_backend)
            result = cli_bridge.run_cli(args)
        except RuntimeError as e:
            typer.secho(str(e), fg=typer.colors.RED)
            raise typer.Exit(1)
        if result.returncode != 0:
            typer.secho("litert-lm run failed: "
                        + (result.stderr or result.stdout),
                        fg=typer.colors.RED)
            raise typer.Exit(1)
        typer.echo(result.stdout.strip())
        return
    # built-in Python runtime path
    from nexora.models.litert.engine import LiteRTProvider

    provider = LiteRTProvider()
    scan_result = scan(str(settings.model_dir))
    models = scan_result["models"]
    if not models:
        typer.secho("No LiteRT model installed. "
                    "Run: nexora litert install",
                    fg=typer.colors.YELLOW)
        raise typer.Exit(1)
    m0 = models[0]
    path = model or (m0["path"] if isinstance(m0, dict) else str(m0))
    if not provider.load(str(path)):
        typer.secho("LiteRT-LM unavailable: " + provider.health().detail,
                    fg=typer.colors.RED)
        raise typer.Exit(1)
    typer.echo(provider.generate(prompt))


@litert.command("serve")
def litert_serve(
    host: str = typer.Option("127.0.0.1", "--host",
                             help="Host to bind (official litert-lm server)"),
    port: int = typer.Option(9379, "--port",
                             help="Port (default 9379, OpenAI-compatible)"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose logging"),
):
    """Start the official litert-lm OpenAI-compatible server (/v1 endpoints)."""
    from nexora.models.litert import cli_bridge
    args = cli_bridge.build_serve_args(host=host, port=port, verbose=verbose)
    typer.echo(f"litert-lm OpenAI-compatible server on "
               f"http://{host}:{port}/v1")
    typer.echo("Endpoints: GET /v1/models, POST /v1/chat/completions "
               "(Ctrl+C to stop)")
    try:
        rc = cli_bridge.serve_cli(args)
    except RuntimeError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(1)
    raise typer.Exit(rc)


@litert.command("doctor")
def litert_doctor():
    """Diagnose the LiteRT-LM runtime and installed models."""
    result = scan(str(settings.model_dir))
    typer.echo(f"Runtime installed: {result['runtime_available']}")
    if not result["runtime_available"]:
        typer.echo("  -> pip install nexora-dot-x[litert]")
    from nexora.models.litert import cli_bridge
    prefix = cli_bridge.resolve_cli()
    typer.echo(f"litert-lm CLI: "
               f"{' '.join(prefix) if prefix else 'not found'}")
    if not prefix:
        typer.echo("  -> pip install litert-lm  (or: uvx litert-lm)")
    typer.echo(f"Models found: {len(result['models'])}")
    if not result["models"]:
        typer.echo("  -> nexora litert install  "
                   "(downloads the built-in Gemma model)")
    for m in result["models"]:
        if isinstance(m, dict):
            typer.echo("  - " + str(m.get("name", m["path"])))
        else:
            typer.echo("  - " + str(m))


# ---- skills CLI ---------------------------------------------------------

@skills.command("list")
def skills_list(pending_only: bool = typer.Option(
        False, "--pending", help="Only skills awaiting approval")):
    """List active (and optionally pending) skills."""
    from nexora.skills.manager import SkillManager
    sm = SkillManager()
    pend = sm.pending()
    act = sm.scan()
    items = pend if pending_only else act + pend
    if not items:
        typer.echo("No skills found.")
        return
    for s in items:
        mark = ("pending" if s.get("_status") == "pending" else "active")
        typer.echo(f"[{mark}] {s.get('name', '?')} - "
                   f"{s.get('description', '')}")
    if not pending_only and pend:
        typer.echo(f"({len(pend)} pending approval - run: "
                   "nexora skills approve <name>)")


@skills.command("approve")
def skills_approve(name: str = typer.Argument(..., help="Skill name")):
    """Approve a pending skill (moves it to active)."""
    from nexora.skills.manager import SkillManager
    r = SkillManager().approve(name)
    if not r.get("ok"):
        typer.secho("Error: " + r.get("error", ""), fg=typer.colors.RED)
        raise typer.Exit(1)
    typer.echo(f"Skill approved: {name}")


@skills.command("reject")
def skills_reject(name: str = typer.Argument(..., help="Skill name")):
    """Reject (delete) a pending skill."""
    from nexora.skills.manager import SkillManager
    r = SkillManager().reject(name)
    if not r.get("ok"):
        typer.secho("Error: " + r.get("error", ""), fg=typer.colors.RED)
        raise typer.Exit(1)
    typer.echo(f"Skill rejected: {name}")


@skills.command("scan")
def skills_scan_cmd(name: str = typer.Argument(..., help="Skill name")):
    """Run the static safety scan on a skill's source files."""
    from nexora.skills.manager import SkillManager
    from nexora.skills.scanner import scan_skill_files
    s = SkillManager().inspect(name)
    if not s:
        typer.secho("Skill not found: " + name, fg=typer.colors.RED)
        raise typer.Exit(1)
    r = scan_skill_files(s)
    if r["ok"]:
        typer.echo(f"Scan clean for {name} "
                   f"({r['files_scanned']} file(s)).")
        return
    typer.secho(f"Findings for {name}:", fg=typer.colors.RED)
    for i in r["issues"]:
        typer.echo("  - " + i)
    raise typer.Exit(1)


@skills.command("run")
def skills_run(name: str = typer.Argument(..., help="Skill name"),
               payload: str = typer.Option("", "--payload", "-p",
                                           help="Input text for the skill")):
    """Run an approved skill (static scan is re-checked first)."""
    from nexora.skills.manager import SkillManager
    from nexora.skills.runtime import run_skill
    s = SkillManager().inspect(name)
    if not s:
        typer.secho("Skill not found: " + name, fg=typer.colors.RED)
        raise typer.Exit(1)
    r = run_skill(s, payload)
    if not r.get("ok"):
        typer.secho("Run failed: " + r.get("error", ""), fg=typer.colors.RED)
        raise typer.Exit(1)
    typer.echo(str(r.get("result")))


@skills.command("export")
def skills_export(name: str = typer.Argument(..., help="Skill name"),
                  out: str = typer.Option(".", "--out", "-o",
                                          help="Output directory")):
    """Export a skill as a .zip archive (share between installs)."""
    import shutil
    from pathlib import Path
    from nexora.skills.manager import SkillManager
    s = SkillManager().inspect(name)
    if not s:
        typer.secho("Skill not found: " + name, fg=typer.colors.RED)
        raise typer.Exit(1)
    skill_dir = Path(s.get("_dir") or "")
    if not skill_dir.exists():
        typer.secho("Skill directory missing: " + str(skill_dir),
                    fg=typer.colors.RED)
        raise typer.Exit(1)
    dest = Path(out)
    dest.mkdir(parents=True, exist_ok=True)
    archive = shutil.make_archive(str(dest / name), "zip", skill_dir)
    typer.echo(f"Exported: {archive}")


def main():
    cli()


if __name__ == "__main__":
    main()
