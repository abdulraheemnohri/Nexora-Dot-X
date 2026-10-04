from pathlib import Path
from nexora.database.engine import init_db
from nexora.database.backup import create_backup


def test_backup_creates_archive(tmp_path: Path, monkeypatch):
    import nexora.config as cfg
    monkeypatch.setattr(cfg.settings, "data_dir", tmp_path / "data")
    monkeypatch.setattr(cfg.settings, "db_path", tmp_path / "data" / "nexora.db")
    init_db(tmp_path / "data" / "nexora.db")
    archive = create_backup(target_dir=tmp_path / "backups")
    assert Path(archive).exists()
    assert archive.endswith(".zip")
