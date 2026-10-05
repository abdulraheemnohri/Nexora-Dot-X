"""Static safety scanner for proposed skills (self-growth gate 1)."""
import ast
import re
from pathlib import Path

FORBIDDEN_IMPORTS = {"subprocess", "ctypes", "shutil", "socket", "sys"}
FORBIDDEN_CALLS = {"eval", "exec", "compile", "__import__", "open"}
NETWORK_RE = re.compile("https?://|urllib|requests\\.")


def scan_source(source: str) -> dict:
    issues = []
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"ok": False, "issues": ["syntax error: " + str(e)]}
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module.split(".")[0]]
        for n in names:
            if n in FORBIDDEN_IMPORTS:
                issues.append("forbidden import: " + n)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in FORBIDDEN_CALLS:
            issues.append("forbidden call: " + node.func.id)
    if NETWORK_RE.search(source):
        issues.append("network access detected: requires approval")
    return {"ok": not issues, "issues": issues}


def scan_skill_files(skill: dict) -> dict:
    """Scan every Python file inside a skill directory (pending or active).

    The skill entry's "_dir" key points at the skill folder. Returns
    ok/issues/files_scanned for UI display.
    """
    skill_dir = skill.get("_dir") or ""
    issues = []
    files = 0
    if skill_dir and Path(skill_dir).exists():
        for py in sorted(Path(skill_dir).glob("**/*.py")):
            files += 1
            try:
                src = py.read_text(encoding="utf-8")
            except OSError as e:
                issues.append(py.name + ": read error: " + str(e))
                continue
            result = scan_source(src)
            for i in result["issues"]:
                issues.append(py.name + ": " + i)
    return {"ok": not issues, "issues": issues, "files_scanned": files}
