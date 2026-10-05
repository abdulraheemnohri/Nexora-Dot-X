"""Execution runtime for approved skills (System 2 executor).

Only active (user-approved) skills can run. The runtime re-runs the
static safety scan before execution and refuses anything that fails.
"""
import importlib.util
from pathlib import Path

from nexora.control.audit import audit
from nexora.core.events import bus
from nexora.skills.scanner import scan_skill_files


def run_skill(skill: dict, payload: str = "") -> dict:
    """Import an approved skill's tools/main.py and call run(payload)."""
    if skill.get("_status") != "active":
        return {"ok": False, "error": "skill is not approved/active"}
    scan = scan_skill_files(skill)
    if not scan["ok"]:
        return {"ok": False,
                "error": "static scan failed: " + "; ".join(scan["issues"])}
    skill_dir = skill.get("_dir") or ""
    main = Path(skill_dir) / "tools" / "main.py"
    if not main.exists():
        return {"ok": False, "error": "skill has no tools/main.py"}
    spec = importlib.util.spec_from_file_location(
        "nexora_skill_" + Path(skill_dir).name, main)
    if spec is None or spec.loader is None:
        return {"ok": False, "error": "cannot load skill module"}
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    entry = getattr(module, "run", None)
    if not callable(entry):
        return {"ok": False, "error": "skill defines no run() function"}
    result = entry(payload)
    audit("user", tool="skills", action="run " + str(skill.get("name")),
          decision="ALLOW", outcome="skill executed")
    bus.publish("skill.run", {"name": skill.get("name")})
    return {"ok": True, "skill": skill.get("name"), "result": result}
