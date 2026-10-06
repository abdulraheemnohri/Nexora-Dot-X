"""Interactive TUI dashboard for Nexora Dot X (rich-based).

Panels: main dashboard, Dots, Tasks, Models, Approvals. Every panel is a
read-only view over the same System 1 governed state as the web UI.
Run with: nexora tui
"""
import time

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

console = Console()

MENU = ("[d]ots [t]asks [m]odels [a]pprovals "
        "[r]efresh [w]atch :help :status :quit [q]")


def _safe(fn, default):
    try:
        return fn()
    except Exception:
        return default


def snapshot() -> dict:
    """Collect a point-in-time status snapshot (never raises)."""
    from nexora import __version__
    from nexora.config import settings
    from nexora.core.profiles import get_profile

    def _dots():
        from nexora.database.runtime import SessionFactory
        from nexora.database.models import Dot
        with SessionFactory() as s:
            return [(d.id, d.name, d.enabled, d.status or "-")
                    for d in s.query(Dot)
                    .order_by(Dot.created_at.desc()).limit(20)]

    def _tasks():
        from nexora.core.task_engine import TaskEngine
        return [(t.id, t.status, (t.goal or "")[:60])
                for t in TaskEngine().list(limit=20)]

    def _approvals():
        from nexora.control.approvals import ApprovalCenter
        return [(a.id, a.risk, a.tool, a.action)
                for a in ApprovalCenter().pending()]

    def _models():
        from nexora.core.model_service import ModelService
        return [(m["backend"], m["status"], m["model"])
                for m in ModelService().status()]

    return {
        "version": _safe(lambda: __version__, "?"),
        "profile": _safe(lambda: get_profile().name, "balanced"),
        "host": settings.host, "port": settings.port,
        "auth": settings.auth_enabled,
        "local_only": settings.local_only,
        "dots": _safe(_dots, []),
        "tasks": _safe(_tasks, []),
        "approvals": _safe(_approvals, []),
        "models": _safe(_models, []),
    }


def render(snap: dict) -> str:
    """Render the main dashboard as a plain string (test-friendly)."""
    lines = [
        "=" * 62,
        "NEXORA DOT X".center(62),
        "Autonomous AI Operating System".center(62),
        "=" * 62,
        "SYSTEM 1  policy: ACTIVE  auth: " + ("ON" if snap["auth"] else "OFF")
        + "  pending approvals: " + str(len(snap["approvals"])),
        "SYSTEM 2  profile: " + snap["profile"]
        + "  local_only: " + str(snap["local_only"]),
        "SERVER    " + str(snap["host"]) + ":" + str(snap["port"]),
        "-" * 62,
        "WORKER    dots: " + str(len(snap["dots"]))
        + "  tasks: " + str(len(snap["tasks"]))
        + "  models: " + str(len(snap["models"])),
        "=" * 62,
        MENU,
    ]
    return chr(10).join(lines)


def _panel(title: str, rows, headers) -> None:
    table = Table(title=title)
    for h in headers:
        table.add_column(h)
    for row in rows:
        table.add_row(*[str(c) for c in row])
    if not rows:
        table.add_row(*["-"] * len(headers))
    console.print(Panel(table))


def show_dots(snap: dict) -> None:
    _panel("Dots", [(d[1], d[0], "enabled" if d[2] else "paused", d[3])
                    for d in snap["dots"]],
           ["name", "id", "state", "status"])


def show_tasks(snap: dict) -> None:
    _panel("Tasks", snap["tasks"], ["id", "status", "goal"])


def show_models(snap: dict) -> None:
    _panel("Models", snap["models"], ["backend", "status", "model"])


def show_approvals(snap: dict) -> None:
    _panel("Pending approvals", snap["approvals"],
           ["id", "risk", "tool", "action"])


def run(refresh: int = 2) -> None:
    """Interactive loop. Keys: d/t/m/a panels, r refresh, w watch mode, q quit."""
    watch = False
    while True:
        snap = snapshot()
        console.clear()
        console.print(render(snap))
        if watch:
            time.sleep(max(1, refresh))
            continue
        choice = Prompt.ask("nexora", default="r").strip().lower()
        if choice in ("q", ":q", ":quit", "quit"):
            return
        if choice == "d":
            show_dots(snap)
        elif choice == "t":
            show_tasks(snap)
        elif choice == "m":
            show_models(snap)
        elif choice == "a":
            show_approvals(snap)
        elif choice == "w":
            watch = True
        elif choice == ":help":
            console.print(MENU)
        elif choice == ":status":
            console.print(render(snap))
        # anything else: refresh
