from pathlib import Path
from pydantic import BaseModel
import os

class Settings(BaseModel):
    host: str = os.getenv("NEXORA_HOST", "127.0.0.1")
    port: int = int(os.getenv("NEXORA_PORT", "8000"))
    data_dir: Path = Path(os.getenv("NEXORA_DATA_DIR", "./data"))
    model_dir: Path = Path(os.getenv("NEXORA_MODEL_DIR", "./models"))
    local_only: bool = os.getenv("NEXORA_LOCAL_ONLY", "true").lower() == "true"
    auth_enabled: bool = os.getenv("NEXORA_AUTH_ENABLED", "false").lower() == "true"
    log_level: str = os.getenv("NEXORA_LOG_LEVEL", "INFO")

settings = Settings()
