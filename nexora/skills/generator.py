"""Self-growing skill pipeline.

Problem detected -> proposal -> generated implementation -> static scan ->
risk analysis -> USER APPROVAL -> activation.

The AI can never activate its own skill; activation is a System 1/user step.
"""
import json
from pathlib import Path
from nexora.config import settings
from nexora.skills.scanner import scan_source
from nexora.control.audit import audit
from nexora.core.events import bus


class SkillProposal:
    def __init__(self, name: str, description: str, source: str,
                 tests_source: str = "", risk: str = "medium"):
        self.name = name
        self.description = description
        self.source = source
        self.tests_source = tests_source
        self.risk = risk
        self.issues = []
        self.status = "PROPOSED"


class SkillGenerator:
    def __init__(self, skills_dir=None):
        self.dir = Path(skills_dir) if skills_dir else settings.skills_dir

    def propose(self, name: str, description: str, source: str,
                tests_source: str = "") -> SkillProposal:
        p = SkillProposal(name, description, source, tests_source)
        scan = scan_source(source)
        p.issues = scan["issues"]
        if not scan["ok"]:
            p.status = "REJECTED_STATIC_SCAN"
            audit("skill-generator", tool="skills", action="propose " + name,
                  decision="BLOCK", outcome="; ".join(scan["issues"]))
        else:
            audit("skill-generator", tool="skills", action="propose " + name,
                  decision="ASK", outcome="awaiting user approval")
        bus.publish("skill.proposed", {"name": name, "issues": p.issues,
                                       "status": p.status})
        return p

    def activate(self, proposal: SkillProposal) -> dict:
        """Only callable from the user approval flow."""
        if proposal.status != "PROPOSED":
            return {"ok": False, "error": "cannot activate: " + proposal.status}
        target = self.dir / proposal.name
        (target / "tools").mkdir(parents=True, exist_ok=True)
        (target / "skill.json").write_text(json.dumps({
            "name": proposal.name, "version": "0.1.0", "author": "nexora-self",
            "description": proposal.description, "risk": proposal.risk,
            "status": "approved"}, ensure_ascii=False), encoding="utf-8")
        (target / "tools" / "main.py").write_text(proposal.source, encoding="utf-8")
        if proposal.tests_source:
            (target / "tests").mkdir(exist_ok=True)
            (target / "tests" / "test_skill.py").write_text(proposal.tests_source,
                                                            encoding="utf-8")
        audit("user", tool="skills", action="activate " + proposal.name,
              decision="ALLOW", outcome="skill activated")
        bus.publish("skill.activated", {"name": proposal.name})
        return {"ok": True, "skill": proposal.name}
