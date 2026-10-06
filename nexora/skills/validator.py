"""Schema and policy validation for skills before System 1 approval."""
import json
import re
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
ALLOWED_RISK = {"safe", "medium", "high", "critical"}

REQUIRED = {"name", "version", "description", "entrypoint", "risk"}

def validate_metadata(meta: dict) -> dict:
    issues = []
    if not isinstance(meta, dict):
        return {"ok": False, "issues": ["skill metadata must be an object"]}
    for key in REQUIRED:
        if not meta.get(key):
            issues.append("missing metadata: " + key)
    name = str(meta.get("name", ""))
    if name and not NAME_RE.fullmatch(name):
        issues.append("invalid skill name: " + name)
    risk = str(meta.get("risk", ""))
    if risk and risk not in ALLOWED_RISK:
        issues.append("invalid risk: " + risk)
    entry = str(meta.get("entrypoint", "tools/main.py"))
    if Path(entry).is_absolute() or ".." in Path(entry).parts:
        issues.append("entrypoint escapes skill directory")
    permissions = meta.get("permissions", [])
    if permissions is not None and not isinstance(permissions, list):
        issues.append("permissions must be a list")
    return {"ok": not issues, "issues": issues}

def validate_skill_dir(skill_dir: str | Path) -> dict:
    root = Path(skill_dir).resolve()
    meta_file = root / "skill.json"
    if not meta_file.exists():
        return {"ok": False, "issues": ["skill.json missing"]}
    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return {"ok": False, "issues": ["invalid skill.json: " + str(e)]}
    result = validate_metadata(meta)
    entry = root / str(meta.get("entrypoint", "tools/main.py"))
    if not entry.exists():
        result["issues"].append("entrypoint missing: " + str(meta.get("entrypoint")))
    result["ok"] = not result["issues"]
    result["metadata"] = meta
    return result
