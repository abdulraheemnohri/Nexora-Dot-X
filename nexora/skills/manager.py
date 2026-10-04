"""Skill system: local, built-in and imported skills with metadata + risk."""
import json
from pathlib import Path
from nexora.config import settings


class SkillManager:
    def __init__(self, skills_dir: Path | None = None):
        self.dir = skills_dir or settings.skills_dir

    def scan(self) -> list:
        skills = []
        if not self.dir.exists():
            return skills
        for meta_file in sorted(self.dir.glob("*/skill.json")):
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                meta["_dir"] = str(meta_file.parent)
                skills.append(meta)
            except Exception:
                skills.append({"name": meta_file.parent.name, "error": "invalid skill.json"})
        return skills

    def inspect(self, name: str) -> dict | None:
        for s in self.scan():
            if s.get("name") == name:
                return s
        return None

    def install_from_dir(self, src: Path) -> dict:
        meta_file = Path(src) / "skill.json"
        if not meta_file.exists():
            return {"ok": False, "error": "skill.json missing"}
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        name = meta.get("name") or Path(src).name
        target = self.dir / name
        target.mkdir(parents=True, exist_ok=True)
        for f in Path(src).glob("**/*"):
            if f.is_file():
                rel = f.relative_to(src)
                (target / rel).parent.mkdir(parents=True, exist_ok=True)
                (target / rel).write_bytes(f.read_bytes())
        return {"ok": True, "skill": name}
