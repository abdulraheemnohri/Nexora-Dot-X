"""Model manifest for .litertlm files (portable across future models)."""
import json
from dataclasses import dataclass, asdict
from pathlib import Path

COMPATIBLE = ("gemma", "qwen", "functiongemma", "llama", "phi")


@dataclass
class Manifest:
    name: str
    file: str
    family: str = ""
    size_bytes: int = 0
    context: int = 4096
    quant: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def load_manifest(model_path: Path) -> Manifest | None:
    sidecar = model_path.with_suffix(".json")
    if sidecar.exists():
        try:
            data = json.loads(sidecar.read_text(encoding="utf-8"))
            return Manifest(file=str(model_path), **{
                k: v for k, v in data.items() if k in Manifest.__dataclass_fields__})
        except Exception:
            return None
    if not model_path.exists():
        return None
    family = next((f for f in COMPATIBLE if f in model_path.name.lower()), "")
    return Manifest(name=model_path.stem, file=str(model_path),
                    family=family, size_bytes=model_path.stat().st_size)
