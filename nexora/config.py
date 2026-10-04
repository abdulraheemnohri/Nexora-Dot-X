from pathlib import Path
import os


class Settings:
    """Central configuration. All values overridable via environment variables."""

    def __init__(self):
        self.host: str = os.getenv("NEXORA_HOST", "127.0.0.1")
        self.port: int = int(os.getenv("NEXORA_PORT", "8000"))
        self.data_dir: Path = Path(os.getenv("NEXORA_DATA_DIR", "./data"))
        self.model_dir: Path = Path(os.getenv("NEXORA_MODEL_DIR", "./models"))
        self.litert_dir: Path = Path(os.getenv("NEXORA_LITERT_DIR", "./models/litert"))
        self.workspace_dir: Path = Path(os.getenv("NEXORA_WORKSPACE_DIR", "./workspaces"))
        self.skills_dir: Path = Path(os.getenv("NEXORA_SKILLS_DIR", "./skills"))
        self.local_only: bool = os.getenv("NEXORA_LOCAL_ONLY", "true").lower() == "true"
        self.auth_enabled: bool = os.getenv("NEXORA_AUTH_ENABLED", "false").lower() == "true"
        self.log_level: str = os.getenv("NEXORA_LOG_LEVEL", "INFO")
        self.default_model: str = os.getenv("NEXORA_DEFAULT_MODEL", "litert")

    def ensure_dirs(self):
        for d in (self.data_dir, self.model_dir, self.litert_dir,
                  self.workspace_dir, self.skills_dir, self.data_dir / "logs"):
            d.mkdir(parents=True, exist_ok=True)

    @property
    def db_path(self) -> Path:
        return self.data_dir / "nexora.db"


settings = Settings()
