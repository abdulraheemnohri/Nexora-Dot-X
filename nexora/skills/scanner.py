"""Static safety scanner for proposed skills (self-growth gate 1)."""
import ast
import re

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
