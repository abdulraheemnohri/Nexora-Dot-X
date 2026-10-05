"""Sandboxed filesystem tools: operations are restricted to allowed roots."""
import shutil
from pathlib import Path
from nexora.config import settings
from nexora.tools.registry import ToolSpec

ALLOWED_ROOTS = [settings.workspace_dir.resolve()]


def _resolve_checked(path: str) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = settings.workspace_dir / p
    p = p.resolve()
    if not any(p == root or root in p.parents for root in ALLOWED_ROOTS):
        raise PermissionError(f"path outside sandbox: {p}")
    return p


class FilesystemTool:
    id = "filesystem"

    def run(self, action: str) -> str:
        parts = action.split(":", 1)
        op = parts[0].strip().lower()
        arg = parts[1].strip() if len(parts) > 1 else ""
        if op == "list":
            p = _resolve_checked(arg or ".")
            return "\n".join(sorted(x.name + ("/" if x.is_dir() else "")
                                    for x in p.iterdir())) or "(empty)"
        if op == "read":
            return _resolve_checked(arg).read_text(encoding="utf-8", errors="replace")[:20000]
        if op == "write":
            target, _, content = arg.partition("|")
            p = _resolve_checked(target)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return f"wrote {len(content)} bytes to {p.name}"
        if op == "search":
            root = _resolve_checked(arg or ".")
            hits = [str(p) for p in root.rglob("*") if arg.lower() in p.name.lower()][:50]
            return "\n".join(hits) or "no matches"
        if op == "copy":
            src, _, dst = arg.partition("|")
            shutil.copy2(_resolve_checked(src.strip()), _resolve_checked(dst.strip()))
            return "copied"
        if op == "delete":
            p = _resolve_checked(arg)
            p.unlink()
            return "deleted"
        return f"unsupported filesystem op: {op}"


def register(registry) -> ToolSpec:
    spec = ToolSpec("filesystem", "Filesystem", "Sandboxed file operations within workspaces.", risk="medium")
    registry.register(spec, FilesystemTool().run)
    return spec
