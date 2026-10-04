"""Backup / restore: SQLite DB, config, bots, skills, schedules, policies.

Model files are NOT included unless explicitly selected.
"""
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

from nexora.config import settings


def create_backup(target_dir=None, include_models: bool = False) -> str:
    target_dir = Path(target_dir or (settings.data_dir / "backups"))
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive = target_dir / ("nexora-backup-" + stamp + ".zip")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        db = settings.db_path
        if db.exists():
            z.write(db, "data/nexora.db")
        env_example = Path(".env.example")
        if env_example.exists():
            z.write(env_example, ".env.example")
        for base, name in ((settings.skills_dir, "skills"),
                           (settings.workspace_dir, "workspaces")):
            if base.exists():
                for f in base.glob("**/*"):
                    if f.is_file():
                        z.write(f, name + "/" + f.relative_to(base).as_posix())
        if include_models and settings.model_dir.exists():
            for f in settings.model_dir.glob("**/*"):
                if f.is_file():
                    z.write(f, "models/" + f.relative_to(settings.model_dir).as_posix())
    return str(archive)


def restore_backup(archive_path: str, *, restore_db: bool = True) -> dict:
    archive = Path(archive_path)
    if not archive.exists():
        return {"ok": False, "error": "archive not found"}
    restored = []
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            if info.filename.startswith("data/nexora.db") and restore_db:
                target = settings.data_dir / "nexora.db"
                with z.open(info) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                re
stored.append(str(target))
            elif info.filename.startswith(("skills/", "workspaces/")):
                dest = settings.data_dir.parent / info.filename
                dest.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as src, open(dest, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                restored.append(str(dest))
    return {"ok": True, "restored": restored}
