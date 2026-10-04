"""Skill system: local, built-in and imported skills with metadata + risk.

Self-grown or imported skills land in skills/.pending/ and MUST be explicitly
approved by the user (System 1) before they become active. The AI cannot
activate its own skills.
"""
import json
import shutil
from pathlib import Path

from nexora.config import settings
from nexora.core.events import bus


class SkillManager:
    def __init__(self, skills_dir: Path | None = None):
        self.dir = skills_dir or settings.skills_dir
        self.pending_dir = self.dir / ".pending"

    # -- discovery ---------------------------------------------------------
    def scan(self) -> list:
        skills = []
        if not self.dir.exists():
            return skills
        for meta_file in sorted(self.dir.glob("*/skill.json")):
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                meta["_dir"] = str(meta_file.parent)
                meta["_status"] = "active"
                skills.append(meta)
            except Exception:
                skills.append({"name": meta_file.parent.name, "error": "invalid skill.json"})
        return skills

    def pending(self) -> list:
        skills = []
        if not self.pending_dir.exists():
            return skills
        for meta_file in sorted(self.pending_dir.glob("*/skill.json")):
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                meta["_dir"] = str(meta_file.parent)
                meta["_status"] = "pending"
                skills.append(meta)
            except Exception:
                skills.append({"name": meta_file.parent.name,
                               "error": "invalid skill.json", "_status": "pending"})
        return skills

    def inspect(self, name: str) -> dict | None:
        for s in self.scan() + self.pending():
            if s.get("name") == name:
                return s
        return None

    # -- lifecycle ---------------------------------------------------------
    def submit(self, name: str, meta: dict, files: dict) -> dict:
        """Queue a new self-grown/imported skill for approval."""
        if not name or "/" in name or name.startswith("."):
            return {"ok": False, "error": "invalid skill name"}
        target = self.pending_dir / name
        target.mkdir(parents=True, exist_ok=True)
        meta = dict(meta)
        meta["name"] = name
        (target / "skill.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        for rel, content in (files or {}).items():
            f = target / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(content, encoding="utf-8")
        bus.publish("skill.submitted", {"name": name})
        return {"ok": True, "skill": name, "status": "pending"}

    def approve(self, name: str) -> dict:
        src = self.pending_dir / name
        if not src.exists():
            return {"ok": False, "error": "no pending skill: " + name}
        target = self.dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(src), str(target))
        bus.publish("skill.approved", {"name": name})
        return {"ok": True, "skill": name, "status": "active"}

    def reject(self, name: str) -> dict:
        src = self.pending_dir / name
        if not src.exists():
            return {"ok": False, "error": "no pending skill: " + name}
        shutil.rmtree(src)
        bus.publish("skill.rejected", {"name": name})
        return {"ok": True, "skill": name, "status": "rejected"}

    def install_from_dir(self, src: Path) -> dict:
        meta_file = Path(src) / "skill.json"
        if not meta_file.exists():
            return {"ok": False, "error": "skill.json missing"}
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        name = meta.get("name") or Path(src).name
        files = {}
        for f in Path(src).glob("**/*"):
            if f.is_file() and f.name != "skill.json":
                files[f.relative_to(src).as_posix()] = f.read_text(encoding="utf-8")
        return self.submit(name, meta, files)
