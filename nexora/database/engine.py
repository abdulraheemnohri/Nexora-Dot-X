from pathlib import Path
from sqlalchemy import create_engine
from nexora.config import settings

settings.data_dir.mkdir(parents=True, exist_ok=True)
engine = create_engine(f"sqlite:///{Path(settings.data_dir) / 'nexora.db'}", future=True)
