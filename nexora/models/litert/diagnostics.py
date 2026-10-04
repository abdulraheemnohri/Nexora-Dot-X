from pathlib import Path

def scan(model_dir: str) -> dict:
    p = Path(model_dir)
    models = sorted(str(x) for x in p.rglob("*.litertlm")) if p.exists() else []
    return {"directory": str(p), "exists": p.exists(), "models": models, "ready": bool(models)}
